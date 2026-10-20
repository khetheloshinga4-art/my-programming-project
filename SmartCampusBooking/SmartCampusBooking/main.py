#!/usr/bin/env python3
"""
Smart Campus Resource Booking System
Richfield Graduate Institution – PROGRAMMING 512 Assignment

Entry point for the application.
Run:  python main.py
"""

import sys
import os

# Ensure the project root is on the Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from gui.app import run_app


def main():
    print("=" * 60)
    print("  Smart Campus Resource Booking System")
    print("  Richfield Graduate Institution")
    print("=" * 60)
    print("Starting GUI... (close the window to exit)")
    print()
    print("Demo accounts (password for all: password123):")
    print("  sysop          – System Operator")
    print("  admin_jhb      – Johannesburg Campus Admin")
    print("  admin_cpt      – Cape Town Campus Admin")
    print("  admin_dbn      – Durban Campus Admin")
    print("  lecturer1      – Lecturer (Dr. Thabo Molefe)")
    print("  lecturer2      – Lecturer (Ms. Sarah Naidoo)")
    print("=" * 60)
    run_app()


if __name__ == "__main__":
    main()
