import json
import statistics
from shapely.geometry import shape
from backend.app.models.storage import storage_repo
from backend.app.services.geometry.crs import project_geometry

p003 = storage_repo.get_parcel_detail("P003")
assert p003 is not None, "P003 must exist in storage"

p1_proj = project_geometry(shape(p003["geometry_geojson"]), "EPSG:4326", "EPSG:32643")
p2_proj = project_geometry(shape(p003["drone_geometry_geojson"]), "EPSG:4326", "EPSG:32643")

ext_a = p1_proj.exterior
ext_b = p2_proj.exterior

step = 0.5
num_a = max(20, int(ext_a.length / step))
num_b = max(20, int(ext_b.length / step))
dists_a = [ext_b.distance(ext_a.interpolate(i * step)) for i in range(num_a)]
dists_b = [ext_a.distance(ext_b.interpolate(i * step)) for i in range(num_b)]
all_dists = sorted(dists_a + dists_b)

n = len(all_dists)
mean_dev = statistics.mean(all_dists)
median_dev = statistics.median(all_dists)
p90_dev = all_dists[int(0.90 * (n - 1))]
p95_dev = all_dists[int(0.95 * (n - 1))]
p99_dev = all_dists[int(0.99 * (n - 1))]
max_dev = max(all_dists)

pct_1_0m = (sum(1 for d in all_dists if d <= 1.0) / n) * 100.0
pct_1_5m = (sum(1 for d in all_dists if d <= 1.5) / n) * 100.0
pct_2_0m = (sum(1 for d in all_dists if d <= 2.0) / n) * 100.0
pct_3_0m = (sum(1 for d in all_dists if d <= 3.0) / n) * 100.0

print(f"=== P003 (Survey 184/2) BOUNDARY SAMPLING REPORT (0.5m interval) ===")
print(f"Perimeter Legacy: {round(ext_a.length, 2)} m, Perimeter Candidate: {round(ext_b.length, 2)} m")
print(f"Sample points evaluated: {n}")
print(f"Mean deviation: {round(mean_dev, 4)} m")
print(f"Median deviation: {round(median_dev, 4)} m")
print(f"P90 deviation: {round(p90_dev, 4)} m")
print(f"P95 deviation: {round(p95_dev, 4)} m")
print(f"P99 deviation: {round(p99_dev, 4)} m")
print(f"Max deviation: {round(max_dev, 4)} m")
print(f"Percentage <= 1.0m: {round(pct_1_0m, 2)}%")
print(f"Percentage <= 1.5m: {round(pct_1_5m, 2)}%")
print(f"Percentage <= 2.0m: {round(pct_2_0m, 2)}%")
print(f"Percentage <= 3.0m: {round(pct_3_0m, 2)}%")
