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

storage_repo = StorageRepository()
