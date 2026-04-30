"""
WeAreCars - Car Rental Management System
A production-quality Tkinter desktop application for managing car rentals.
Fixed eye button + added right-side dashboard panel.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
from typing import Optional

# ─────────────────────────── CONSTANTS ───────────────────────────────────────
APP_TITLE = "WeAreCars"
DATA_FILE = "wearecars_bookings.json"
CREDENTIALS = {"username": "sta001", "password": "givemethekeys123"}
BASE_RATE_PER_DAY = 25
CAR_TYPE_SURCHARGE = {
    "City Car": 0,
    "Family Car": 50,
    "Sports Car": 75,
    "SUV": 65,
}
FUEL_TYPE_SURCHARGE = {
    "Petrol": 0,
    "Diesel": 0,
    "Hybrid": 30,
    "Electric": 50,
}
UNLIMITED_MILEAGE_PER_DAY = 10
BREAKDOWN_COVER_PER_DAY = 2

# Colour palette
C = {
    "bg_dark": "#0D1117",
    "bg_card": "#161B22",
    "bg_input": "#1C2128",
    "accent": "#E8B84B",
    "accent_hover": "#F5D06A",
    "accent_dark": "#C49A2E",
    "text_primary": "#F0F6FC",
    "text_secondary": "#8B949E",
    "text_muted": "#484F58",
    "danger": "#F85149",
    "success": "#3FB950",
    "border": "#30363D",
    "highlight": "#1F2937",
    "row_alt": "#1A1F26",
}

FONT_TITLE = ("Georgia", 28, "bold")
FONT_HEADING = ("Georgia", 16, "bold")
FONT_SUBHEAD = ("Helvetica", 12, "bold")
FONT_BODY = ("Helvetica", 11)
FONT_SMALL = ("Helvetica", 9)
FONT_MONO = ("Courier", 10)


# ─────────────────────────── DATA LAYER ──────────────────────────────────────
class BookingStore:
    """Handles JSON persistence for all bookings."""

    def __init__(self, filepath: str = DATA_FILE):
        self.filepath = filepath
        self.bookings: list = []
        self._next_id = 1
        self.load()

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    data = json.load(f)
                self.bookings = data.get("bookings", [])
                self._next_id = data.get("next_id", 1)
            except (json.JSONDecodeError, KeyError):
                self.bookings = []
                self._next_id = 1
        else:
            self.bookings = []
            self._next_id = 1

    def save(self):
        with open(self.filepath, "w") as f:
            json.dump({"bookings": self.bookings, "next_id": self._next_id}, f, indent=2)

    def add(self, booking: dict) -> dict:
        booking["id"] = self._next_id
        booking["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.bookings.append(booking)
        self._next_id += 1
        self.save()
        return booking

    def update(self, booking_id: int, updates: dict) -> bool:
        for i, b in enumerate(self.bookings):
            if b["id"] == booking_id:
                self.bookings[i].update(updates)
                self.bookings[i]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                self.save()
                return True
        return False

    def delete(self, booking_id: int) -> bool:
        original = len(self.bookings)
        self.bookings = [b for b in self.bookings if b["id"] != booking_id]
        if len(self.bookings) < original:
            self.save()
            return True
        return False

    def get_by_id(self, booking_id: int) -> Optional[dict]:
        for b in self.bookings:
            if b["id"] == booking_id:
                return b
        return None

    def total_revenue(self) -> float:
        return sum(b.get("total_cost", 0) for b in self.bookings)

    def most_popular_car_type(self) -> str:
        if not self.bookings:
            return "N/A"
        counts: dict = {}
        for b in self.bookings:
            ct = b.get("car_type", "Unknown")
            counts[ct] = counts.get(ct, 0) + 1
        return max(counts, key=counts.get)

    def most_popular_fuel_type(self) -> str:
        if not self.bookings:
            return "N/A"
        counts: dict = {}
        for b in self.bookings:
            ft = b.get("fuel_type", "Unknown")
            counts[ft] = counts.get(ft, 0) + 1
        return max(counts, key=counts.get)

    def average_booking_value(self) -> float:
        if not self.bookings:
            return 0.0
        return self.total_revenue() / len(self.bookings)

    def car_type_counts(self) -> dict:
        counts = {}
        for b in self.bookings:
            ct = b.get("car_type", "Unknown")
            counts[ct] = counts.get(ct, 0) + 1
        return counts

    def fuel_type_counts(self) -> dict:
        counts = {}
        for b in self.bookings:
            ft = b.get("fuel_type", "Unknown")
            counts[ft] = counts.get(ft, 0) + 1
        return counts


# ─────────────────────── PRICE CALCULATOR ────────────────────────────────────
def calculate_price(days: int, car_type: str, fuel_type: str,
                    unlimited_mileage: bool, breakdown_cover: bool) -> dict:
    """Return a full price breakdown dict."""
    base = days * BASE_RATE_PER_DAY
    car_surcharge = CAR_TYPE_SURCHARGE.get(car_type, 0)
    fuel_surcharge = FUEL_TYPE_SURCHARGE.get(fuel_type, 0)
    mileage_cost = days * UNLIMITED_MILEAGE_PER_DAY if unlimited_mileage else 0
    breakdown_cost = days * BREAKDOWN_COVER_PER_DAY if breakdown_cover else 0
    total = base + car_surcharge + fuel_surcharge + mileage_cost + breakdown_cost
    return {
        "base": base,
        "car_surcharge": car_surcharge,
        "fuel_surcharge": fuel_surcharge,
        "mileage_cost": mileage_cost,
        "breakdown_cost": breakdown_cost,
        "total": total,
    }


# ─────────────────────── VALIDATION ──────────────────────────────────────────
def validate_booking_fields(fields: dict) -> list:
    errors = []
    if not fields.get("first_name", "").strip():
        errors.append("First Name is required.")
    if not fields.get("surname", "").strip():
        errors.append("Surname is required.")
    if not fields.get("address", "").strip():
        errors.append("Address is required.")
    try:
        age = int(fields.get("age", 0))
        if age < 18:
            errors.append("Customer must be 18 or older.")
    except (ValueError, TypeError):
        errors.append("Age must be a valid number.")
    if fields.get("driving_license") != "Yes":
        errors.append("A valid driving licence is required to make a booking.")
    try:
        days = int(fields.get("days", 0))
        if not (1 <= days <= 28):
            errors.append("Number of days must be between 1 and 28.")
    except (ValueError, TypeError):
        errors.append("Number of days must be a valid number.")
    if fields.get("car_type") not in CAR_TYPE_SURCHARGE:
        errors.append("Please select a valid car type.")
    if fields.get("fuel_type") not in FUEL_TYPE_SURCHARGE:
        errors.append("Please select a valid fuel type.")
    return errors


# ─────────────────────── STYLE SETUP ─────────────────────────────────────────
def apply_dark_theme(root: tk.Tk):
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame", background=C["bg_dark"])
    style.configure("Card.TFrame", background=C["bg_card"])
    style.configure("TLabel", background=C["bg_dark"], foreground=C["text_primary"], font=FONT_BODY)
    style.configure("Card.TLabel", background=C["bg_card"], foreground=C["text_primary"], font=FONT_BODY)
    style.configure("Muted.TLabel", background=C["bg_dark"], foreground=C["text_secondary"], font=FONT_SMALL)
    style.configure("CardMuted.TLabel", background=C["bg_card"], foreground=C["text_secondary"], font=FONT_SMALL)
    style.configure("Accent.TLabel", background=C["bg_dark"], foreground=C["accent"], font=FONT_SUBHEAD)
    style.configure("CardAccent.TLabel", background=C["bg_card"], foreground=C["accent"], font=FONT_SUBHEAD)
    style.configure("Success.TLabel", background=C["bg_card"], foreground=C["success"], font=FONT_BODY)
    style.configure("Danger.TLabel", background=C["bg_card"], foreground=C["danger"], font=FONT_BODY)
    style.configure("Accent.TButton", background=C["accent"], foreground=C["bg_dark"],
                    font=FONT_SUBHEAD, relief="flat", padding=(14, 8))
    style.map("Accent.TButton",
              background=[("active", C["accent_hover"]), ("pressed", C["accent_dark"])])
    style.configure("Ghost.TButton", background=C["bg_card"], foreground=C["text_primary"],
                    font=FONT_BODY, relief="flat", padding=(12, 7))
    style.map("Ghost.TButton",
              background=[("active", C["highlight"])],
              foreground=[("active", C["accent"])])
    style.configure("Danger.TButton", background=C["danger"], foreground=C["text_primary"],
                    font=FONT_BODY, relief="flat", padding=(12, 7))
    style.map("Danger.TButton", background=[("active", "#FF6B6B")])
    style.configure("TEntry", fieldbackground=C["bg_input"], foreground=C["text_primary"],
                    insertcolor=C["accent"], bordercolor=C["border"], lightcolor=C["border"],
                    darkcolor=C["border"], font=FONT_BODY, padding=6)
    style.map("TEntry", bordercolor=[("focus", C["accent"])])
    style.configure("TCombobox", fieldbackground=C["bg_input"], foreground=C["text_primary"],
                    background=C["bg_input"], selectbackground=C["accent"],
                    selectforeground=C["bg_dark"], arrowcolor=C["accent"], font=FONT_BODY, padding=6)
    style.map("TCombobox", fieldbackground=[("readonly", C["bg_input"])])
    style.configure("TCheckbutton", background=C["bg_card"], foreground=C["text_primary"], font=FONT_BODY)
    style.map("TCheckbutton", background=[("active", C["bg_card"])])
    style.configure("Treeview", background=C["bg_card"], foreground=C["text_primary"],
                    fieldbackground=C["bg_card"], rowheight=30, font=FONT_BODY, borderwidth=0)
    style.configure("Treeview.Heading", background=C["bg_dark"], foreground=C["accent"],
                    font=FONT_SUBHEAD, relief="flat")
    style.map("Treeview",
              background=[("selected", C["accent"])],
              foreground=[("selected", C["bg_dark"])])
    style.configure("TScrollbar", background=C["bg_card"], troughcolor=C["bg_dark"],
                    arrowcolor=C["text_muted"], borderwidth=0)


# ─────────────────────── REUSABLE WIDGETS ────────────────────────────────────
class Separator(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=1, bg=C["border"], **kwargs)


class StatCard(tk.Frame):
    """Metric card for the dashboard."""
    def __init__(self, parent, icon: str, title: str, value: str, sub: str = ""):
        super().__init__(parent, bg=C["bg_card"], highlightthickness=1, highlightbackground=C["border"])
        inner = tk.Frame(self, bg=C["bg_card"], padx=20, pady=16)
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text=icon + " " + title, font=FONT_SMALL,
                 bg=C["bg_card"], fg=C["text_secondary"]).pack(anchor="w")
        self.val_lbl = tk.Label(inner, text=value, font=("Georgia", 22, "bold"),
                                bg=C["bg_card"], fg=C["accent"])
        self.val_lbl.pack(anchor="w", pady=(6, 0))
        if sub:
            tk.Label(inner, text=sub, font=FONT_SMALL, bg=C["bg_card"],
                     fg=C["text_muted"]).pack(anchor="w", pady=(3, 0))

    def update_value(self, value: str):
        self.val_lbl.config(text=value)


# ─────────────────────── SPLASH SCREEN ───────────────────────────────────────
class SplashScreen(tk.Toplevel):
    """3-second splash with progress bar."""
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(bg=C["bg_dark"])
        w, h = 500, 320
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        outer = tk.Frame(self, bg=C["accent"], padx=2, pady=2)
        outer.place(relx=0, rely=0, relwidth=1, relheight=1)
        inner = tk.Frame(outer, bg=C["bg_card"])
        inner.place(relx=0, rely=0, relwidth=1, relheight=1)
        tk.Frame(inner, bg=C["accent"], height=5).pack(fill="x")
        content = tk.Frame(inner, bg=C["bg_card"])
        content.pack(expand=True)
        tk.Label(content, text="🚗", font=("Helvetica", 48), bg=C["bg_card"],
                 fg=C["accent"]).pack(pady=(0, 10))
        tk.Label(content, text=APP_TITLE, font=("Georgia", 34, "bold"),
                 bg=C["bg_card"], fg=C["text_primary"]).pack()
        tk.Label(content, text="Car Rental Management System", font=("Helvetica", 12),
                 bg=C["bg_card"], fg=C["text_secondary"]).pack(pady=(4, 4))
        tk.Label(content, text="Loading — please wait…", font=FONT_SMALL,
                 bg=C["bg_card"], fg=C["text_muted"]).pack(pady=(14, 0))
        self._pval = 0
        self.bar = ttk.Progressbar(content, length=320, mode="determinate", maximum=100)
        self.bar.pack(pady=(8, 0))
        self._tick()

    def _tick(self):
        if self._pval < 100:
            self._pval += 2
            self.bar["value"] = self._pval
            self.after(55, self._tick)


# ─────────────────────── LOGIN SCREEN ────────────────────────────────────────
class LoginScreen(tk.Frame):
    """Username / password login panel with fixed eye button."""
    def __init__(self, parent, on_success):
        super().__init__(parent, bg=C["bg_dark"])
        self.on_success = on_success
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        card = tk.Frame(self, bg=C["bg_card"], highlightthickness=1, highlightbackground=C["border"])
        card.place(relx=0.5, rely=0.5, anchor="center")
        inner = tk.Frame(card, bg=C["bg_card"], padx=48, pady=40)
        inner.pack()
        tk.Frame(inner, bg=C["accent"], height=4).pack(fill="x", pady=(0, 28))
        tk.Label(inner, text="🚗 " + APP_TITLE, font=("Georgia", 26, "bold"),
                 bg=C["bg_card"], fg=C["text_primary"]).pack()
        tk.Label(inner, text="Staff Portal Login", font=("Helvetica", 11),
                 bg=C["bg_card"], fg=C["text_secondary"]).pack(pady=(4, 28))

        # Username
        tk.Label(inner, text="Username", font=FONT_SMALL, bg=C["bg_card"],
                 fg=C["text_secondary"]).pack(anchor="w")
        self.uvar = tk.StringVar()
        self.u_entry = ttk.Entry(inner, textvariable=self.uvar, font=FONT_BODY, width=34)
        self.u_entry.pack(fill="x", pady=(2, 16))

        # Password row with eye button and checkbox
        tk.Label(inner, text="Password", font=FONT_SMALL, bg=C["bg_card"],
                 fg=C["text_secondary"]).pack(anchor="w")
        self.pvar = tk.StringVar()
        pw_row = tk.Frame(inner, bg=C["bg_card"])
        pw_row.pack(fill="x", pady=(2, 6))
        self.p_entry = ttk.Entry(pw_row, textvariable=self.pvar, show="•", font=FONT_BODY)
        self.p_entry.pack(side="left", fill="x", expand=True)

        # Eye button toggles visibility and updates checkbox
        self.show_var = tk.BooleanVar(value=False)
        self.eye_btn = tk.Button(
            pw_row, text="👁", font=FONT_SMALL, bg=C["bg_input"], fg=C["text_secondary"],
            relief="flat", cursor="hand2", command=self._toggle_password
        )
        self.eye_btn.pack(side="left", padx=(4, 0))

        # Checkbox also toggles
        cb_row = tk.Frame(inner, bg=C["bg_card"])
        cb_row.pack(anchor="w", pady=(4, 20))
        self.show_cb = ttk.Checkbutton(
            cb_row, text=" Show password", variable=self.show_var,
            command=self._toggle_password, style="TCheckbutton"
        )
        self.show_cb.pack(side="left")

        self.err_var = tk.StringVar()
        tk.Label(inner, textvariable=self.err_var, font=FONT_SMALL, bg=C["bg_card"],
                 fg=C["danger"], wraplength=300).pack(pady=(0, 10))
        tk.Button(inner, text=" Sign In ", font=FONT_SUBHEAD, bg=C["accent"], fg=C["bg_dark"],
                  activebackground=C["accent_hover"], activeforeground=C["bg_dark"],
                  relief="flat", cursor="hand2", pady=10, command=self._login).pack(fill="x")
        self.u_entry.focus()
        self.u_entry.bind("<Return>", lambda _: self.p_entry.focus())
        self.p_entry.bind("<Return>", lambda _: self._login())

    def _toggle_password(self):
        """Toggle visibility and keep both eye button and checkbox in sync."""
        if self.show_var.get():
            self.p_entry.config(show="")
            self.eye_btn.config(text="🙈")
        else:
            self.p_entry.config(show="•")
            self.eye_btn.config(text="👁")

    def _login(self):
        u = self.uvar.get().strip()
        p = self.pvar.get()
        if u == CREDENTIALS["username"] and p == CREDENTIALS["password"]:
            self.err_var.set("")
            self.on_success()
        else:
            self.err_var.set("❌ Incorrect username or password. Please try again.")
            self.pvar.set("")
            self.p_entry.focus()


# ─────────────────────── DASHBOARD (with right sidebar) ──────────────────────
class Dashboard(tk.Frame):
    """Main dashboard with analytics cards, action buttons, recent bookings,
    and a right sidebar showing popular car types & fuel distribution."""
    def __init__(self, parent, store: BookingStore, nav):
        super().__init__(parent, bg=C["bg_dark"])
        self.store = store
        self.nav = nav
        self._stat_cards = {}
        self._build()
        self.refresh()

    def _build(self):
        # Top navbar
        navbar = tk.Frame(self, bg=C["bg_card"], padx=28, pady=14)
        navbar.pack(fill="x")
        tk.Label(navbar, text="🚗 " + APP_TITLE, font=("Georgia", 18, "bold"),
                 bg=C["bg_card"], fg=C["text_primary"]).pack(side="left")
        tk.Label(navbar, text="Dashboard", font=FONT_SMALL, bg=C["bg_card"],
                 fg=C["text_secondary"]).pack(side="left", padx=(16, 0))
        tk.Button(navbar, text="⏻ Log Out", font=FONT_SMALL, bg=C["bg_card"],
                  fg=C["text_secondary"], relief="flat", cursor="hand2",
                  command=self.nav["logout"]).pack(side="right")
        Separator(self).pack(fill="x")

        # Main container: left content + right sidebar
        main_container = tk.Frame(self, bg=C["bg_dark"])
        main_container.pack(fill="both", expand=True)

        # LEFT SIDE (main content)
        left_frame = tk.Frame(main_container, bg=C["bg_dark"])
        left_frame.pack(side="left", fill="both", expand=True)

        # Scrollable body for left side
        body_canvas = tk.Canvas(left_frame, bg=C["bg_dark"], highlightthickness=0)
        body_canvas.pack(fill="both", expand=True)
        body = tk.Frame(body_canvas, bg=C["bg_dark"])
        body_canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: body_canvas.configure(scrollregion=body_canvas.bbox("all")))
        pad = {"padx": 28, "pady": 0}

        # Welcome strip
        welcome = tk.Frame(body, bg=C["bg_dark"], **pad)
        welcome.pack(fill="x", pady=(24, 0))
        tk.Label(welcome, text="Good day! Here's an overview of WeAreCars.",
                 font=FONT_BODY, bg=C["bg_dark"], fg=C["text_secondary"]).pack(anchor="w")

        # Stat cards
        cards_frame = tk.Frame(body, bg=C["bg_dark"], **pad)
        cards_frame.pack(fill="x", pady=(16, 0))
        cards_frame.columnconfigure((0, 1, 2, 3), weight=1)
        stats = [
            ("bookings", "📋", "Total Bookings", "0"),
            ("revenue", "💷", "Total Revenue", "£0.00"),
            ("avg", "📊", "Avg Booking Value", "£0.00"),
            ("top_car", "🚗", "Most Popular Car", "N/A"),
        ]
        for col, (key, icon, title, val) in enumerate(stats):
            sc = StatCard(cards_frame, icon, title, val)
            sc.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 10, 0))
            self._stat_cards[key] = sc

        # Action buttons
        actions_label = tk.Frame(body, bg=C["bg_dark"], **pad)
        actions_label.pack(fill="x", pady=(28, 8))
        tk.Label(actions_label, text="ACTIONS", font=("Helvetica", 9, "bold"),
                 bg=C["bg_dark"], fg=C["text_muted"]).pack(anchor="w")
        btn_grid = tk.Frame(body, bg=C["bg_dark"], **pad)
        btn_grid.pack(fill="x", pady=(0, 24))
        actions = [
            ("➕ New Booking", C["accent"], C["bg_dark"], self.nav["add"]),
            ("📋 View Bookings", C["bg_card"], C["text_primary"], self.nav["view"]),
            ("✏️ Update Booking", C["bg_card"], C["text_primary"], self.nav["update"]),
            ("🗑 Delete Booking", C["danger"], C["text_primary"], self.nav["delete"]),
        ]
        for i, (label, bg, fg, cmd) in enumerate(actions):
            btn = tk.Button(btn_grid, text=label, font=FONT_SUBHEAD, bg=bg, fg=fg,
                            activebackground=C["accent_hover"], activeforeground=C["bg_dark"],
                            relief="flat", cursor="hand2", pady=14, padx=20, command=cmd)
            btn.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 10, 0))
            btn_grid.columnconfigure(i, weight=1)

        # Recent bookings mini-table
        recent_label = tk.Frame(body, bg=C["bg_dark"], **pad)
        recent_label.pack(fill="x", pady=(0, 8))
        tk.Label(recent_label, text="RECENT BOOKINGS", font=("Helvetica", 9, "bold"),
                 bg=C["bg_dark"], fg=C["text_muted"]).pack(anchor="w")
        tv_wrap = tk.Frame(body, bg=C["bg_dark"], **pad)
        tv_wrap.pack(fill="both", expand=True, pady=(0, 28))
        cols = ("id", "name", "car_type", "days", "total", "created")
        self.recent_tree = ttk.Treeview(tv_wrap, columns=cols, show="headings", height=6)
        hdr = [("id","ID",55), ("name","Customer",200), ("car_type","Car",110),
               ("days","Days",60), ("total","Total",100), ("created","Booked On",140)]
        for col, heading, width in hdr:
            self.recent_tree.heading(col, text=heading)
            self.recent_tree.column(col, width=width, anchor="center" if col != "name" else "w")
        vsb = ttk.Scrollbar(tv_wrap, orient="vertical", command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=vsb.set)
        self.recent_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="left", fill="y")

        # RIGHT SIDEBAR
        right_frame = tk.Frame(main_container, bg=C["bg_card"], width=280, relief="ridge", bd=1)
        right_frame.pack(side="right", fill="y", padx=(0, 0), pady=0)
        right_frame.pack_propagate(False)

        # Title for sidebar
        tk.Label(right_frame, text="📊 RENTAL INSIGHTS", font=FONT_SUBHEAD,
                 bg=C["bg_card"], fg=C["accent"]).pack(pady=(16, 8))

        # Car type popularity
        self.car_list_frame = tk.Frame(right_frame, bg=C["bg_card"])
        self.car_list_frame.pack(fill="x", padx=16, pady=8)
        tk.Label(self.car_list_frame, text="🚘 Most Popular Car Types",
                 font=FONT_SMALL, bg=C["bg_card"], fg=C["text_secondary"]).pack(anchor="w")
        self.car_listbox = tk.Listbox(self.car_list_frame, height=6, bg=C["bg_input"],
                                      fg=C["text_primary"], font=FONT_SMALL,
                                      selectbackground=C["accent"], selectforeground=C["bg_dark"],
                                      relief="flat", highlightthickness=0)
        self.car_listbox.pack(fill="x", pady=(4, 8))

        # Fuel type distribution
        self.fuel_frame = tk.Frame(right_frame, bg=C["bg_card"])
        self.fuel_frame.pack(fill="x", padx=16, pady=8)
        tk.Label(self.fuel_frame, text="⛽ Fuel Type Distribution",
                 font=FONT_SMALL, bg=C["bg_card"], fg=C["text_secondary"]).pack(anchor="w")
        self.fuel_listbox = tk.Listbox(self.fuel_frame, height=5, bg=C["bg_input"],
                                       fg=C["text_primary"], font=FONT_SMALL,
                                       selectbackground=C["accent"], selectforeground=C["bg_dark"],
                                       relief="flat", highlightthickness=0)
        self.fuel_listbox.pack(fill="x", pady=(4, 8))

        # Extra note
        tk.Label(right_frame, text="Double-click any row to edit",
                 font=FONT_SMALL, bg=C["bg_card"], fg=C["text_muted"]).pack(side="bottom", pady=12)

    def refresh(self):
        s = self.store
        self._stat_cards["bookings"].update_value(str(len(s.bookings)))
        self._stat_cards["revenue"].update_value(f"£{s.total_revenue():,.2f}")
        self._stat_cards["avg"].update_value(f"£{s.average_booking_value():,.2f}")
        self._stat_cards["top_car"].update_value(s.most_popular_car_type())

        # Update recent bookings
        for row in self.recent_tree.get_children():
            self.recent_tree.delete(row)
        recent = sorted(s.bookings, key=lambda b: b.get("id", 0), reverse=True)[:6]
        for b in recent:
            name = f"{b.get('first_name','')} {b.get('surname','')}"
            self.recent_tree.insert("", "end", values=(
                b.get("id", ""), name, b.get("car_type", ""),
                b.get("days", ""), f"£{b.get('total_cost', 0):.2f}", b.get("created_at", "")
            ))

        # Update right sidebar lists
        car_counts = s.car_type_counts()
        self.car_listbox.delete(0, tk.END)
        for car, cnt in sorted(car_counts.items(), key=lambda x: x[1], reverse=True):
            self.car_listbox.insert(tk.END, f"{car}: {cnt} booking{'s' if cnt != 1 else ''}")
        if not car_counts:
            self.car_listbox.insert(tk.END, "No bookings yet")

        fuel_counts = s.fuel_type_counts()
        self.fuel_listbox.delete(0, tk.END)
        for fuel, cnt in sorted(fuel_counts.items(), key=lambda x: x[1], reverse=True):
            self.fuel_listbox.insert(tk.END, f"{fuel}: {cnt} booking{'s' if cnt != 1 else ''}")
        if not fuel_counts:
            self.fuel_listbox.insert(tk.END, "No data")


# ─────────────────────── BOOKING FORM ────────────────────────────────────────
class BookingForm(tk.Frame):
    """Shared form for adding / editing a booking."""
    def __init__(self, parent, store: BookingStore, on_save, on_cancel, existing: Optional[dict] = None):
        super().__init__(parent, bg=C["bg_dark"])
        self.store = store
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.existing = existing
        self._build()
        if existing:
            self._populate(existing)

    # Helper layout methods
    def _section(self, title: str) -> tk.Frame:
        wrapper = tk.Frame(self.body, bg=C["bg_dark"], padx=28, pady=6)
        wrapper.pack(fill="x")
        tk.Label(wrapper, text=title, font=("Helvetica", 10, "bold"),
                 bg=C["bg_dark"], fg=C["accent"]).pack(anchor="w", pady=(0, 6))
        card = tk.Frame(wrapper, bg=C["bg_card"], highlightthickness=1,
                        highlightbackground=C["border"], padx=20, pady=16)
        card.pack(fill="x")
        return card

    @staticmethod
    def _lbl(parent, text: str):
        tk.Label(parent, text=text, font=FONT_SMALL, bg=C["bg_card"],
                 fg=C["text_secondary"]).pack(anchor="w")

    @staticmethod
    def _row(parent) -> tk.Frame:
        f = tk.Frame(parent, bg=C["bg_card"])
        f.pack(fill="x", pady=6)
        return f

    @staticmethod
    def _col(parent, padright=0) -> tk.Frame:
        f = tk.Frame(parent, bg=C["bg_card"])
        f.pack(side="left", fill="x", expand=True, padx=(0, padright) if padright else 0)
        return f

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=C["bg_card"], padx=28, pady=16)
        hdr.pack(fill="x")
        ttl = "✏️ Edit Booking" if self.existing else "➕ New Booking"
        tk.Label(hdr, text=ttl, font=FONT_HEADING, bg=C["bg_card"],
                 fg=C["text_primary"]).pack(side="left")
        tk.Button(hdr, text="✕ Cancel", font=FONT_SMALL, bg=C["bg_card"],
                  fg=C["text_secondary"], relief="flat", cursor="hand2",
                  command=self.on_cancel).pack(side="right")
        Separator(self).pack(fill="x")

        # Scrollable body
        canvas = tk.Canvas(self, bg=C["bg_dark"], highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self.body = tk.Frame(canvas, bg=C["bg_dark"])
        win = canvas.create_window((0, 0), window=self.body, anchor="nw")

        def _cfg(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win, width=e.width)
        canvas.bind("<Configure>", _cfg)
        self.body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._build_fields()

    def _build_fields(self):
        # Personal Details
        p = self._section("👤 Personal Details")
        row1 = self._row(p)
        c1 = self._col(row1, 10)
        self._lbl(c1, "First Name *")
        self.fn_var = tk.StringVar()
        ttk.Entry(c1, textvariable=self.fn_var, font=FONT_BODY).pack(fill="x")
        c2 = self._col(row1)
        self._lbl(c2, "Surname *")
        self.sn_var = tk.StringVar()
        ttk.Entry(c2, textvariable=self.sn_var, font=FONT_BODY).pack(fill="x")

        row2 = self._row(p)
        c3 = self._col(row2)
        self._lbl(c3, "Address *")
        self.addr_var = tk.StringVar()
        ttk.Entry(c3, textvariable=self.addr_var, font=FONT_BODY).pack(fill="x")

        row3 = self._row(p)
        c4 = self._col(row3, 10)
        self._lbl(c4, "Age * (must be 18+)")
        self.age_var = tk.StringVar()
        ttk.Entry(c4, textvariable=self.age_var, font=FONT_BODY).pack(fill="x")
        c5 = self._col(row3)
        self._lbl(c5, "Driving Licence *")
        self.lic_var = tk.StringVar(value="Yes")
        ttk.Combobox(c5, textvariable=self.lic_var, values=["Yes", "No"],
                     state="readonly", font=FONT_BODY).pack(fill="x")

        # Rental Details
        r = self._section("🚗 Rental Details")
        row4 = self._row(r)
        c6 = self._col(row4, 10)
        self._lbl(c6, "Number of Days * (1–28, £25/day)")
        self.days_var = tk.StringVar()
        self.days_var.trace_add("write", self._update_price)
        ttk.Entry(c6, textvariable=self.days_var, font=FONT_BODY).pack(fill="x")
        c7 = self._col(row4)
        self._lbl(c7, "Car Type *")
        self.car_var = tk.StringVar()
        self.car_var.trace_add("write", self._update_price)
        ttk.Combobox(c7, textvariable=self.car_var, values=list(CAR_TYPE_SURCHARGE.keys()),
                     state="readonly", font=FONT_BODY).pack(fill="x")
        tk.Label(r, text="Car Type pricing: City Car +£0 | Family Car +£50 | Sports Car +£75 | SUV +£65",
                 font=FONT_SMALL, bg=C["bg_card"], fg=C["text_muted"]).pack(anchor="w", pady=(2, 6))

        row5 = self._row(r)
        c8 = self._col(row5)
        self._lbl(c8, "Fuel Type *")
        self.fuel_var = tk.StringVar()
        self.fuel_var.trace_add("write", self._update_price)
        ttk.Combobox(c8, textvariable=self.fuel_var, values=list(FUEL_TYPE_SURCHARGE.keys()),
                     state="readonly", font=FONT_BODY).pack(fill="x")
        tk.Label(r, text="Fuel pricing: Petrol +£0 | Diesel +£0 | Hybrid +£30 | Electric +£50",
                 font=FONT_SMALL, bg=C["bg_card"], fg=C["text_muted"]).pack(anchor="w", pady=(2, 0))

        # Extras
        e = self._section("⭐ Optional Extras")
        ex_row = self._row(e)
        self.mile_var = tk.BooleanVar()
        self.mile_var.trace_add("write", self._update_price)
        ttk.Checkbutton(ex_row, text=" Unlimited Mileage (+£10/day)",
                        variable=self.mile_var, style="TCheckbutton").pack(side="left", padx=(0, 30))
        self.brkd_var = tk.BooleanVar()
        self.brkd_var.trace_add("write", self._update_price)
        ttk.Checkbutton(ex_row, text=" Breakdown Cover (+£2/day)",
                        variable=self.brkd_var, style="TCheckbutton").pack(side="left")

        # Price estimate
        pr = self._section("💷 Estimated Price")
        self.price_lbl = tk.Label(pr, text="Complete rental details above to see price estimate.",
                                  font=FONT_BODY, bg=C["bg_card"], fg=C["text_secondary"], justify="left")
        self.price_lbl.pack(anchor="w")

        # Save / Cancel
        btn_wrap = tk.Frame(self.body, bg=C["bg_dark"], padx=28, pady=20)
        btn_wrap.pack(fill="x")
        save_txt = "✏️ Update Booking" if self.existing else "💾 Save Booking"
        tk.Button(btn_wrap, text=save_txt, font=FONT_SUBHEAD, bg=C["accent"], fg=C["bg_dark"],
                  activebackground=C["accent_hover"], activeforeground=C["bg_dark"],
                  relief="flat", cursor="hand2", padx=18, pady=10, command=self._submit).pack(side="left", padx=(0, 10))
        tk.Button(btn_wrap, text="Cancel", font=FONT_BODY, bg=C["bg_card"], fg=C["text_secondary"],
                  activebackground=C["highlight"], relief="flat", cursor="hand2", padx=16, pady=10,
                  command=self.on_cancel).pack(side="left")

    def _update_price(self, *_):
        try:
            days = int(self.days_var.get())
            car = self.car_var.get()
            fuel = self.fuel_var.get()
            if not (1 <= days <= 28) or car not in CAR_TYPE_SURCHARGE or fuel not in FUEL_TYPE_SURCHARGE:
                return
            bp = calculate_price(days, car, fuel, self.mile_var.get(), self.brkd_var.get())
            lines = [f"Base ({days}d × £{BASE_RATE_PER_DAY}): £{bp['base']:.2f}"]
            if bp["car_surcharge"]:
                lines.append(f"{car} surcharge: £{bp['car_surcharge']:.2f}")
            if bp["fuel_surcharge"]:
                lines.append(f"{fuel} surcharge: £{bp['fuel_surcharge']:.2f}")
            if bp["mileage_cost"]:
                lines.append(f"Unlimited mileage: £{bp['mileage_cost']:.2f}")
            if bp["breakdown_cost"]:
                lines.append(f"Breakdown cover: £{bp['breakdown_cost']:.2f}")
            lines.append(f"\n TOTAL: £{bp['total']:.2f}")
            self.price_lbl.config(text="\n".join(lines), fg=C["text_primary"], font=FONT_MONO)
        except (ValueError, TypeError):
            self.price_lbl.config(text="Complete rental details above to see price estimate.",
                                  fg=C["text_secondary"], font=FONT_BODY)

    def _populate(self, b: dict):
        self.fn_var.set(b.get("first_name", ""))
        self.sn_var.set(b.get("surname", ""))
        self.addr_var.set(b.get("address", ""))
        self.age_var.set(str(b.get("age", "")))
        self.lic_var.set(b.get("driving_license", "Yes"))
        self.days_var.set(str(b.get("days", "")))
        self.car_var.set(b.get("car_type", ""))
        self.fuel_var.set(b.get("fuel_type", ""))
        self.mile_var.set(b.get("unlimited_mileage", False))
        self.brkd_var.set(b.get("breakdown_cover", False))

    def _collect(self) -> dict:
        return {
            "first_name": self.fn_var.get().strip(),
            "surname": self.sn_var.get().strip(),
            "address": self.addr_var.get().strip(),
            "age": self.age_var.get().strip(),
            "driving_license": self.lic_var.get(),
            "days": self.days_var.get().strip(),
            "car_type": self.car_var.get(),
            "fuel_type": self.fuel_var.get(),
            "unlimited_mileage": self.mile_var.get(),
            "breakdown_cover": self.brkd_var.get(),
        }

    def _submit(self):
        fields = self._collect()
        errors = validate_booking_fields(fields)
        if errors:
            messagebox.showerror("Validation Error", "Please fix the following:\n\n• " + "\n• ".join(errors), parent=self)
            return
        days = int(fields["days"])
        age = int(fields["age"])
        bp = calculate_price(days, fields["car_type"], fields["fuel_type"],
                             fields["unlimited_mileage"], fields["breakdown_cover"])
        record = {
            "first_name": fields["first_name"],
            "surname": fields["surname"],
            "address": fields["address"],
            "age": age,
            "driving_license": fields["driving_license"],
            "days": days,
            "car_type": fields["car_type"],
            "fuel_type": fields["fuel_type"],
            "unlimited_mileage": fields["unlimited_mileage"],
            "breakdown_cover": fields["breakdown_cover"],
            "total_cost": bp["total"],
            "price_breakdown": bp,
        }
        summary = self._build_summary(record, bp)
        if not messagebox.askyesno("Confirm Booking", summary, parent=self):
            return
        if self.existing:
            self.store.update(self.existing["id"], record)
            messagebox.showinfo("Updated", "Booking updated successfully.", parent=self)
        else:
            self.store.add(record)
            messagebox.showinfo("Saved", "Booking saved successfully.", parent=self)
        self.on_save()

    @staticmethod
    def _build_summary(rec: dict, bp: dict) -> str:
        extras = []
        if rec["unlimited_mileage"]:
            extras.append(f"Unlimited Mileage (+£{bp['mileage_cost']:.2f})")
        if rec["breakdown_cover"]:
            extras.append(f"Breakdown Cover (+£{bp['breakdown_cost']:.2f})")
        e_str = ", ".join(extras) if extras else "None"
        return (
            f"Please review your booking:\n\n"
            f" Customer : {rec['first_name']} {rec['surname']}\n"
            f" Age : {rec['age']}\n"
            f" Address : {rec['address']}\n"
            f" Car Type : {rec['car_type']}\n"
            f" Fuel Type: {rec['fuel_type']}\n"
            f" Days : {rec['days']}\n"
            f" Extras : {e_str}\n"
            f"\n ──────────────────────────────\n"
            f" TOTAL COST: £{bp['total']:.2f}\n"
            f"\nDo you want to confirm this booking?"
        )


# ─────────────────────── BOOKINGS VIEW ───────────────────────────────────────
class BookingsView(tk.Frame):
    """Full treeview of all bookings with search and actions."""
    def __init__(self, parent, store: BookingStore, on_edit, on_delete, on_back):
        super().__init__(parent, bg=C["bg_dark"])
        self.store = store
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_back = on_back
        self._sort_col = "id"
        self._sort_asc = False
        self._build()
        self.refresh()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=C["bg_card"], padx=28, pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📋 All Bookings", font=FONT_HEADING, bg=C["bg_card"],
                 fg=C["text_primary"]).pack(side="left")
        tk.Button(hdr, text="← Dashboard", font=FONT_SMALL, bg=C["bg_card"],
                  fg=C["text_secondary"], relief="flat", cursor="hand2",
                  command=self.on_back).pack(side="right")
        Separator(self).pack(fill="x")

        # Search bar
        sf = tk.Frame(self, bg=C["bg_dark"], padx=28, pady=12)
        sf.pack(fill="x")
        tk.Label(sf, text="🔍 Search:", font=FONT_BODY, bg=C["bg_dark"],
                 fg=C["text_secondary"]).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(sf, textvariable=self.search_var, font=FONT_BODY, width=32).pack(side="left", padx=8)
        tk.Button(sf, text="Clear", font=FONT_SMALL, bg=C["bg_card"], fg=C["text_secondary"],
                  relief="flat", cursor="hand2", command=lambda: self.search_var.set("")).pack(side="left")
        self.count_lbl = tk.Label(sf, text="", font=FONT_SMALL, bg=C["bg_dark"], fg=C["text_muted"])
        self.count_lbl.pack(side="right")

        # Treeview
        tv_wrap = tk.Frame(self, bg=C["bg_dark"], padx=28)
        tv_wrap.pack(fill="both", expand=True)
        cols = ("id","name","age","car_type","fuel_type","days","extras","total","created")
        self.tree = ttk.Treeview(tv_wrap, columns=cols, show="headings", selectmode="browse")
        col_cfg = [
            ("id", "ID", 55, "center"),
            ("name", "Customer", 175, "w"),
            ("age", "Age", 50, "center"),
            ("car_type", "Car Type", 110, "center"),
            ("fuel_type","Fuel", 90, "center"),
            ("days", "Days", 55, "center"),
            ("extras", "Extras", 155, "w"),
            ("total", "Total", 100, "center"),
            ("created", "Booked On", 130, "center"),
        ]
        for col, hdg, w, anc in col_cfg:
            self.tree.heading(col, text=hdg, command=lambda c=col: self._sort(c))
            self.tree.column(col, width=w, anchor=anc, minwidth=40)
        vsb = ttk.Scrollbar(tv_wrap, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tv_wrap, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tv_wrap.rowconfigure(0, weight=1)
        tv_wrap.columnconfigure(0, weight=1)

        # Action row
        act = tk.Frame(self, bg=C["bg_dark"], padx=28, pady=14)
        act.pack(fill="x")
        tk.Button(act, text="✏️ Edit Selected", font=FONT_BODY, bg=C["bg_card"],
                  fg=C["text_primary"], activebackground=C["highlight"], relief="flat",
                  cursor="hand2", padx=14, pady=8, command=self._edit_selected).pack(side="left", padx=(0, 10))
        tk.Button(act, text="🗑 Delete Selected", font=FONT_BODY, bg=C["danger"],
                  fg=C["text_primary"], activebackground="#FF6B6B", relief="flat",
                  cursor="hand2", padx=14, pady=8, command=self._delete_selected).pack(side="left")
        tk.Label(act, text="Double-click a row to edit", font=FONT_SMALL,
                 bg=C["bg_dark"], fg=C["text_muted"]).pack(side="right")
        self.tree.bind("<Double-1>", lambda _: self._edit_selected())

    def _sort(self, col: str):
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        self.refresh()

    def refresh(self):
        query = self.search_var.get().lower()
        results = []
        for b in self.store.bookings:
            name = f"{b.get('first_name','')} {b.get('surname','')}".lower()
            searchable = name + b.get("car_type","").lower() + b.get("fuel_type","").lower() + str(b.get("id",""))
            if query in searchable:
                results.append(b)
        # Sort
        def _key(b):
            v = b.get(self._sort_col, "")
            if self._sort_col in ("id","age","days"):
                try:
                    return int(v)
                except (ValueError, TypeError):
                    return 0
            if self._sort_col == "total":
                return b.get("total_cost", 0)
            return str(v).lower()
        results.sort(key=_key, reverse=not self._sort_asc)

        for row in self.tree.get_children():
            self.tree.delete(row)
        for i, b in enumerate(results):
            name = f"{b.get('first_name','')} {b.get('surname','')}"
            extras = []
            if b.get("unlimited_mileage"):
                extras.append("Mileage")
            if b.get("breakdown_cover"):
                extras.append("Breakdown")
            ex_str = ", ".join(extras) if extras else "—"
            tag = "alt" if i % 2 else ""
            self.tree.insert("", "end", iid=str(b["id"]), tags=(tag,), values=(
                b.get("id",""), name, b.get("age",""), b.get("car_type",""),
                b.get("fuel_type",""), b.get("days",""), ex_str,
                f"£{b.get('total_cost',0):.2f}", b.get("created_at","")
            ))
        self.tree.tag_configure("alt", background=C["row_alt"])
        self.count_lbl.config(text=f"{len(results)} booking(s)")

    def _selected_id(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a booking first.", parent=self)
            return None
        return int(sel[0])

    def _edit_selected(self):
        bid = self._selected_id()
        if bid is not None:
            self.on_edit(bid)

    def _delete_selected(self):
        bid = self._selected_id()
        if bid is None:
            return
        b = self.store.get_by_id(bid)
        if b:
            name = f"{b.get('first_name','')} {b.get('surname','')}"
            if messagebox.askyesno("Confirm Delete", f"Delete booking #{bid} for {name}?\nThis cannot be undone.", parent=self):
                self.store.delete(bid)
                self.refresh()
                self.on_delete()
                messagebox.showinfo("Deleted", "Booking deleted.", parent=self)


# ─────────────────────── SELECT-TO-EDIT DIALOG ───────────────────────────────
class SelectBookingDialog(tk.Toplevel):
    """Small dialog to choose a booking ID for update/delete."""
    def __init__(self, parent, store: BookingStore, action_label: str, on_select):
        super().__init__(parent)
        self.store = store
        self.on_select = on_select
        self.title(f"Select Booking — {action_label}")
        self.configure(bg=C["bg_card"])
        self.resizable(False, False)
        w, h = 540, 400
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.grab_set()
        self._build(action_label)

    def _build(self, action_label: str):
        tk.Frame(self, bg=C["accent"], height=3).pack(fill="x")
        hdr = tk.Frame(self, bg=C["bg_card"], padx=20, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"Choose a booking to {action_label.lower()}",
                 font=FONT_SUBHEAD, bg=C["bg_card"], fg=C["text_primary"]).pack(anchor="w")
        Separator(self).pack(fill="x")
        tv_frame = tk.Frame(self, bg=C["bg_card"], padx=16, pady=10)
        tv_frame.pack(fill="both", expand=True)
        cols = ("id","name","car_type","days","total")
        tree = ttk.Treeview(tv_frame, columns=cols, show="headings", height=10)
        cfg = [("id","ID",55), ("name","Customer",180), ("car_type","Car",110),
               ("days","Days",55), ("total","Total",100)]
        for col, hdg, w in cfg:
            tree.heading(col, text=hdg)
            tree.column(col, width=w, anchor="center" if col != "name" else "w")
        vsb = ttk.Scrollbar(tv_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="left", fill="y")
        for b in sorted(self.store.bookings, key=lambda x: x.get("id", 0), reverse=True):
            name = f"{b.get('first_name','')} {b.get('surname','')}"
            tree.insert("", "end", iid=str(b["id"]), values=(
                b.get("id",""), name, b.get("car_type",""), b.get("days",""),
                f"£{b.get('total_cost',0):.2f}"
            ))
        btn_row = tk.Frame(self, bg=C["bg_card"], padx=16, pady=12)
        btn_row.pack(fill="x")
        def _confirm():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("No Selection", "Please select a booking.", parent=self)
                return
            bid = int(sel[0])
            self.destroy()
            self.on_select(bid)
        tk.Button(btn_row, text=f" {action_label} ", font=FONT_SUBHEAD, bg=C["accent"],
                  fg=C["bg_dark"], activebackground=C["accent_hover"], relief="flat",
                  cursor="hand2", padx=14, pady=8, command=_confirm).pack(side="left", padx=(0, 10))
        tk.Button(btn_row, text="Cancel", font=FONT_BODY, bg=C["bg_card"],
                  fg=C["text_secondary"], activebackground=C["highlight"], relief="flat",
                  cursor="hand2", padx=12, pady=8, command=self.destroy).pack(side="left")
        tree.bind("<Double-1>", lambda _: _confirm())


# ─────────────────────── MAIN APPLICATION ────────────────────────────────────
class WeAreCarsApp:
    """Root application controller — manages all screens."""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry("1200x760")
        self.root.minsize(1000, 650)
        self.root.configure(bg=C["bg_dark"])
        apply_dark_theme(self.root)
        self.store = BookingStore()
        self._current_frame: Optional[tk.Frame] = None
        self._show_splash()

    def _clear(self):
        if self._current_frame:
            self._current_frame.destroy()
            self._current_frame = None

    def _show(self, frame: tk.Frame):
        self._clear()
        self._current_frame = frame
        frame.pack(fill="both", expand=True)

    def _show_splash(self):
        self.root.withdraw()
        splash = SplashScreen(self.root)
        self.root.after(3000, lambda: self._after_splash(splash))

    def _after_splash(self, splash: SplashScreen):
        splash.destroy()
        self.root.deiconify()
        self._show_login()

    def _show_login(self):
        self._show(LoginScreen(self.root, on_success=self._show_dashboard))

    def _show_dashboard(self):
        nav = {
            "add": self._show_add,
            "view": self._show_view_bookings,
            "update": self._show_update_picker,
            "delete": self._show_delete_picker,
            "logout": self._logout,
        }
        dash = Dashboard(self.root, self.store, nav)
        self._show(dash)

    def _show_add(self):
        form = BookingForm(self.root, self.store, on_save=self._show_dashboard,
                           on_cancel=self._show_dashboard)
        self._show(form)

    def _show_view_bookings(self):
        view = BookingsView(self.root, self.store, on_edit=self._edit_booking,
                            on_delete=self._show_dashboard, on_back=self._show_dashboard)
        self._show(view)

    def _show_update_picker(self):
        if not self.store.bookings:
            messagebox.showinfo("No Bookings", "There are no bookings to update.")
            return
        SelectBookingDialog(self.root, self.store, action_label="Edit Booking",
                            on_select=self._edit_booking)

    def _edit_booking(self, booking_id: int):
        b = self.store.get_by_id(booking_id)
        if not b:
            messagebox.showerror("Not Found", f"Booking #{booking_id} was not found.")
            return
        form = BookingForm(self.root, self.store, on_save=self._show_dashboard,
                           on_cancel=self._show_dashboard, existing=b)
        self._show(form)

    def _show_delete_picker(self):
        if not self.store.bookings:
            messagebox.showinfo("No Bookings", "There are no bookings to delete.")
            return
        SelectBookingDialog(self.root, self.store, action_label="Delete Booking",
                            on_select=self._confirm_delete)

    def _confirm_delete(self, booking_id: int):
        b = self.store.get_by_id(booking_id)
        if not b:
            messagebox.showerror("Not Found", f"Booking #{booking_id} was not found.")
            return
        name = f"{b.get('first_name','')} {b.get('surname','')}"
        if messagebox.askyesno("Confirm Delete", f"Permanently delete booking #{booking_id} for {name}?\nThis action cannot be undone."):
            self.store.delete(booking_id)
            messagebox.showinfo("Deleted", f"Booking #{booking_id} has been deleted.")
            self._show_dashboard()

    def _logout(self):
        if messagebox.askyesno("Log Out", "Are you sure you want to log out?"):
            self._show_login()

    def run(self):
        self.root.mainloop()


# ─────────────────────── ENTRY POINT ─────────────────────────────────────────
if __name__ == "__main__":
    app = WeAreCarsApp()
    app.run()
