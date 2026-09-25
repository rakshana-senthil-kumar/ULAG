"""
Role-Based Authentication & Access Control Manager for BHUMI-FUSION V2
Supports user roles (ADMIN, GIS_OPERATOR, REVIEW_OFFICER, VIEWER) and permission checks.
"""

from typing import Dict, List, Any, Optional

USER_ROLES = {
    "ADMIN": {
        "permissions": ["ingest", "edit", "reconcile", "resolve_conflict", "publish", "admin"]
    },
    "GIS_OPERATOR": {
        "permissions": ["ingest", "edit", "reconcile", "resolve_conflict"]
    },
    "REVIEW_OFFICER": {
        "permissions": ["reconcile", "resolve_conflict", "publish"]
    },
    "VIEWER": {
        "permissions": ["read_only"]
    }
}

class AuthManager:
    def __init__(self, current_role: str = "REVIEW_OFFICER"):
        self.current_role = current_role

    def is_authorized(self, action: str, role: str = None) -> bool:
        user_role = role or self.current_role
        perms = USER_ROLES.get(user_role, {}).get("permissions", [])
        if "admin" in perms or "read_only" in perms and action == "read":
            return True
        return action in perms

    def get_role_metadata(self, role: str = None) -> Dict[str, Any]:
        user_role = role or self.current_role
        return {
            "role": user_role,
            "permissions": USER_ROLES.get(user_role, {}).get("permissions", [])
        }

auth_manager = AuthManager()
