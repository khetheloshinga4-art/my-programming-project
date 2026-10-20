"""
Main Tkinter GUI for the Smart Campus Resource Booking System.
Provides login, registration, campus selection, and role-specific dashboards.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from models.user import User, Lecturer, CampusAdministrator, SystemOperator, create_user_from_dict
from models.booking_rules import get_policy_for_campus


class SmartCampusApp(tk.Tk):
    """Root application window."""

    def __init__(self):
        super().__init__()
        self.title("Smart Campus Resource Booking System – Richfield")
        self.geometry("1000x700")
        self.minsize(900, 600)
        self.configure(bg="#f0f4f8")

        # Centre the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"1000x700+{x}+{y}")

        self.db = DatabaseManager()
        self.current_user: Optional[User] = None
        self.current_campus: Optional[Dict] = None

        # Style
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._configure_styles()

        # Container for frames
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.frames: Dict[str, tk.Frame] = {}
        self._show_frame("LoginFrame")

    def _configure_styles(self):
        self.style.configure("TFrame", background="#f0f4f8")
        self.style.configure("TLabel", background="#f0f4f8", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#1a365d")
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 12, "bold"), foreground="#2c5282")
        self.style.configure("TButton", font=("Segoe UI", 10), padding=6)
        self.style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
        self.style.configure("Treeview", font=("Segoe UI", 9), rowheight=24)
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _show_frame(self, name: str, **kwargs):
        """Destroy current content and show the requested frame."""
        for widget in self.container.winfo_children():
            widget.destroy()

        if name == "LoginFrame":
            frame = LoginFrame(self.container, self)
        elif name == "RegisterFrame":
            frame = RegisterFrame(self.container, self)
        elif name == "CampusSelectFrame":
            frame = CampusSelectFrame(self.container, self)
        elif name == "LecturerDashboard":
            frame = LecturerDashboard(self.container, self)
        elif name == "AdminDashboard":
            frame = AdminDashboard(self.container, self)
        elif name == "OperatorDashboard":
            frame = OperatorDashboard(self.container, self)
        else:
            frame = LoginFrame(self.container, self)

        frame.pack(fill="both", expand=True)
        self.frames[name] = frame

    def login_success(self, user_data: Dict):
        self.current_user = create_user_from_dict(user_data)
        # Campus admins are locked to their campus
        if isinstance(self.current_user, CampusAdministrator):
            self.current_campus = self.db.get_campus_by_id(self.current_user.campus_id)
            self._show_frame("AdminDashboard")
        else:
            self._show_frame("CampusSelectFrame")

    def logout(self):
        self.current_user = None
        self.current_campus = None
        self._show_frame("LoginFrame")

    def select_campus(self, campus: Dict):
        self.current_campus = campus
        if isinstance(self.current_user, Lecturer):
            self._show_frame("LecturerDashboard")
        elif isinstance(self.current_user, SystemOperator):
            self._show_frame("OperatorDashboard")
        else:
            self._show_frame("AdminDashboard")


# ---------------------------------------------------------------------------
# Login / Register Frames
# ---------------------------------------------------------------------------
class LoginFrame(ttk.Frame):
    def __init__(self, parent, app: SmartCampusApp):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        # Header
        header = ttk.Frame(self)
        header.pack(pady=(40, 20))
        ttk.Label(header, text="Smart Campus Resource Booking System",
                  style="Header.TLabel").pack()
        ttk.Label(header, text="Richfield Graduate Institution",
                  style="SubHeader.TLabel").pack(pady=5)

        # Form card
        card = ttk.LabelFrame(self, text="  Login  ", padding=20)
        card.pack(pady=10)

        ttk.Label(card, text="Username:").grid(row=0, column=0, sticky="e", padx=5, pady=8)
        self.username_var = tk.StringVar()
        ttk.Entry(card, textvariable=self.username_var, width=30).grid(row=0, column=1, padx=5, pady=8)

        ttk.Label(card, text="Password:").grid(row=1, column=0, sticky="e", padx=5, pady=8)
        self.password_var = tk.StringVar()
        ttk.Entry(card, textvariable=self.password_var, show="•", width=30).grid(row=1, column=1, padx=5, pady=8)

        btn_frame = ttk.Frame(card)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="Login", command=self._login, style="Accent.TButton").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Register as Lecturer", command=lambda: self.app._show_frame("RegisterFrame")).pack(side="left", padx=5)

        # Demo credentials hint
        hint = ttk.LabelFrame(self, text="  Demo Accounts (password: password123)  ", padding=10)
        hint.pack(pady=20, padx=40, fill="x")
        demo_text = (
            "• sysop – System Operator (full access)\n"
            "• admin_jhb / admin_cpt / admin_dbn – Campus Administrators\n"
            "• lecturer1 / lecturer2 – Lecturers"
        )
        ttk.Label(hint, text=demo_text, justify="left").pack(anchor="w")

    def _login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        if not username or not password:
            messagebox.showwarning("Input Required", "Please enter both username and password.")
            return
        user = self.app.db.authenticate(username, password)
        if user:
            self.app.login_success(user)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")


class RegisterFrame(ttk.Frame):
    def __init__(self, parent, app: SmartCampusApp):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        ttk.Label(self, text="Lecturer Registration", style="Header.TLabel").pack(pady=(30, 15))

        card = ttk.LabelFrame(self, text="  New Lecturer Account  ", padding=20)
        card.pack()

        fields = [
            ("Username:", "username"),
            ("Password:", "password"),
            ("Full Name:", "full_name"),
            ("Email:", "email"),
        ]
        self.vars = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(card, text=label).grid(row=i, column=0, sticky="e", padx=5, pady=6)
            var = tk.StringVar()
            show = "•" if key == "password" else ""
            ttk.Entry(card, textvariable=var, width=32, show=show).grid(row=i, column=1, padx=5, pady=6)
            self.vars[key] = var

        btn_frame = ttk.Frame(card)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=12)
        ttk.Button(btn_frame, text="Register", command=self._register).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Back to Login", command=lambda: self.app._show_frame("LoginFrame")).pack(side="left", padx=5)

    def _register(self):
        username = self.vars["username"].get().strip()
        password = self.vars["password"].get()
        full_name = self.vars["full_name"].get().strip()
        email = self.vars["email"].get().strip()

        if not all([username, password, full_name]):
            messagebox.showwarning("Input Required", "Username, password and full name are required.")
            return
        if len(password) < 6:
            messagebox.showwarning("Weak Password", "Password must be at least 6 characters.")
            return

        success, msg = self.app.db.register_user(username, password, full_name, "lecturer", email=email)
        if success:
            messagebox.showinfo("Success", msg)
            self.app._show_frame("LoginFrame")
        else:
            messagebox.showerror("Registration Failed", msg)


# ---------------------------------------------------------------------------
# Campus Selection
# ---------------------------------------------------------------------------
class CampusSelectFrame(ttk.Frame):
    def __init__(self, parent, app: SmartCampusApp):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=20, pady=15)
        ttk.Label(top, text=f"Welcome, {self.app.current_user.full_name}",
                  style="Header.TLabel").pack(side="left")
        ttk.Button(top, text="Logout", command=self.app.logout).pack(side="right")

        ttk.Label(self, text="Select a Campus to work with",
                  style="SubHeader.TLabel").pack(pady=10)

        campuses = self.app.db.get_all_campuses()
        for campus in campuses:
            policy = get_policy_for_campus(campus)
            frame = ttk.LabelFrame(self, text=f"  {campus['name']}  ", padding=12)
            frame.pack(fill="x", padx=40, pady=8)

            ttk.Label(frame, text=f"Location: {campus['location']}").pack(anchor="w")
            ttk.Label(frame, text=f"Policy: {policy.get_policy_description()}").pack(anchor="w")
            ttk.Label(frame, text=campus.get("description", ""), wraplength=700).pack(anchor="w", pady=4)
            ttk.Button(frame, text="Select this Campus",
                       command=lambda c=campus: self.app.select_campus(c)).pack(anchor="e", pady=4)


# ---------------------------------------------------------------------------
# Shared helper widgets
# ---------------------------------------------------------------------------
def create_status_bar(parent, app: SmartCampusApp) -> ttk.Frame:
    bar = ttk.Frame(parent)
    bar.pack(fill="x", side="bottom", padx=5, pady=3)
    user_text = f"User: {app.current_user.full_name} ({app.current_user.role})"
    campus_text = f" | Campus: {app.current_campus['name']}" if app.current_campus else ""
    ttk.Label(bar, text=user_text + campus_text, font=("Segoe UI", 9)).pack(side="left")
    if app.current_campus:
        policy = get_policy_for_campus(app.current_campus)
        ttk.Label(bar, text=f"Policy: {policy.get_policy_description()}",
                  font=("Segoe UI", 9, "italic"), foreground="#2b6cb0").pack(side="right")
    return bar


# ---------------------------------------------------------------------------
# Lecturer Dashboard
# ---------------------------------------------------------------------------
class LecturerDashboard(ttk.Frame):
    def __init__(self, parent, app: SmartCampusApp):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        # Top bar
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)
        ttk.Label(top, text="Lecturer Dashboard", style="Header.TLabel").pack(side="left")
        ttk.Button(top, text="Change Campus",
                   command=lambda: self.app._show_frame("CampusSelectFrame")).pack(side="right", padx=4)
        ttk.Button(top, text="Logout", command=self.app.logout).pack(side="right", padx=4)

        # Notebook
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Tab 1: Book Resource
        book_tab = ttk.Frame(notebook)
        notebook.add(book_tab, text="  Book Resource  ")
        self._build_book_tab(book_tab)

        # Tab 2: My Bookings
        my_tab = ttk.Frame(notebook)
        notebook.add(my_tab, text="  My Bookings  ")
        self._build_my_bookings_tab(my_tab)

        # Tab 3: Availability
        avail_tab = ttk.Frame(notebook)
        notebook.add(avail_tab, text="  Resource Availability  ")
        self._build_availability_tab(avail_tab)

        create_status_bar(self, self.app)

    def _build_book_tab(self, parent):
        left = ttk.Frame(parent)
        left.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        ttk.Label(left, text="Available Resources", style="SubHeader.TLabel").pack(anchor="w")

        cols = ("ID", "Name", "Type", "Capacity")
        self.res_tree = ttk.Treeview(left, columns=cols, show="headings", height=12)
        for c in cols:
            self.res_tree.heading(c, text=c)
            self.res_tree.column(c, width=100 if c != "Name" else 180)
        self.res_tree.pack(fill="both", expand=True, pady=5)
        self.res_tree.bind("<<TreeviewSelect>>", self._on_resource_select)

        self._refresh_resources()

        # Booking form
        form = ttk.LabelFrame(parent, text="  Create Booking  ", padding=12)
        form.pack(side="right", fill="y", padx=10, pady=10)

        ttk.Label(form, text="Selected Resource:").grid(row=0, column=0, sticky="w", pady=4)
        self.sel_res_var = tk.StringVar(value="(none)")
        ttk.Label(form, textvariable=self.sel_res_var, wraplength=200).grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(form, text="Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="w", pady=4)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(form, textvariable=self.date_var, width=18).grid(row=1, column=1, pady=4)

        ttk.Label(form, text="Start Time (HH:MM):").grid(row=2, column=0, sticky="w", pady=4)
        self.time_var = tk.StringVar(value="09:00")
        ttk.Entry(form, textvariable=self.time_var, width=18).grid(row=2, column=1, pady=4)

        ttk.Label(form, text="Duration (hours):").grid(row=3, column=0, sticky="w", pady=4)
        self.dur_var = tk.StringVar(value="1.0")
        ttk.Entry(form, textvariable=self.dur_var, width=18).grid(row=3, column=1, pady=4)

        ttk.Label(form, text="Notes (optional):").grid(row=4, column=0, sticky="w", pady=4)
        self.notes_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.notes_var, width=18).grid(row=4, column=1, pady=4)

        ttk.Button(form, text="Submit Booking", command=self._submit_booking,
                   style="Accent.TButton").grid(row=5, column=0, columnspan=2, pady=12)

        policy = get_policy_for_campus(self.app.current_campus)
        ttk.Label(form, text=f"Current policy:\n{policy.get_policy_description()}",
                  wraplength=220, foreground="#2b6cb0").grid(row=6, column=0, columnspan=2, pady=8)

        self.selected_resource_id = None

    def _refresh_resources(self):
        for item in self.res_tree.get_children():
            self.res_tree.delete(item)
        resources = self.app.db.get_resources_by_campus(self.app.current_campus["campus_id"])
        for r in resources:
            self.res_tree.insert("", "end", values=(
                r["resource_id"], r["name"], r["resource_type"], r["capacity"]
            ))

    def _on_resource_select(self, event):
        sel = self.res_tree.selection()
        if sel:
            vals = self.res_tree.item(sel[0], "values")
            self.selected_resource_id = int(vals[0])
            self.sel_res_var.set(f"{vals[1]} ({vals[2]})")

    def _submit_booking(self):
        if not self.selected_resource_id:
            messagebox.showwarning("No Resource", "Please select a resource first.")
            return

        date_str = self.date_var.get().strip()
        time_str = self.time_var.get().strip()
        try:
            duration = float(self.dur_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Input", "Duration must be a number (e.g. 1.5).")
            return

        # Validate date format
        try:
            booking_dt = datetime.strptime(date_str, "%Y-%m-%d")
            if booking_dt.date() < datetime.now().date():
                messagebox.showerror("Invalid Date", "Cannot book in the past.")
                return
        except ValueError:
            messagebox.showerror("Invalid Date", "Date must be YYYY-MM-DD.")
            return

        # Validate time format
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            messagebox.showerror("Invalid Time", "Time must be HH:MM (24-hour).")
            return

        # Apply campus-specific booking rules
        policy = get_policy_for_campus(self.app.current_campus)
        valid, msg = policy.validate_booking(duration, time_str, date_str)
        if not valid:
            messagebox.showerror("Policy Violation", msg)
            return

        success, result_msg = self.app.db.create_booking(
            resource_id=self.selected_resource_id,
            user_id=self.app.current_user.user_id,
            campus_id=self.app.current_campus["campus_id"],
            booking_date=date_str,
            start_time=time_str,
            duration_hours=duration,
            notes=self.notes_var.get().strip()
        )
        if success:
            messagebox.showinfo("Success", result_msg)
            self._refresh_my_bookings()
        else:
            messagebox.showerror("Booking Failed", result_msg)

    def _build_my_bookings_tab(self, parent):
        ttk.Label(parent, text="Your Booking History", style="SubHeader.TLabel").pack(anchor="w", padx=10, pady=8)

        cols = ("ID", "Resource", "Campus", "Date", "Start", "Duration", "End", "Status")
        self.my_tree = ttk.Treeview(parent, columns=cols, show="headings", height=15)
        widths = [50, 150, 140, 100, 60, 70, 60, 80]
        for c, w in zip(cols, widths):
            self.my_tree.heading(c, text=c)
            self.my_tree.column(c, width=w)
        self.my_tree.pack(fill="both", expand=True, padx=10, pady=5)

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="Refresh", command=self._refresh_my_bookings).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel Selected Booking", command=self._cancel_booking).pack(side="left", padx=5)

        self._refresh_my_bookings()

    def _refresh_my_bookings(self):
        for item in self.my_tree.get_children():
            self.my_tree.delete(item)
        bookings = self.app.db.get_user_bookings(self.app.current_user.user_id)
        for b in bookings:
            self.my_tree.insert("", "end", values=(
                b["booking_id"], b["resource_name"], b["campus_name"],
                b["booking_date"], b["start_time"], f"{b['duration_hours']}h",
                b["end_time"], b["status"]
            ))

    def _cancel_booking(self):
        sel = self.my_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a booking to cancel.")
            return
        booking_id = int(self.my_tree.item(sel[0], "values")[0])
        if not messagebox.askyesno("Confirm", "Cancel this booking?"):
            return
        success, msg = self.app.db.cancel_booking(booking_id, self.app.current_user.user_id)
        if success:
            messagebox.showinfo("Success", msg)
            self._refresh_my_bookings()
        else:
            messagebox.showerror("Cannot Cancel", msg)

    def _build_availability_tab(self, parent):
        top = ttk.Frame(parent)
        top.pack(fill="x", padx=10, pady=8)
        ttk.Label(top, text="Check availability for date:").pack(side="left")
        self.avail_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(top, textvariable=self.avail_date_var, width=14).pack(side="left", padx=6)
        ttk.Button(top, text="Check", command=self._check_availability).pack(side="left")

        cols = ("Resource", "Type", "Existing Bookings")
        self.avail_tree = ttk.Treeview(parent, columns=cols, show="headings", height=16)
        for c in cols:
            self.avail_tree.heading(c, text=c)
            self.avail_tree.column(c, width=200 if c != "Existing Bookings" else 350)
        self.avail_tree.pack(fill="both", expand=True, padx=10, pady=5)

    def _check_availability(self):
        date_str = self.avail_date_var.get().strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Use YYYY-MM-DD format.")
            return

        for item in self.avail_tree.get_children():
            self.avail_tree.delete(item)

        resources = self.app.db.get_resources_by_campus(self.app.current_campus["campus_id"])
        for r in resources:
            bookings = self.app.db.get_bookings_for_resource_on_date(r["resource_id"], date_str)
            if bookings:
                slots = ", ".join(f"{b['start_time']}-{b['end_time']}" for b in bookings)
            else:
                slots = "Fully available"
            self.avail_tree.insert("", "end", values=(r["name"], r["resource_type"], slots))


# ---------------------------------------------------------------------------
# Campus Administrator Dashboard
# ---------------------------------------------------------------------------
class AdminDashboard(ttk.Frame):
    def __init__(self, parent, app: SmartCampusApp):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)
        ttk.Label(top, text="Campus Administrator Dashboard", style="Header.TLabel").pack(side="left")
        ttk.Button(top, text="Logout", command=self.app.logout).pack(side="right")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=5)

        res_tab = ttk.Frame(notebook)
        notebook.add(res_tab, text="  Manage Resources  ")
        self._build_resource_tab(res_tab)

        book_tab = ttk.Frame(notebook)
        notebook.add(book_tab, text="  Campus Bookings  ")
        self._build_bookings_tab(book_tab)

        report_tab = ttk.Frame(notebook)
        notebook.add(report_tab, text="  Campus Report  ")
        self._build_report_tab(report_tab)

        create_status_bar(self, self.app)

    def _build_resource_tab(self, parent):
        # Resource list
        cols = ("ID", "Name", "Type", "Capacity", "Active", "Description")
        self.res_tree = ttk.Treeview(parent, columns=cols, show="headings", height=10)
        for c in cols:
            self.res_tree.heading(c, text=c)
            self.res_tree.column(c, width=90 if c != "Description" else 200)
        self.res_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.res_tree.bind("<<TreeviewSelect>>", self._on_res_select)

        # Form
        form = ttk.LabelFrame(parent, text="  Add / Update Resource  ", padding=10)
        form.pack(fill="x", padx=10, pady=8)

        self.r_name = tk.StringVar()
        self.r_type = tk.StringVar()
        self.r_cap = tk.StringVar(value="1")
        self.r_desc = tk.StringVar()
        self.r_active = tk.IntVar(value=1)
        self.editing_id = None

        row1 = ttk.Frame(form)
        row1.pack(fill="x", pady=3)
        ttk.Label(row1, text="Name:").pack(side="left")
        ttk.Entry(row1, textvariable=self.r_name, width=25).pack(side="left", padx=5)
        ttk.Label(row1, text="Type:").pack(side="left", padx=(10, 0))
        type_combo = ttk.Combobox(row1, textvariable=self.r_type, width=20,
                                  values=["Computer Laboratory", "Seminar Room", "Projector",
                                          "Presentation Equipment", "Other"])
        type_combo.pack(side="left", padx=5)

        row2 = ttk.Frame(form)
        row2.pack(fill="x", pady=3)
        ttk.Label(row2, text="Capacity:").pack(side="left")
        ttk.Entry(row2, textvariable=self.r_cap, width=8).pack(side="left", padx=5)
        ttk.Label(row2, text="Description:").pack(side="left", padx=(10, 0))
        ttk.Entry(row2, textvariable=self.r_desc, width=40).pack(side="left", padx=5)
        ttk.Checkbutton(row2, text="Active", variable=self.r_active).pack(side="left", padx=10)

        btn_row = ttk.Frame(form)
        btn_row.pack(pady=6)
        ttk.Button(btn_row, text="Add New", command=self._add_resource).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Update Selected", command=self._update_resource).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Remove Selected", command=self._remove_resource).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Clear Form", command=self._clear_res_form).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Refresh", command=self._refresh_resources).pack(side="left", padx=4)

        self._refresh_resources()

    def _refresh_resources(self):
        for item in self.res_tree.get_children():
            self.res_tree.delete(item)
        resources = self.app.db.get_resources_by_campus(
            self.app.current_campus["campus_id"], active_only=False
        )
        for r in resources:
            self.res_tree.insert("", "end", values=(
                r["resource_id"], r["name"], r["resource_type"],
                r["capacity"], "Yes" if r["is_active"] else "No",
                r.get("description", "")
            ))

    def _on_res_select(self, event):
        sel = self.res_tree.selection()
        if sel:
            vals = self.res_tree.item(sel[0], "values")
            self.editing_id = int(vals[0])
            self.r_name.set(vals[1])
            self.r_type.set(vals[2])
            self.r_cap.set(vals[3])
            self.r_active.set(1 if vals[4] == "Yes" else 0)
            self.r_desc.set(vals[5])

    def _clear_res_form(self):
        self.editing_id = None
        self.r_name.set("")
        self.r_type.set("")
        self.r_cap.set("1")
        self.r_desc.set("")
        self.r_active.set(1)

    def _add_resource(self):
        name = self.r_name.get().strip()
        rtype = self.r_type.get().strip()
        if not name or not rtype:
            messagebox.showwarning("Input Required", "Name and Type are required.")
            return
        try:
            capacity = int(self.r_cap.get())
        except ValueError:
            messagebox.showerror("Invalid", "Capacity must be an integer.")
            return
        success, msg = self.app.db.add_resource(
            self.app.current_campus["campus_id"], name, rtype, capacity, self.r_desc.get()
        )
        if success:
            messagebox.showinfo("Success", msg)
            self._clear_res_form()
            self._refresh_resources()
        else:
            messagebox.showerror("Failed", msg)

    def _update_resource(self):
        if not self.editing_id:
            messagebox.showwarning("No Selection", "Select a resource to update.")
            return
        name = self.r_name.get().strip()
        rtype = self.r_type.get().strip()
        try:
            capacity = int(self.r_cap.get())
        except ValueError:
            messagebox.showerror("Invalid", "Capacity must be an integer.")
            return
        success, msg = self.app.db.update_resource(
            self.editing_id, name, rtype, capacity, self.r_desc.get(), self.r_active.get()
        )
        if success:
            messagebox.showinfo("Success", msg)
            self._clear_res_form()
            self._refresh_resources()
        else:
            messagebox.showerror("Failed", msg)

    def _remove_resource(self):
        if not self.editing_id:
            messagebox.showwarning("No Selection", "Select a resource to remove.")
            return
        if not messagebox.askyesno("Confirm", "Remove / deactivate this resource?"):
            return
        success, msg = self.app.db.delete_resource(self.editing_id)
        if success:
            messagebox.showinfo("Success", msg)
            self._clear_res_form()
            self._refresh_resources()
        else:
            messagebox.showerror("Failed", msg)

    def _build_bookings_tab(self, parent):
        cols = ("ID", "Resource", "Lecturer", "Date", "Start", "Duration", "End", "Status")
        self.book_tree = ttk.Treeview(parent, columns=cols, show="headings", height=18)
        widths = [50, 140, 140, 100, 60, 70, 60, 80]
        for c, w in zip(cols, widths):
            self.book_tree.heading(c, text=c)
            self.book_tree.column(c, width=w)
        self.book_tree.pack(fill="both", expand=True, padx=10, pady=5)

        ttk.Button(parent, text="Refresh Bookings", command=self._refresh_bookings).pack(pady=6)
        self._refresh_bookings()

    def _refresh_bookings(self):
        for item in self.book_tree.get_children():
            self.book_tree.delete(item)
        bookings = self.app.db.get_campus_bookings(self.app.current_campus["campus_id"])
        for b in bookings:
            self.book_tree.insert("", "end", values=(
                b["booking_id"], b["resource_name"], b["lecturer_name"],
                b["booking_date"], b["start_time"], f"{b['duration_hours']}h",
                b["end_time"], b["status"]
            ))

    def _build_report_tab(self, parent):
        self.report_text = tk.Text(parent, wrap="word", font=("Consolas", 10), height=25)
        self.report_text.pack(fill="both", expand=True, padx=10, pady=10)
        ttk.Button(parent, text="Generate Campus Report", command=self._generate_report).pack(pady=5)
        self._generate_report()

    def _generate_report(self):
        report = self.app.db.get_campus_report(self.app.current_campus["campus_id"])
        campus = self.app.current_campus
        policy = get_policy_for_campus(campus)

        lines = [
            f"{'=' * 60}",
            f"  CAMPUS REPORT – {campus['name']}",
            f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"{'=' * 60}",
            f"",
            f"Location: {campus['location']}",
            f"Booking Policy: {policy.get_policy_description()}",
            f"",
            f"Total Bookings (all time): {report['total_bookings']}",
            f"Active Bookings:           {report['active_bookings']}",
            f"Average Duration:          {report['avg_duration']} hours",
            f"",
            f"Top Resources by Usage:",
        ]
        if report["top_resources"]:
            for i, r in enumerate(report["top_resources"], 1):
                lines.append(f"  {i}. {r['name']} – {r['booking_count']} booking(s)")
        else:
            lines.append("  (no bookings yet)")
        lines.append("")
        lines.append("=" * 60)

        self.report_text.delete("1.0", "end")
        self.report_text.insert("1.0", "\n".join(lines))


# ---------------------------------------------------------------------------
# System Operator Dashboard
# ---------------------------------------------------------------------------
class OperatorDashboard(ttk.Frame):
    def __init__(self, parent, app: SmartCampusApp):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)
        ttk.Label(top, text="System Operator Dashboard", style="Header.TLabel").pack(side="left")
        ttk.Button(top, text="Change Campus View",
                   command=lambda: self.app._show_frame("CampusSelectFrame")).pack(side="right", padx=4)
        ttk.Button(top, text="Logout", command=self.app.logout).pack(side="right", padx=4)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=5)

        all_book_tab = ttk.Frame(notebook)
        notebook.add(all_book_tab, text="  All Bookings  ")
        self._build_all_bookings(all_book_tab)

        report_tab = ttk.Frame(notebook)
        notebook.add(report_tab, text="  Cross-Campus Reports  ")
        self._build_cross_report(report_tab)

        res_tab = ttk.Frame(notebook)
        notebook.add(res_tab, text="  Resources (Current Campus)  ")
        self._build_resources_view(res_tab)

        create_status_bar(self, self.app)

    def _build_all_bookings(self, parent):
        cols = ("ID", "Resource", "Campus", "Lecturer", "Date", "Start", "Duration", "Status")
        self.all_tree = ttk.Treeview(parent, columns=cols, show="headings", height=18)
        widths = [50, 130, 140, 130, 100, 60, 70, 80]
        for c, w in zip(cols, widths):
            self.all_tree.heading(c, text=c)
            self.all_tree.column(c, width=w)
        self.all_tree.pack(fill="both", expand=True, padx=10, pady=5)
        ttk.Button(parent, text="Refresh", command=self._refresh_all_bookings).pack(pady=5)
        self._refresh_all_bookings()

    def _refresh_all_bookings(self):
        for item in self.all_tree.get_children():
            self.all_tree.delete(item)
        bookings = self.app.db.get_all_bookings()
        for b in bookings:
            self.all_tree.insert("", "end", values=(
                b["booking_id"], b["resource_name"], b["campus_name"],
                b["lecturer_name"], b["booking_date"], b["start_time"],
                f"{b['duration_hours']}h", b["status"]
            ))

    def _build_cross_report(self, parent):
        self.cross_text = tk.Text(parent, wrap="word", font=("Consolas", 10), height=25)
        self.cross_text.pack(fill="both", expand=True, padx=10, pady=10)
        ttk.Button(parent, text="Generate Comparative Report",
                   command=self._generate_cross_report).pack(pady=5)
        self._generate_cross_report()

    def _generate_cross_report(self):
        reports = self.app.db.get_cross_campus_report()
        lines = [
            "=" * 70,
            "  CROSS-CAMPUS COMPARATIVE REPORT",
            f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 70,
            "",
        ]
        for r in reports:
            lines.extend([
                f"▶ {r['campus_name']}",
                f"   Policy hours : {r['booking_hours']}  |  Max duration: {r['max_booking_hours']}h",
                f"   Total bookings: {r['total_bookings']}  |  Active: {r['active_bookings']}",
                f"   Avg duration  : {r['avg_duration']} hours",
                "   Top resources :",
            ])
            if r["top_resources"]:
                for tr in r["top_resources"]:
                    lines.append(f"      • {tr['name']} ({tr['booking_count']})")
            else:
                lines.append("      (none)")
            lines.append("")

        lines.append("-" * 70)
        lines.append("Observations on policy impact:")
        # Simple comparative notes
        if reports:
            max_bookings = max(reports, key=lambda x: x["total_bookings"])
            min_avg = min(reports, key=lambda x: x["avg_duration"] or 999)
            lines.append(f"  • Highest booking volume: {max_bookings['campus_name']} "
                         f"({max_bookings['total_bookings']} bookings)")
            lines.append(f"  • Shortest average duration: {min_avg['campus_name']} "
                         f"({min_avg['avg_duration']}h) – reflects tighter max-duration policy")
        lines.append("=" * 70)

        self.cross_text.delete("1.0", "end")
        self.cross_text.insert("1.0", "\n".join(lines))

    def _build_resources_view(self, parent):
        cols = ("ID", "Name", "Type", "Capacity", "Active")
        self.op_res_tree = ttk.Treeview(parent, columns=cols, show="headings", height=16)
        for c in cols:
            self.op_res_tree.heading(c, text=c)
            self.op_res_tree.column(c, width=120)
        self.op_res_tree.pack(fill="both", expand=True, padx=10, pady=5)
        ttk.Button(parent, text="Refresh", command=self._refresh_op_resources).pack(pady=5)
        self._refresh_op_resources()

    def _refresh_op_resources(self):
        for item in self.op_res_tree.get_children():
            self.op_res_tree.delete(item)
        if not self.app.current_campus:
            return
        resources = self.app.db.get_resources_by_campus(
            self.app.current_campus["campus_id"], active_only=False
        )
        for r in resources:
            self.op_res_tree.insert("", "end", values=(
                r["resource_id"], r["name"], r["resource_type"],
                r["capacity"], "Yes" if r["is_active"] else "No"
            ))


# ---------------------------------------------------------------------------
# Entry point helper
# ---------------------------------------------------------------------------
def run_app():
    app = SmartCampusApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()
