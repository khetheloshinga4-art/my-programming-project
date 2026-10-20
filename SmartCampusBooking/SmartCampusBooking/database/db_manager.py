"""
Database Manager for Smart Campus Resource Booking System.
Handles all SQLite persistence: users, campuses, resources, bookings.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any


class DatabaseManager:
    """Encapsulates all database operations with connection management."""

    def __init__(self, db_path: str = "campus_booking.db"):
        # Place DB next to the main application for easy portability
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, db_path)
        self._initialize_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _initialize_database(self) -> None:
        """Create tables if they do not exist and seed initial data."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('lecturer', 'campus_admin', 'system_operator')),
                    campus_id INTEGER,
                    email TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (campus_id) REFERENCES campuses(campus_id)
                )
            """)

            # Campuses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS campuses (
                    campus_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    location TEXT NOT NULL,
                    max_booking_hours REAL NOT NULL,
                    booking_start_hour INTEGER NOT NULL,
                    booking_end_hour INTEGER NOT NULL,
                    description TEXT
                )
            """)

            # Resources table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resources (
                    resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campus_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    capacity INTEGER DEFAULT 1,
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    UNIQUE(campus_id, name),
                    FOREIGN KEY (campus_id) REFERENCES campuses(campus_id)
                )
            """)

            # Bookings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    campus_id INTEGER NOT NULL,
                    booking_date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    duration_hours REAL NOT NULL,
                    end_time TEXT NOT NULL,
                    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'cancelled', 'completed')),
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (resource_id) REFERENCES resources(resource_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (campus_id) REFERENCES campuses(campus_id)
                )
            """)

            conn.commit()

        # Seed initial data only if tables are empty
        self._seed_initial_data()

    def _seed_initial_data(self) -> None:
        """Insert default campuses, sample resources, and admin accounts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if campuses already exist
            cursor.execute("SELECT COUNT(*) FROM campuses")
            if cursor.fetchone()[0] > 0:
                return  # Already seeded

            # Three campuses with different booking policies
            campuses = [
                ("Johannesburg Campus", "Johannesburg, Gauteng", 4.0, 8, 18,
                 "Main campus – max 4 hours per booking, 08:00-18:00"),
                ("Cape Town Campus", "Cape Town, Western Cape", 2.0, 9, 17,
                 "Coastal campus – max 2 hours per booking, 09:00-17:00"),
                ("Durban Campus", "Durban, KwaZulu-Natal", 3.0, 7, 19,
                 "Coastal campus – max 3 hours per booking, 07:00-19:00"),
            ]
            cursor.executemany("""
                INSERT INTO campuses (name, location, max_booking_hours,
                                      booking_start_hour, booking_end_hour, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, campuses)

            # Sample resources for each campus
            resources = [
                # Johannesburg (campus_id will be 1)
                (1, "Computer Lab A", "Computer Laboratory", 40, "40 workstations with dual monitors"),
                (1, "Computer Lab B", "Computer Laboratory", 30, "30 workstations"),
                (1, "Seminar Room 1", "Seminar Room", 25, "Projector and whiteboard"),
                (1, "Multimedia Projector 1", "Projector", 1, "Portable HD projector"),
                (1, "Presentation Suite", "Presentation Equipment", 1, "Full AV suite"),
                # Cape Town (campus_id 2)
                (2, "Computer Lab CT-1", "Computer Laboratory", 35, "35 workstations"),
                (2, "Lecture Theatre CT", "Seminar Room", 80, "Large lecture theatre"),
                (2, "Projector CT-A", "Projector", 1, "Ceiling-mounted projector"),
                (2, "Meeting Room CT", "Seminar Room", 12, "Small meeting room"),
                # Durban (campus_id 3)
                (3, "Computer Lab DB-1", "Computer Laboratory", 28, "28 workstations"),
                (3, "Seminar Room DB-A", "Seminar Room", 20, "Standard seminar room"),
                (3, "AV Equipment Set", "Presentation Equipment", 1, "Portable AV kit"),
                (3, "Conference Hall", "Seminar Room", 50, "Conference hall with stage"),
            ]
            cursor.executemany("""
                INSERT INTO resources (campus_id, name, resource_type, capacity, description)
                VALUES (?, ?, ?, ?, ?)
            """, resources)

            # Default system accounts (passwords are plain for demo; production would hash)
            # password for all demo accounts: password123
            users = [
                ("sysop", "password123", "System Operator", "system_operator", None, "sysop@richfield.ac.za"),
                ("admin_jhb", "password123", "JHB Campus Admin", "campus_admin", 1, "admin.jhb@richfield.ac.za"),
                ("admin_cpt", "password123", "CPT Campus Admin", "campus_admin", 2, "admin.cpt@richfield.ac.za"),
                ("admin_dbn", "password123", "DBN Campus Admin", "campus_admin", 3, "admin.dbn@richfield.ac.za"),
                ("lecturer1", "password123", "Dr. Thabo Molefe", "lecturer", None, "t.molefe@richfield.ac.za"),
                ("lecturer2", "password123", "Ms. Sarah Naidoo", "lecturer", None, "s.naidoo@richfield.ac.za"),
            ]
            cursor.executemany("""
                INSERT INTO users (username, password, full_name, role, campus_id, email)
                VALUES (?, ?, ?, ?, ?, ?)
            """, users)

            conn.commit()

    # ------------------------------------------------------------------
    # User operations
    # ------------------------------------------------------------------
    def register_user(self, username: str, password: str, full_name: str,
                      role: str = "lecturer", campus_id: Optional[int] = None,
                      email: str = "") -> Tuple[bool, str]:
        """Register a new user. Returns (success, message)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, password, full_name, role, campus_id, email)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, password, full_name, role, campus_id, email))
                conn.commit()
                return True, "Registration successful. You may now log in."
        except sqlite3.IntegrityError:
            return False, "Username already exists. Please choose another."
        except Exception as e:
            return False, f"Registration failed: {str(e)}"

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user record as dict, or None."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, username, full_name, role, campus_id, email
                FROM users WHERE username = ? AND password = ?
            """, (username, password))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ------------------------------------------------------------------
    # Campus operations
    # ------------------------------------------------------------------
    def get_all_campuses(self) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM campuses ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]

    def get_campus_by_id(self, campus_id: int) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM campuses WHERE campus_id = ?", (campus_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ------------------------------------------------------------------
    # Resource operations
    # ------------------------------------------------------------------
    def get_resources_by_campus(self, campus_id: int, active_only: bool = True) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute("""
                    SELECT * FROM resources
                    WHERE campus_id = ? AND is_active = 1
                    ORDER BY resource_type, name
                """, (campus_id,))
            else:
                cursor.execute("""
                    SELECT * FROM resources WHERE campus_id = ?
                    ORDER BY resource_type, name
                """, (campus_id,))
            return [dict(row) for row in cursor.fetchall()]

    def add_resource(self, campus_id: int, name: str, resource_type: str,
                     capacity: int = 1, description: str = "") -> Tuple[bool, str]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO resources (campus_id, name, resource_type, capacity, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (campus_id, name, resource_type, capacity, description))
                conn.commit()
                return True, f"Resource '{name}' added successfully."
        except sqlite3.IntegrityError:
            return False, "A resource with this name already exists at the campus."
        except Exception as e:
            return False, f"Failed to add resource: {str(e)}"

    def update_resource(self, resource_id: int, name: str, resource_type: str,
                        capacity: int, description: str, is_active: int = 1) -> Tuple[bool, str]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE resources
                    SET name = ?, resource_type = ?, capacity = ?, description = ?, is_active = ?
                    WHERE resource_id = ?
                """, (name, resource_type, capacity, description, is_active, resource_id))
                conn.commit()
                if cursor.rowcount == 0:
                    return False, "Resource not found."
                return True, "Resource updated successfully."
        except sqlite3.IntegrityError:
            return False, "Duplicate resource name at this campus."
        except Exception as e:
            return False, f"Update failed: {str(e)}"

    def delete_resource(self, resource_id: int) -> Tuple[bool, str]:
        """Soft-delete by setting is_active = 0, or hard-delete if no bookings."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Check for active bookings
                cursor.execute("""
                    SELECT COUNT(*) FROM bookings
                    WHERE resource_id = ? AND status = 'active'
                """, (resource_id,))
                if cursor.fetchone()[0] > 0:
                    # Soft delete
                    cursor.execute("UPDATE resources SET is_active = 0 WHERE resource_id = ?",
                                   (resource_id,))
                    conn.commit()
                    return True, "Resource deactivated (has active bookings)."
                else:
                    cursor.execute("DELETE FROM resources WHERE resource_id = ?", (resource_id,))
                    conn.commit()
                    return True, "Resource permanently removed."
        except Exception as e:
            return False, f"Delete failed: {str(e)}"

    def get_resource_by_id(self, resource_id: int) -> Optional[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM resources WHERE resource_id = ?", (resource_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ------------------------------------------------------------------
    # Booking operations
    # ------------------------------------------------------------------
    def create_booking(self, resource_id: int, user_id: int, campus_id: int,
                       booking_date: str, start_time: str, duration_hours: float,
                       notes: str = "") -> Tuple[bool, str]:
        """Create a booking after validating no overlap."""
        try:
            # Calculate end time
            start_h, start_m = map(int, start_time.split(":"))
            total_minutes = start_h * 60 + start_m + int(duration_hours * 60)
            end_h = total_minutes // 60
            end_m = total_minutes % 60
            end_time = f"{end_h:02d}:{end_m:02d}"

            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Check for overlapping active bookings on same resource & date
                cursor.execute("""
                    SELECT booking_id, start_time, end_time FROM bookings
                    WHERE resource_id = ? AND booking_date = ? AND status = 'active'
                """, (resource_id, booking_date))
                existing = cursor.fetchall()

                for b in existing:
                    # Simple overlap check: start < other_end AND end > other_start
                    if start_time < b["end_time"] and end_time > b["start_time"]:
                        return False, f"Overlapping booking exists ({b['start_time']}-{b['end_time']})."

                cursor.execute("""
                    INSERT INTO bookings
                    (resource_id, user_id, campus_id, booking_date, start_time,
                     duration_hours, end_time, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (resource_id, user_id, campus_id, booking_date, start_time,
                      duration_hours, end_time, notes))
                conn.commit()
                return True, "Booking created successfully."
        except Exception as e:
            return False, f"Booking failed: {str(e)}"

    def get_user_bookings(self, user_id: int, status: Optional[str] = None) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("""
                    SELECT b.*, r.name AS resource_name, c.name AS campus_name
                    FROM bookings b
                    JOIN resources r ON b.resource_id = r.resource_id
                    JOIN campuses c ON b.campus_id = c.campus_id
                    WHERE b.user_id = ? AND b.status = ?
                    ORDER BY b.booking_date DESC, b.start_time DESC
                """, (user_id, status))
            else:
                cursor.execute("""
                    SELECT b.*, r.name AS resource_name, c.name AS campus_name
                    FROM bookings b
                    JOIN resources r ON b.resource_id = r.resource_id
                    JOIN campuses c ON b.campus_id = c.campus_id
                    WHERE b.user_id = ?
                    ORDER BY b.booking_date DESC, b.start_time DESC
                """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_campus_bookings(self, campus_id: int, status: Optional[str] = None) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("""
                    SELECT b.*, r.name AS resource_name, u.full_name AS lecturer_name
                    FROM bookings b
                    JOIN resources r ON b.resource_id = r.resource_id
                    JOIN users u ON b.user_id = u.user_id
                    WHERE b.campus_id = ? AND b.status = ?
                    ORDER BY b.booking_date DESC, b.start_time DESC
                """, (campus_id, status))
            else:
                cursor.execute("""
                    SELECT b.*, r.name AS resource_name, u.full_name AS lecturer_name
                    FROM bookings b
                    JOIN resources r ON b.resource_id = r.resource_id
                    JOIN users u ON b.user_id = u.user_id
                    WHERE b.campus_id = ?
                    ORDER BY b.booking_date DESC, b.start_time DESC
                """, (campus_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_all_bookings(self, status: Optional[str] = None) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("""
                    SELECT b.*, r.name AS resource_name, c.name AS campus_name,
                           u.full_name AS lecturer_name
                    FROM bookings b
                    JOIN resources r ON b.resource_id = r.resource_id
                    JOIN campuses c ON b.campus_id = c.campus_id
                    JOIN users u ON b.user_id = u.user_id
                    WHERE b.status = ?
                    ORDER BY b.booking_date DESC, b.start_time DESC
                """, (status,))
            else:
                cursor.execute("""
                    SELECT b.*, r.name AS resource_name, c.name AS campus_name,
                           u.full_name AS lecturer_name
                    FROM bookings b
                    JOIN resources r ON b.resource_id = r.resource_id
                    JOIN campuses c ON b.campus_id = c.campus_id
                    JOIN users u ON b.user_id = u.user_id
                    ORDER BY b.booking_date DESC, b.start_time DESC
                """)
            return [dict(row) for row in cursor.fetchall()]

    def cancel_booking(self, booking_id: int, user_id: int) -> Tuple[bool, str]:
        """Cancel a future booking belonging to the user."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT booking_date, start_time, status FROM bookings
                    WHERE booking_id = ? AND user_id = ?
                """, (booking_id, user_id))
                row = cursor.fetchone()
                if not row:
                    return False, "Booking not found or does not belong to you."
                if row["status"] != "active":
                    return False, "Only active bookings can be cancelled."

                # Check if booking is in the future
                booking_dt = datetime.strptime(
                    f"{row['booking_date']} {row['start_time']}", "%Y-%m-%d %H:%M"
                )
                if booking_dt <= datetime.now():
                    return False, "Past or ongoing bookings cannot be cancelled."

                cursor.execute("""
                    UPDATE bookings SET status = 'cancelled' WHERE booking_id = ?
                """, (booking_id,))
                conn.commit()
                return True, "Booking cancelled successfully."
        except Exception as e:
            return False, f"Cancellation failed: {str(e)}"

    def get_bookings_for_resource_on_date(self, resource_id: int, booking_date: str) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM bookings
                WHERE resource_id = ? AND booking_date = ? AND status = 'active'
                ORDER BY start_time
            """, (resource_id, booking_date))
            return [dict(row) for row in cursor.fetchall()]

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def get_campus_report(self, campus_id: int) -> Dict[str, Any]:
        """Generate campus-level statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total bookings (all statuses for historical view)
            cursor.execute("""
                SELECT COUNT(*) AS total FROM bookings WHERE campus_id = ?
            """, (campus_id,))
            total_bookings = cursor.fetchone()["total"]

            # Active bookings
            cursor.execute("""
                SELECT COUNT(*) AS active FROM bookings
                WHERE campus_id = ? AND status = 'active'
            """, (campus_id,))
            active_bookings = cursor.fetchone()["active"]

            # Most frequently used resources
            cursor.execute("""
                SELECT r.name, COUNT(b.booking_id) AS booking_count
                FROM bookings b
                JOIN resources r ON b.resource_id = r.resource_id
                WHERE b.campus_id = ?
                GROUP BY r.resource_id
                ORDER BY booking_count DESC
                LIMIT 5
            """, (campus_id,))
            top_resources = [dict(row) for row in cursor.fetchall()]

            # Average booking duration
            cursor.execute("""
                SELECT AVG(duration_hours) AS avg_duration
                FROM bookings WHERE campus_id = ? AND status != 'cancelled'
            """, (campus_id,))
            avg_row = cursor.fetchone()
            avg_duration = round(avg_row["avg_duration"] or 0, 2)

            return {
                "total_bookings": total_bookings,
                "active_bookings": active_bookings,
                "top_resources": top_resources,
                "avg_duration": avg_duration,
            }

    def get_cross_campus_report(self) -> List[Dict]:
        """Comparative report across all campuses."""
        campuses = self.get_all_campuses()
        reports = []
        for campus in campuses:
            report = self.get_campus_report(campus["campus_id"])
            report["campus_id"] = campus["campus_id"]
            report["campus_name"] = campus["name"]
            report["max_booking_hours"] = campus["max_booking_hours"]
            report["booking_hours"] = f"{campus['booking_start_hour']:02d}:00 - {campus['booking_end_hour']:02d}:00"
            reports.append(report)
        return reports
