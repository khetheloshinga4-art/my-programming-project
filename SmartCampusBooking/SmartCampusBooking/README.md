# Smart Campus Resource Booking System

**Richfield Graduate Institution – PROGRAMMING 512 Assignment**

A fully functional Python desktop application that allows lecturers, campus administrators and system operators to manage shared academic resources (labs, seminar rooms, projectors, etc.) across multiple campuses.

## Features

### Multi-Campus Support
- Three campuses with independent booking policies:
  - **Johannesburg** – max 4 h, 08:00–18:00
  - **Cape Town** – max 2 h, 09:00–17:00, **no weekend bookings**
  - **Durban** – max 3 h, 07:00–19:00
- Campus data stored in dictionaries / SQLite tables
- Active campus clearly displayed in the GUI status bar

### Role-Based Access Control (OOP)
| Role | Capabilities |
|------|--------------|
| **Lecturer** | Register, log in, select campus, view resources, create bookings, view/cancel own bookings, check availability |
| **Campus Administrator** | Log in (campus-locked), add/update/remove resources, view all campus bookings, generate campus report |
| **System Operator** | Full access, view bookings across all campuses, generate comparative cross-campus reports |

Implemented with:
- Abstract base class `User`
- Inheritance: `Lecturer`, `CampusAdministrator`, `SystemOperator`
- Encapsulation (private attributes + properties)
- Factory function `create_user_from_dict`

### Booking Rules (Separated for Extensibility)
- Abstract `BookingPolicy` + concrete policy classes per campus
- Policy registry makes adding a new campus trivial
- Rules applied automatically on every booking attempt
- Overlap detection prevents double-bookings

### Data Persistence
- SQLite database (`campus_booking.db`) created automatically
- Tables: `users`, `campuses`, `resources`, `bookings`
- All data survives application restarts

### GUI (Tkinter)
- Clean, tabbed interface
- Login / Registration screens
- Role-specific dashboards
- Real-time resource availability checker
- Input validation and clear error messages

## Requirements

- Python 3.8+
- Standard library only (tkinter, sqlite3, datetime, abc, typing)

No external packages required.

## How to Run

```bash
cd SmartCampusBooking
python main.py
```

## Demo Accounts

| Username    | Password     | Role                |
|-------------|--------------|---------------------|
| sysop       | password123  | System Operator     |
| admin_jhb   | password123  | Johannesburg Admin  |
| admin_cpt   | password123  | Cape Town Admin     |
| admin_dbn   | password123  | Durban Admin        |
| lecturer1   | password123  | Lecturer            |
| lecturer2   | password123  | Lecturer            |

New lecturers can register via the GUI.

## Project Structure

```
SmartCampusBooking/
├── main.py                 # Application entry point
├── campus_booking.db       # SQLite database (created on first run)
├── database/
│   ├── __init__.py
│   └── db_manager.py       # All SQLite operations
├── models/
│   ├── __init__.py
│   ├── user.py             # User hierarchy (OOP)
│   └── booking_rules.py    # Campus-specific policies
├── gui/
│   ├── __init__.py
│   └── app.py              # Full Tkinter GUI
└── README.md
```

## Design Notes

- **Booking rules are completely separated** from core booking logic → new campuses or rule changes require minimal code changes.
- Duplicate resource names per campus are rejected at the database level (UNIQUE constraint).
- Soft-delete is used for resources that still have active bookings.
- Past/ongoing bookings cannot be cancelled.
- All critical paths include try/except and user-friendly messages.

## Author

Junior Software Developer – PROGRAMMING 512
Richfield Graduate Institution
