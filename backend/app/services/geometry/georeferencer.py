"""
ULAG Manual Georeferencing & 4-Point Affine Rubber-Sheeting Service
Provides least-squares affine transformation, residual error analysis (RMSE, mean, max),
and raster / vector coordinate re-projection for unreferenced cadastral maps.
"""

from typing import List, Dict, Any, Optional, Tuple
import math
import numpy as np
from datetime import datetime, timezone
import uuid

try:
    from backend.app.models.storage import storage_repo
except ImportError:
    from app.models.storage import storage_repo


class ControlPoint:
    def __init__(self, point_id: str, img_x: float, img_y: float, map_x: float, map_y: float, crs: str = "EPSG:32643"):
        self.point_id = point_id
        self.img_x = img_x
        self.img_y = img_y
        self.map_x = map_x
        self.map_y = map_y
        self.crs = crs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "point_id": self.point_id,
            "img_x": self.img_x,
            "img_y": self.img_y,
            "map_x": self.map_x,
            "map_y": self.map_y,
            "crs": self.crs
        }


class GeoreferenceResult:
    def __init__(
        self,
        job_id: str,
        image_name: str,
        control_points: List[Dict[str, Any]],
        affine_matrix: List[float], # [a, b, c, d, e, f] where x_map = a*x + b*y + c, y_map = d*x + e*y + f
        rmse: float,
        mean_residual: float,
        max_residual: float,
        point_residuals: List[Dict[str, Any]],
        target_crs: str,
        status: str, # "ACCEPTED", "EXCEEDS_TOLERANCE", "OVERRIDDEN", "REJECTED"
        created_by: str,
        created_at: str,
        notes: str = ""
    ):
        self.job_id = job_id
        self.image_name = image_name
        self.control_points = control_points
        self.affine_matrix = affine_matrix
        self.rmse = rmse
        self.mean_residual = mean_residual
        self.max_residual = max_residual
        self.point_residuals = point_residuals
        self.target_crs = target_crs
        self.status = status
        self.created_by = created_by
        self.created_at = created_at
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "image_name": self.image_name,
            "control_points": self.control_points,
            "affine_matrix": {
                "a": self.affine_matrix[0],
                "b": self.affine_matrix[1],
                "c": self.affine_matrix[2],
                "d": self.affine_matrix[3],
                "e": self.affine_matrix[4],
                "f": self.affine_matrix[5]
            },
            "rmse": round(self.rmse, 4),
            "mean_residual": round(self.mean_residual, 4),
            "max_residual": round(self.max_residual, 4),
            "point_residuals": self.point_residuals,
            "target_crs": self.target_crs,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "notes": self.notes
        }


class AffineGeoreferencer:
    """
    Solves 2D Affine Transformation parameters using least-squares:
    x' = a * x + b * y + c
    y' = d * x + e * y + f
    Supports rotation, scale, translation, and shear.
    """
    DEFAULT_RMSE_THRESHOLD_METERS = 2.5 # Cadastral surveying tolerance in meters

    def compute_affine_transformation(
        self,
        image_name: str,
        control_points: List[Dict[str, Any]],
        target_crs: str = "EPSG:32643",
        operator: str = "admin",
        override_threshold: bool = False,
        rmse_threshold: float = DEFAULT_RMSE_THRESHOLD_METERS,
        notes: str = ""
    ) -> GeoreferenceResult:
        if len(control_points) < 3:
            raise ValueError(f"At least 3 non-collinear control points are required. Provided: {len(control_points)}")

        # Prepare matrices for least squares
        # For each point i:
        # [ x_i  y_i  1   0    0    0 ] [a]   [ x_map_i ]
        # [ 0    0    0   x_i  y_i  1 ] [b] = [ y_map_i ]
        #                               [c]
        #                               [d]
        #                               [e]
        #                               [f]
        A = []
        L = []
        pts_clean = []
        for i, pt in enumerate(control_points):
            ix = float(pt["img_x"])
            iy = float(pt["img_y"])
            mx = float(pt["map_x"])
            my = float(pt["map_y"])
            pid = pt.get("point_id", f"GCP-{i+1}")
            pts_clean.append({"point_id": pid, "img_x": ix, "img_y": iy, "map_x": mx, "map_y": my, "crs": target_crs})

            A.append([ix, iy, 1.0, 0.0, 0.0, 0.0])
            L.append(mx)
            A.append([0.0, 0.0, 0.0, ix, iy, 1.0])
            L.append(my)

        A = np.array(A, dtype=np.float64)
        L = np.array(L, dtype=np.float64)

        # Solve via least squares
        params, residuals, rank, s = np.linalg.lstsq(A, L, rcond=None)
        a, b, c, d, e, f = params.tolist()

        # Calculate point-by-point residuals
        point_residuals = []
        sq_residuals = []
        for pt in pts_clean:
            ix = pt["img_x"]
            iy = pt["img_y"]
            pred_mx = a * ix + b * iy + c
            pred_my = d * ix + e * iy + f

            dx = pred_mx - pt["map_x"]
            dy = pred_my - pt["map_y"]
            dist_residual = math.hypot(dx, dy)
            sq_residuals.append(dist_residual ** 2)

            point_residuals.append({
                "point_id": pt["point_id"],
                "predicted_map_x": round(pred_mx, 3),
                "predicted_map_y": round(pred_my, 3),
                "target_map_x": round(pt["map_x"], 3),
                "target_map_y": round(pt["map_y"], 3),
                "dx": round(dx, 4),
                "dy": round(dy, 4),
                "residual_meters": round(dist_residual, 4)
            })

        rmse = math.sqrt(float(np.mean(sq_residuals)))
        mean_res = float(np.mean([r["residual_meters"] for r in point_residuals]))
        max_res = float(np.max([r["residual_meters"] for r in point_residuals]))

        # Assess status against threshold
        if rmse <= rmse_threshold:
            status = "ACCEPTED"
        elif override_threshold:
            status = "OVERRIDDEN"
        else:
            status = "EXCEEDS_TOLERANCE"

        job_id = f"geo-{uuid.uuid4().hex[:8]}"
        created_at = datetime.now(timezone.utc).isoformat()

        res = GeoreferenceResult(
            job_id=job_id,
            image_name=image_name,
            control_points=pts_clean,
            affine_matrix=[a, b, c, d, e, f],
            rmse=rmse,
            mean_residual=mean_res,
            max_residual=max_res,
            point_residuals=point_residuals,
            target_crs=target_crs,
            status=status,
            created_by=operator,
            created_at=created_at,
            notes=notes
        )

        # Persist to storage repository
        storage_repo.save_georeferencing_job(job_id, res.to_dict())

        # Audit log entry
        storage_repo.save_audit_log(
            user_id=operator,
            action="GEOREFERENCE_AFFINE",
            target_type="MAP_IMAGE",
            target_id=image_name,
            details={
                "job_id": job_id,
                "rmse": rmse,
                "status": status,
                "control_points_count": len(pts_clean),
                "threshold": rmse_threshold
            }
        )

        return res

    def transform_point(self, matrix: List[float], img_x: float, img_y: float) -> Tuple[float, float]:
        """Applies affine matrix [a, b, c, d, e, f] to an image point."""
        a, b, c, d, e, f = matrix
        return (a * img_x + b * img_y + c, d * img_x + e * img_y + f)


georeferencer = AffineGeoreferencer()
