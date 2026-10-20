"""
User hierarchy implementing OOP principles:
- Base User class with encapsulation
- Inheritance for Lecturer, CampusAdministrator, SystemOperator
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any


class User(ABC):
    """Abstract base class for all system users. Demonstrates encapsulation."""

    def __init__(self, user_id: int, username: str, full_name: str,
                 role: str, campus_id: Optional[int] = None, email: str = ""):
        self._user_id = user_id
        self._username = username
        self._full_name = full_name
        self._role = role
        self._campus_id = campus_id
        self._email = email

    # Encapsulated getters
    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def full_name(self) -> str:
        return self._full_name

    @property
    def role(self) -> str:
        return self._role

    @property
    def campus_id(self) -> Optional[int]:
        return self._campus_id

    @property
    def email(self) -> str:
        return self._email

    def __str__(self) -> str:
        return f"{self._full_name} ({self._role})"

    @abstractmethod
    def get_permissions(self) -> List[str]:
        """Return list of permission strings for this role."""
        pass

    def can(self, permission: str) -> bool:
        return permission in self.get_permissions()


class Lecturer(User):
    """Lecturer role – can book resources and manage own bookings."""

    def __init__(self, user_id: int, username: str, full_name: str,
                 campus_id: Optional[int] = None, email: str = ""):
        super().__init__(user_id, username, full_name, "lecturer", campus_id, email)

    def get_permissions(self) -> List[str]:
        return [
            "view_resources",
            "create_booking",
            "view_own_bookings",
            "cancel_own_booking",
            "view_availability",
        ]


class CampusAdministrator(User):
    """Campus Administrator – manages resources and bookings for one campus."""

    def __init__(self, user_id: int, username: str, full_name: str,
                 campus_id: int, email: str = ""):
        super().__init__(user_id, username, full_name, "campus_admin", campus_id, email)

    def get_permissions(self) -> List[str]:
        return [
            "view_resources",
            "add_resource",
            "update_resource",
            "remove_resource",
            "view_campus_bookings",
            "view_campus_reports",
            "view_availability",
        ]


class SystemOperator(User):
    """System Operator – full institutional access and cross-campus reports."""

    def __init__(self, user_id: int, username: str, full_name: str, email: str = ""):
        super().__init__(user_id, username, full_name, "system_operator", None, email)

    def get_permissions(self) -> List[str]:
        return [
            "view_resources",
            "view_all_bookings",
            "view_all_reports",
            "view_cross_campus_reports",
            "view_availability",
            "manage_all_campuses",
        ]


def create_user_from_dict(data: Dict[str, Any]) -> User:
    """Factory function to instantiate the correct User subclass from DB row."""
    role = data.get("role")
    if role == "lecturer":
        return Lecturer(
            data["user_id"], data["username"], data["full_name"],
            data.get("campus_id"), data.get("email", "")
        )
    elif role == "campus_admin":
        return CampusAdministrator(
            data["user_id"], data["username"], data["full_name"],
            data["campus_id"], data.get("email", "")
        )
    elif role == "system_operator":
        return SystemOperator(
            data["user_id"], data["username"], data["full_name"],
            data.get("email", "")
        )
    else:
        raise ValueError(f"Unknown role: {role}")
