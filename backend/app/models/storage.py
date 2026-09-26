"""
Storage Repository for ULAG
Provides persistence for cadastral datasets, parcel matches, conflicts,
reconciliation results, and human review decisions.
Works out of the box with SQLite and preserves all original source data without modification.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

from pathlib import Path
DB_DIR = os.path.join(str(Path(__file__).resolve().parents[3]), "data")
_ulag_db = os.path.join(DB_DIR, "ulag.db")
_legacy_db = os.path.join(DB_DIR, "bhumi_fusion.db")

# If legacy db has data but ulag.db is empty or missing, sync it automatically
if os.path.exists(_legacy_db) and (not os.path.exists(_ulag_db) or os.path.getsize(_ulag_db) < 100000):
    try:
        import shutil
        shutil.copyfile(_legacy_db, _ulag_db)
    except Exception:
        pass

DB_FILE = _ulag_db if os.path.exists(_ulag_db) else _legacy_db

class StorageRepository:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parcels (
                    parcel_id TEXT PRIMARY KEY,
                    survey_no TEXT,
                    subdivision_no TEXT,
                    full_survey TEXT,
                    land_use TEXT,
                    legacy_area REAL,
                    legacy_geometry TEXT,
                    drone_geometry TEXT,
                    reconciled_geometry TEXT,
                    gnss_points TEXT,
                    confidence REAL,
                    status TEXT,
                    conflict_type TEXT,
                    source_comparison TEXT,
                    evidence TEXT,
                    recommendation TEXT,
                    created_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conflicts (
                    conflict_id TEXT PRIMARY KEY,
                    parcel_id TEXT,
                    survey_no TEXT,
                    conflict_type TEXT,
                    severity TEXT,
                    confidence REAL,
                    discrepancy_delta TEXT,
                    sources_comparison TEXT,
                    explanation TEXT,
                    status TEXT,
                    reviewed_by TEXT,
                    timestamp TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS review_actions (
                    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conflict_id TEXT,
                    parcel_id TEXT,
                    action TEXT,
                    decided_by TEXT,
                    comment TEXT,
                    timestamp TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_state (
                    id INTEGER PRIMARY KEY,
                    total_parcels INTEGER,
                    matched_count INTEGER,
                    conflicts_count INTEGER,
                    review_count INTEGER,
                    last_run_timestamp TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dsm_dtm_metadata (
                    dataset_id TEXT PRIMARY KEY,
                    dataset_type TEXT,
                    metadata_json TEXT,
                    created_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parcel_elevation (
                    parcel_id TEXT PRIMARY KEY,
                    elevation_json TEXT,
                    updated_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS utility_features (
                    utility_id TEXT PRIMARY KEY,
                    asset_json TEXT,
                    created_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parcel_utility (
                    parcel_id TEXT PRIMARY KEY,
                    assoc_json TEXT,
                    updated_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_runs (
                    dataset_id TEXT PRIMARY KEY,
                    status_json TEXT,
                    updated_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feature_sync_changes (
                    feature_id TEXT PRIMARY KEY,
                    change_json TEXT,
                    updated_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    role TEXT,
                    full_name TEXT,
                    created_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id TEXT PRIMARY KEY,
                    username TEXT,
                    action TEXT,
                    parcel_id TEXT,
                    old_status TEXT,
                    new_status TEXT,
                    confidence REAL,
                    details_json TEXT,
                    timestamp TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS georeferencing_jobs (
                    job_id TEXT PRIMARY KEY,
                    image_name TEXT,
                    control_points_json TEXT,
                    transform_json TEXT,
                    rmse REAL,
                    mean_residual REAL,
                    max_residual REAL,
                    status TEXT,
                    created_by TEXT,
                    created_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS change_detection_results (
                    change_id TEXT PRIMARY KEY,
                    change_type TEXT,
                    confidence REAL,
                    geometry_json TEXT,
                    before_date TEXT,
                    after_date TEXT,
                    source TEXT,
                    created_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS building_extractions (
                    building_id TEXT PRIMARY KEY,
                    parcel_uid TEXT,
                    survey_number TEXT,
                    geometry_json TEXT,
                    area_m2 REAL,
                    confidence REAL,
                    model TEXT,
                    inference_mode TEXT,
                    created_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shared_boundary_proposals (
                    proposal_id TEXT PRIMARY KEY,
                    parcel_a_id TEXT,
                    parcel_b_id TEXT,
                    original_geom_a TEXT,
                    original_geom_b TEXT,
                    split_geom_a TEXT,
                    split_geom_b TEXT,
                    area_diff_a REAL,
                    area_diff_b REAL,
                    confidence REAL,
                    status TEXT,
                    created_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_jobs (
                    job_id TEXT PRIMARY KEY,
                    job_type TEXT,
                    status TEXT,
                    progress INTEGER,
                    processed_count INTEGER,
                    total_count INTEGER,
                    error_message TEXT,
                    metadata_json TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ocr_documents (
                    doc_id TEXT PRIMARY KEY,
                    filename TEXT,
                    file_type TEXT,
                    extracted_fields_json TEXT,
                    raw_text TEXT,
                    verified INTEGER,
                    created_at TEXT
                )
            """)
            conn.commit()

    def save_pipeline_results(
        self,
        parcels_data: List[Dict[str, Any]],
        conflicts_data: List[Dict[str, Any]],
        summary: Dict[str, Any]
    ):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM parcels")
            cursor.execute("DELETE FROM conflicts")
            cursor.execute("DELETE FROM pipeline_state")

            now = datetime.now().isoformat()

            for p in parcels_data:
                cursor.execute("""
                    INSERT INTO parcels (
                        parcel_id, survey_no, subdivision_no, full_survey, land_use,
                        legacy_area, legacy_geometry, drone_geometry, reconciled_geometry,
                        gnss_points, confidence, status, conflict_type,
                        source_comparison, evidence, recommendation, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    p["parcel_id"],
                    p["survey_no"],
                    p.get("subdivision_no"),
                    p["full_survey"],
                    p.get("land_use", ""),
                    p["legacy_area"],
                    json.dumps(p.get("legacy_geometry")),
                    json.dumps(p.get("drone_geometry")),
                    json.dumps(p.get("reconciled_geometry")),
                    json.dumps(p.get("gnss_points", [])),
                    p["confidence"],
                    p["status"],
                    p.get("conflict_type"),
                    json.dumps(p.get("source_comparison")),
                    json.dumps(p.get("evidence")),
                    json.dumps(p.get("recommendation")),
                    now
                ))

            for c in conflicts_data:
                cursor.execute("""
                    INSERT INTO conflicts (
                        conflict_id, parcel_id, survey_no, conflict_type, severity,
                        confidence, discrepancy_delta, sources_comparison, explanation,
                        status, reviewed_by, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    c["conflict_id"],
                    c["parcel_id"],
                    c["survey_no"],
                    c["conflict_type"],
                    c["severity"],
                    c["confidence"],
                    c.get("discrepancy_delta", ""),
                    json.dumps(c.get("sources_comparison")),
                    c["explanation"],
                    c.get("status", "Pending"),
                    c.get("reviewed_by"),
                    c.get("timestamp")
                ))

            cursor.execute("""
                INSERT INTO pipeline_state (
                    id, total_parcels, matched_count, conflicts_count, review_count, last_run_timestamp
                ) VALUES (1, ?, ?, ?, ?, ?)
            """, (
                summary["total_parcels"],
                summary["matched_count"],
                summary["conflicts_count"],
                summary["review_count"],
                now
            ))
            conn.commit()

    def get_pipeline_summary(self) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pipeline_state WHERE id = 1")
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)

    def get_parcels(self, status: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM parcels WHERE 1=1"
            params = []
            if status and status != "All":
                query += " AND status = ?"
                params.append(status)
            if search:
                query += " AND (survey_no LIKE ? OR full_survey LIKE ? OR parcel_id LIKE ?)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])
            query += " ORDER BY parcel_id ASC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append({
                    "parcel_id": r["parcel_id"],
                    "survey_no": r["survey_no"],
                    "subdivision_no": r["subdivision_no"],
                    "full_survey": r["full_survey"],
                    "land_use": r["land_use"],
                    "legacy_area": r["legacy_area"],
                    "confidence": r["confidence"],
                    "status": r["status"],
                    "conflict_type": r["conflict_type"],
                    "recommendation": json.loads(r["recommendation"]) if r["recommendation"] else None
                })
            return results

    def get_parcel_detail(self, parcel_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM parcels WHERE parcel_id = ? OR full_survey = ? OR survey_no = ?", (parcel_id, parcel_id, parcel_id))
            r = cursor.fetchone()
            if not r:
                return None
            return {
                "parcel_id": r["parcel_id"],
                "survey_no": r["survey_no"],
                "subdivision_no": r["subdivision_no"],
                "full_survey": r["full_survey"],
                "land_use": r["land_use"],
                "legacy_area": r["legacy_area"],
                "confidence": r["confidence"],
                "status": r["status"],
                "conflict_type": r["conflict_type"],
                "sources_comparison": json.loads(r["source_comparison"]) if r["source_comparison"] else {},
                "evidence": json.loads(r["evidence"]) if r["evidence"] else {},
                "recommendation": json.loads(r["recommendation"]) if r["recommendation"] else {},
                "geometry_geojson": json.loads(r["legacy_geometry"]) if r["legacy_geometry"] else {},
                "drone_geometry_geojson": json.loads(r["drone_geometry"]) if r["drone_geometry"] else None,
                "reconciled_geometry_geojson": json.loads(r["reconciled_geometry"]) if r["reconciled_geometry"] else None,
                "gnss_points": json.loads(r["gnss_points"]) if r["gnss_points"] else []
            }

    def get_all_parcels_detail(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM parcels ORDER BY parcel_id ASC")
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append({
                    "parcel_id": r["parcel_id"],
                    "survey_no": r["survey_no"],
                    "subdivision_no": r["subdivision_no"],
                    "full_survey": r["full_survey"],
                    "land_use": r["land_use"],
                    "legacy_area": r["legacy_area"],
                    "confidence": r["confidence"],
                    "status": r["status"],
                    "conflict_type": r["conflict_type"],
                    "sources_comparison": json.loads(r["source_comparison"]) if r["source_comparison"] else {},
                    "evidence": json.loads(r["evidence"]) if r["evidence"] else {},
                    "recommendation": json.loads(r["recommendation"]) if r["recommendation"] else {},
                    "geometry_geojson": json.loads(r["legacy_geometry"]) if r["legacy_geometry"] else {},
                    "drone_geometry_geojson": json.loads(r["drone_geometry"]) if r["drone_geometry"] else None,
                    "reconciled_geometry_geojson": json.loads(r["reconciled_geometry"]) if r["reconciled_geometry"] else None,
                    "gnss_points": json.loads(r["gnss_points"]) if r["gnss_points"] else []
                })
            return results

    def get_conflicts(self, conflict_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM conflicts WHERE 1=1"
            params = []
            if conflict_type and conflict_type != "All":
                query += " AND conflict_type LIKE ?"
                params.append(f"%{conflict_type}%")
            query += " ORDER BY conflict_id ASC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append({
                    "conflict_id": r["conflict_id"],
                    "parcel_id": r["parcel_id"],
                    "survey_no": r["survey_no"],
                    "conflict_type": r["conflict_type"],
                    "severity": r["severity"],
                    "confidence": r["confidence"],
                    "discrepancy_delta": r["discrepancy_delta"],
                    "sources_comparison": json.loads(r["sources_comparison"]) if r["sources_comparison"] else {},
                    "explanation": r["explanation"],
                    "status": r["status"],
                    "reviewed_by": r["reviewed_by"],
                    "timestamp": r["timestamp"]
                })
            return results

    def get_conflict_detail(self, conflict_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conflicts WHERE conflict_id = ?", (conflict_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return {
                "conflict_id": r["conflict_id"],
                "parcel_id": r["parcel_id"],
                "survey_no": r["survey_no"],
                "conflict_type": r["conflict_type"],
                "severity": r["severity"],
                "confidence": r["confidence"],
                "discrepancy_delta": r["discrepancy_delta"],
                "sources_comparison": json.loads(r["sources_comparison"]) if r["sources_comparison"] else {},
                "explanation": r["explanation"],
                "status": r["status"],
                "reviewed_by": r["reviewed_by"],
                "timestamp": r["timestamp"]
            }

    def record_review_decision(self, conflict_id: str, action: str, user: str, comment: Optional[str] = None):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status_map = {
                "ACCEPT": "Approved",
                "REJECT": "Rejected",
                "MANUAL_REVIEW": "Manual Review"
            }
            new_status = status_map.get(action.upper(), "Approved")

            # Update conflict (by conflict_id or parcel_id)
            cursor.execute("""
                UPDATE conflicts
                SET status = ?, reviewed_by = ?, timestamp = ?
                WHERE conflict_id = ? OR parcel_id = ?
            """, (new_status, user, now, conflict_id, conflict_id))

            # Retrieve parcel_id for conflict
            cursor.execute("SELECT parcel_id, conflict_id FROM conflicts WHERE conflict_id = ? OR parcel_id = ?", (conflict_id, conflict_id))
            row = cursor.fetchone()
            p_id = row["parcel_id"] if row else conflict_id
            real_c_id = row["conflict_id"] if row else conflict_id

            if p_id and new_status == "Approved":
                cursor.execute("UPDATE parcels SET status = 'Matched' WHERE parcel_id = ?", (p_id,))

            # Insert audit trail
            cursor.execute("""
                INSERT INTO review_actions (conflict_id, parcel_id, action, decided_by, comment, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (real_c_id, p_id, action, user, comment or "", now))

            conn.commit()
            return {
                "conflict_id": conflict_id,
                "status": new_status,
                "reviewed_by": user,
                "timestamp": now
            }

    # DSM / DTM Elevation
    def save_dsm_dtm_metadata(self, meta: Dict[str, Any]):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO dsm_dtm_metadata (dataset_id, dataset_type, metadata_json, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                meta["dataset_id"],
                meta.get("dataset_type", "DSM"),
                json.dumps(meta),
                meta.get("ingested_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()

    def get_dsm_dtm_metadata(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT metadata_json FROM dsm_dtm_metadata ORDER BY created_at DESC")
            return [json.loads(row["metadata_json"]) for row in cursor.fetchall()]

    def save_parcel_elevation(self, parcel_id: str, elev: Dict[str, Any]):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO parcel_elevation (parcel_id, elevation_json, updated_at)
                VALUES (?, ?, ?)
            """, (parcel_id, json.dumps(elev), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()

    def get_parcel_elevation(self, parcel_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT elevation_json FROM parcel_elevation WHERE parcel_id = ?", (parcel_id,))
            r = cursor.fetchone()
            return json.loads(r["elevation_json"]) if r else None

    # Utility Network
    def save_utility_features(self, features: List[Dict[str, Any]]):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for f in features:
                u_id = f.get("utility_id") or f.get("id", f"UTIL-{id(f)}")
                cursor.execute("""
                    INSERT OR REPLACE INTO utility_features (utility_id, asset_json, created_at)
                    VALUES (?, ?, ?)
                """, (u_id, json.dumps(f), now))
            conn.commit()

    def get_utility_features(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT asset_json FROM utility_features")
            return [json.loads(row["asset_json"]) for row in cursor.fetchall()]

    def save_parcel_utility_assoc(self, assoc: Dict[str, Any]):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO parcel_utility (parcel_id, assoc_json, updated_at)
                VALUES (?, ?, ?)
            """, (assoc["parcel_id"], json.dumps(assoc), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()

    def get_parcel_utility_assoc(self, parcel_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT assoc_json FROM parcel_utility WHERE parcel_id = ?", (parcel_id,))
            r = cursor.fetchone()
            return json.loads(r["assoc_json"]) if r else None

    # Synchronization
    def save_sync_run(self, run: Dict[str, Any]):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO sync_runs (dataset_id, status_json, updated_at)
                VALUES (?, ?, ?)
            """, (run["dataset_id"], json.dumps(run), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()

    def get_sync_runs(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status_json FROM sync_runs ORDER BY updated_at DESC")
            return [json.loads(row["status_json"]) for row in cursor.fetchall()]

    def save_feature_sync_changes(self, changes: List[Dict[str, Any]]):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for ch in changes:
                cursor.execute("""
                    INSERT OR REPLACE INTO feature_sync_changes (feature_id, change_json, updated_at)
                    VALUES (?, ?, ?)
                """, (ch["feature_id"], json.dumps(ch), now))
            conn.commit()

    def get_feature_sync_changes(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT change_json FROM feature_sync_changes ORDER BY updated_at DESC")
            return [json.loads(row["change_json"]) for row in cursor.fetchall()]

    def update_parcel_status(self, parcel_id: str, status: str, conflict_type: Optional[str] = None):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if conflict_type is not None:
                cursor.execute("UPDATE parcels SET status = ?, conflict_type = ? WHERE parcel_id = ?", (status, conflict_type, parcel_id))
            else:
                cursor.execute("UPDATE parcels SET status = ? WHERE parcel_id = ?", (status, parcel_id))
            conn.commit()

    # User Management
    def save_user(self, user: Dict[str, Any]):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO users (user_id, username, password_hash, role, full_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user["user_id"],
                user["username"],
                user["password_hash"],
                user.get("role", "STAFF"),
                user.get("full_name", ""),
                user.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            r = cursor.fetchone()
            if not r:
                return None
            return {
                "user_id": r["user_id"],
                "username": r["username"],
                "password_hash": r["password_hash"],
                "role": r["role"],
                "full_name": r["full_name"],
                "created_at": r["created_at"]
            }

    def get_all_users(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, role, full_name, created_at FROM users")
            return [dict(r) for r in cursor.fetchall()]

    # Audit Trail
    def save_audit_log(
        self,
        username: str = "admin",
        action: str = "ACTION",
        parcel_id: Optional[str] = None,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        confidence: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            user = username or kwargs.get("user_id", "admin")
            target = parcel_id or kwargs.get("target_id", "")
            d = details or {}
            if kwargs.get("target_type"):
                d["target_type"] = kwargs.get("target_type")
            log_id = f"LOG-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            cursor.execute("""
                INSERT INTO audit_logs (log_id, username, action, parcel_id, old_status, new_status, confidence, details_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id,
                user,
                action,
                target,
                old_status or "",
                new_status or "",
                confidence or 0.0,
                json.dumps(d),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()

    def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append({
                    "log_id": r["log_id"],
                    "username": r["username"],
                    "action": r["action"],
                    "parcel_id": r["parcel_id"],
                    "old_status": r["old_status"],
                    "new_status": r["new_status"],
                    "confidence": r["confidence"],
                    "details": json.loads(r["details_json"]) if r["details_json"] else {},
                    "timestamp": r["timestamp"]
                })
            return results

    # Georeferencing
    def save_georeferencing_job(self, job_or_id: Any, job_data: Optional[Dict[str, Any]] = None):
        job = job_data if job_data is not None else job_or_id
        if not isinstance(job, dict):
            return
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO georeferencing_jobs (
                    job_id, image_name, control_points_json, transform_json,
                    rmse, mean_residual, max_residual, status, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job["job_id"],
                job.get("image_name", ""),
                json.dumps(job.get("control_points", [])),
                json.dumps(job.get("transformation", {})),
                job.get("rmse", 0.0),
                job.get("mean_residual", 0.0),
                job.get("max_residual", 0.0),
                job.get("status", "COMPLETED"),
                job.get("created_by", "system"),
                job.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()

    def get_georeferencing_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM georeferencing_jobs WHERE job_id = ?", (job_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return {
                "job_id": r["job_id"],
                "image_name": r["image_name"],
                "control_points": json.loads(r["control_points_json"]) if r["control_points_json"] else [],
                "transformation": json.loads(r["transform_json"]) if r["transform_json"] else {},
                "rmse": r["rmse"],
                "mean_residual": r["mean_residual"],
                "max_residual": r["max_residual"],
                "status": r["status"],
                "created_by": r["created_by"],
                "created_at": r["created_at"]
            }

    # Change Detection
    def save_change_detection_results(self, changes: List[Dict[str, Any]]):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for c in changes:
                cursor.execute("""
                    INSERT OR REPLACE INTO change_detection_results (
                        change_id, change_type, confidence, geometry_json, before_date, after_date, source, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    c["change_id"],
                    c.get("change_type", "BUILDING_ADDED"),
                    c.get("confidence", 0.0),
                    json.dumps(c.get("geometry", {})),
                    c.get("before_date", ""),
                    c.get("after_date", ""),
                    c.get("source", "RASTER_CHANGE_DETECTION"),
                    c.get("created_at") or now
                ))
            conn.commit()

    def get_change_detection_results(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM change_detection_results ORDER BY created_at DESC")
            return [{
                "change_id": r["change_id"],
                "change_type": r["change_type"],
                "confidence": r["confidence"],
                "geometry": json.loads(r["geometry_json"]) if r["geometry_json"] else {},
                "before_date": r["before_date"],
                "after_date": r["after_date"],
                "source": r["source"],
                "created_at": r["created_at"]
            } for r in cursor.fetchall()]

    # Building Extractions
    def save_building_extractions(self, buildings: List[Dict[str, Any]]):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for b in buildings:
                b_id = b.get("building_id") or f"BLD-{id(b)}"
                cursor.execute("""
                    INSERT OR REPLACE INTO building_extractions (
                        building_id, parcel_uid, survey_number, geometry_json, area_m2, confidence, model, inference_mode, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    b_id,
                    b.get("parcel_uid", ""),
                    b.get("survey_number", ""),
                    json.dumps(b.get("geometry_geojson") or b.get("geometry", {})),
                    b.get("area_m2", 0.0),
                    b.get("confidence", 0.0),
                    b.get("model_version") or b.get("model", "YOLOv8-Seg"),
                    b.get("inference_mode") or b.get("execution_mode", "ONNX"),
                    b.get("detected_at") or now
                ))
            conn.commit()

    def get_building_extractions(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM building_extractions ORDER BY created_at DESC")
            return [{
                "building_id": r["building_id"],
                "parcel_uid": r["parcel_uid"],
                "survey_number": r["survey_number"],
                "geometry_geojson": json.loads(r["geometry_json"]) if r["geometry_json"] else {},
                "area_m2": r["area_m2"],
                "confidence": r["confidence"],
                "model_version": r["model"],
                "inference_mode": r["inference_mode"],
                "detected_at": r["created_at"]
            } for r in cursor.fetchall()]

    # Shared Boundary Proposals
    def save_shared_boundary_proposal(self, proposal_or_id: Any, proposal_data: Optional[Dict[str, Any]] = None):
        proposal = proposal_data if proposal_data is not None else proposal_or_id
        if not isinstance(proposal, dict):
            return
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO shared_boundary_proposals (
                    proposal_id, parcel_a_id, parcel_b_id, original_geom_a, original_geom_b,
                    split_geom_a, split_geom_b, area_diff_a, area_diff_b, confidence, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal["proposal_id"],
                proposal["parcel_a_id"],
                proposal["parcel_b_id"],
                json.dumps(proposal.get("original_geom_a", {})),
                json.dumps(proposal.get("original_geom_b", {})),
                json.dumps(proposal.get("split_geom_a", {})),
                json.dumps(proposal.get("split_geom_b", {})),
                proposal.get("area_diff_a", 0.0),
                proposal.get("area_diff_b", 0.0),
                proposal.get("confidence", 0.0),
                proposal.get("status", "PROPOSED"),
                proposal.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()

    def get_shared_boundary_proposals(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM shared_boundary_proposals ORDER BY created_at DESC")
            return [{
                "proposal_id": r["proposal_id"],
                "parcel_a_id": r["parcel_a_id"],
                "parcel_b_id": r["parcel_b_id"],
                "original_geom_a": json.loads(r["original_geom_a"]) if r["original_geom_a"] else {},
                "original_geom_b": json.loads(r["original_geom_b"]) if r["original_geom_b"] else {},
                "split_geom_a": json.loads(r["split_geom_a"]) if r["split_geom_a"] else {},
                "split_geom_b": json.loads(r["split_geom_b"]) if r["split_geom_b"] else {},
                "area_diff_a": r["area_diff_a"],
                "area_diff_b": r["area_diff_b"],
                "confidence": r["confidence"],
                "status": r["status"],
                "created_at": r["created_at"]
            } for r in cursor.fetchall()]

    def get_shared_boundary_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM shared_boundary_proposals WHERE proposal_id = ?", (proposal_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return {
                "proposal_id": r["proposal_id"],
                "parcel_a_id": r["parcel_a_id"],
                "parcel_b_id": r["parcel_b_id"],
                "original_geom_a": json.loads(r["original_geom_a"]) if r["original_geom_a"] else {},
                "original_geom_b": json.loads(r["original_geom_b"]) if r["original_geom_b"] else {},
                "split_geom_a": json.loads(r["split_geom_a"]) if r["split_geom_a"] else {},
                "split_geom_b": json.loads(r["split_geom_b"]) if r["split_geom_b"] else {},
                "area_diff_a": r["area_diff_a"],
                "area_diff_b": r["area_diff_b"],
                "confidence": r["confidence"],
                "status": r["status"],
                "created_at": r["created_at"]
            }

    def update_shared_boundary_proposal(self, proposal_id: str, status_or_updates: Any):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if isinstance(status_or_updates, dict):
                st = status_or_updates.get("status", "UPDATED")
            else:
                st = str(status_or_updates)
            cursor.execute("UPDATE shared_boundary_proposals SET status = ? WHERE proposal_id = ?", (st, proposal_id))
            conn.commit()

    # Processing Jobs
    def save_processing_job(self, job: Dict[str, Any]):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT OR REPLACE INTO processing_jobs (
                    job_id, job_type, status, progress, processed_count, total_count, error_message, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job["job_id"],
                job.get("job_type", "GENERAL"),
                job.get("status", "QUEUED"),
                job.get("progress", 0),
                job.get("processed_count", 0),
                job.get("total_count", 0),
                job.get("error_message", ""),
                json.dumps(job.get("metadata", {})),
                job.get("created_at") or now,
                now
            ))
            conn.commit()

    def update_processing_job(
        self,
        job_id: str,
        progress: Optional[int] = None,
        status: Optional[str] = None,
        processed: Optional[int] = None,
        total: Optional[int] = None,
        error: Optional[str] = None
    ):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("SELECT * FROM processing_jobs WHERE job_id = ?", (job_id,))
            r = cursor.fetchone()
            if not r:
                return
            new_status = status if status is not None else r["status"]
            new_progress = progress if progress is not None else r["progress"]
            new_processed = processed if processed is not None else r["processed_count"]
            new_total = total if total is not None else r["total_count"]
            new_error = error if error is not None else r["error_message"]

            cursor.execute("""
                UPDATE processing_jobs
                SET status = ?, progress = ?, processed_count = ?, total_count = ?, error_message = ?, updated_at = ?
                WHERE job_id = ?
            """, (new_status, new_progress, new_processed, new_total, new_error, now, job_id))
            conn.commit()

    def get_processing_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM processing_jobs WHERE job_id = ?", (job_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return {
                "job_id": r["job_id"],
                "job_type": r["job_type"],
                "status": r["status"],
                "progress": r["progress"],
                "processed": r["processed_count"],
                "total": r["total_count"],
                "errors": 1 if r["error_message"] else 0,
                "error_message": r["error_message"],
                "metadata": json.loads(r["metadata_json"]) if r["metadata_json"] else {},
                "created_at": r["created_at"],
                "updated_at": r["updated_at"]
            }

    def get_processing_jobs(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM processing_jobs ORDER BY created_at DESC")
            return [{
                "job_id": r["job_id"],
                "job_type": r["job_type"],
                "status": r["status"],
                "progress": r["progress"],
                "processed": r["processed_count"],
                "total": r["total_count"],
                "errors": 1 if r["error_message"] else 0,
                "error_message": r["error_message"],
                "metadata": json.loads(r["metadata_json"]) if r["metadata_json"] else {},
                "created_at": r["created_at"],
                "updated_at": r["updated_at"]
            } for r in cursor.fetchall()]

    # OCR Documents
    def save_ocr_document(self, doc: Dict[str, Any]):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT OR REPLACE INTO ocr_documents (
                    doc_id, filename, file_type, extracted_fields_json, raw_text, verified, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                doc["doc_id"],
                doc.get("filename", ""),
                doc.get("file_type", "image"),
                json.dumps(doc.get("fields", {})),
                doc.get("raw_text", ""),
                1 if doc.get("verified") else 0,
                doc.get("created_at") or now
            ))
            conn.commit()

    def get_ocr_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ocr_documents WHERE doc_id = ?", (doc_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return {
                "doc_id": r["doc_id"],
                "filename": r["filename"],
                "file_type": r["file_type"],
                "fields": json.loads(r["extracted_fields_json"]) if r["extracted_fields_json"] else {},
                "raw_text": r["raw_text"],
                "verified": bool(r["verified"]),
                "created_at": r["created_at"]
            }

    def get_ocr_documents(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ocr_documents ORDER BY created_at DESC")
            return [{
                "doc_id": r["doc_id"],
                "filename": r["filename"],
                "file_type": r["file_type"],
                "fields": json.loads(r["extracted_fields_json"]) if r["extracted_fields_json"] else {},
                "raw_text": r["raw_text"],
                "verified": bool(r["verified"]),
                "created_at": r["created_at"]
            } for r in cursor.fetchall()]

    def update_ocr_document(self, doc_id: str, fields: Dict[str, Any], verified: bool = True):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ocr_documents
                SET extracted_fields_json = ?, verified = ?
                WHERE doc_id = ?
            """, (json.dumps(fields), 1 if verified else 0, doc_id))
            conn.commit()

storage_repo = StorageRepository()
