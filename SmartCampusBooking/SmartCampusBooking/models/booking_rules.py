"""
Campus-specific Booking Rules.
Separated from core logic so new campuses / policies can be added easily.
Each campus has its own policy class implementing a common interface.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Optional
from datetime import datetime, time


class BookingPolicy(ABC):
    """Abstract base for campus booking policies."""

    def __init__(self, campus_id: int, campus_name: str,
                 max_hours: float, start_hour: int, end_hour: int):
        self.campus_id = campus_id
        self.campus_name = campus_name
        self.max_hours = max_hours
        self.start_hour = start_hour
        self.end_hour = end_hour

    @abstractmethod
    def validate_booking(self, duration_hours: float, start_time_str: str,
                         booking_date: str) -> Tuple[bool, str]:
        """Return (is_valid, error_message)."""
        pass

    def get_policy_description(self) -> str:
        return (
            f"{self.campus_name}: Max {self.max_hours}h per session, "
            f"hours {self.start_hour:02d}:00–{self.end_hour:02d}:00"
        )

    def _parse_time(self, time_str: str) -> time:
        h, m = map(int, time_str.split(":"))
        return time(h, m)


class JohannesburgPolicy(BookingPolicy):
    """Johannesburg – longer sessions allowed, standard business hours."""

    def validate_booking(self, duration_hours: float, start_time_str: str,
                         booking_date: str) -> Tuple[bool, str]:
        if duration_hours <= 0:
            return False, "Duration must be greater than zero."
        if duration_hours > self.max_hours:
            return False, f"Maximum booking duration is {self.max_hours} hours at Johannesburg Campus."

        start = self._parse_time(start_time_str)
        if start.hour < self.start_hour or start.hour >= self.end_hour:
            return False, f"Bookings only allowed between {self.start_hour:02d}:00 and {self.end_hour:02d}:00."

        # End time must also stay within allowed hours
        total_minutes = start.hour * 60 + start.minute + int(duration_hours * 60)
        end_hour = total_minutes // 60
        if end_hour > self.end_hour or (end_hour == self.end_hour and total_minutes % 60 > 0):
            return False, f"Booking would end after {self.end_hour:02d}:00. Please shorten the duration."

        return True, "OK"


class CapeTownPolicy(BookingPolicy):
    """Cape Town – shorter max duration, slightly later start."""

    def validate_booking(self, duration_hours: float, start_time_str: str,
                         booking_date: str) -> Tuple[bool, str]:
        if duration_hours <= 0:
            return False, "Duration must be greater than zero."
        if duration_hours > self.max_hours:
            return False, f"Maximum booking duration is {self.max_hours} hours at Cape Town Campus."

        start = self._parse_time(start_time_str)
        if start.hour < self.start_hour or start.hour >= self.end_hour:
            return False, f"Bookings only allowed between {self.start_hour:02d}:00 and {self.end_hour:02d}:00."

        total_minutes = start.hour * 60 + start.minute + int(duration_hours * 60)
        end_hour = total_minutes // 60
        if end_hour > self.end_hour or (end_hour == self.end_hour and total_minutes % 60 > 0):
            return False, f"Booking would end after {self.end_hour:02d}:00. Please shorten the duration."

        # Extra rule: no bookings on weekends (example of campus-specific rule)
        try:
            dt = datetime.strptime(booking_date, "%Y-%m-%d")
            if dt.weekday() >= 5:  # Saturday=5, Sunday=6
                return False, "Cape Town Campus does not allow weekend bookings."
        except ValueError:
            return False, "Invalid booking date format."

        return True, "OK"


class DurbanPolicy(BookingPolicy):
    """Durban – extended early/late hours, medium max duration."""

    def validate_booking(self, duration_hours: float, start_time_str: str,
                         booking_date: str) -> Tuple[bool, str]:
        if duration_hours <= 0:
            return False, "Duration must be greater than zero."
        if duration_hours > self.max_hours:
            return False, f"Maximum booking duration is {self.max_hours} hours at Durban Campus."

        start = self._parse_time(start_time_str)
        if start.hour < self.start_hour or start.hour >= self.end_hour:
            return False, f"Bookings only allowed between {self.start_hour:02d}:00 and {self.end_hour:02d}:00."

        total_minutes = start.hour * 60 + start.minute + int(duration_hours * 60)
        end_hour = total_minutes // 60
        if end_hour > self.end_hour or (end_hour == self.end_hour and total_minutes % 60 > 0):
            return False, f"Booking would end after {self.end_hour:02d}:00. Please shorten the duration."

        return True, "OK"


# Registry – easy to extend with new campuses
POLICY_REGISTRY: Dict[int, type] = {
    1: JohannesburgPolicy,
    2: CapeTownPolicy,
    3: DurbanPolicy,
}


def get_policy_for_campus(campus: Dict) -> BookingPolicy:
    """Factory that returns the correct policy instance for a campus record."""
    campus_id = campus["campus_id"]
    policy_cls = POLICY_REGISTRY.get(campus_id, JohannesburgPolicy)
    return policy_cls(
        campus_id=campus_id,
        campus_name=campus["name"],
        max_hours=campus["max_booking_hours"],
        start_hour=campus["booking_start_hour"],
        end_hour=campus["booking_end_hour"],
    )
