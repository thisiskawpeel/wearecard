"""
WeAreCars - Car Rental Management System
=========================================
A standalone Windows Forms-style application built with Python Tkinter.
Designed for WeAreCars staff to manage vehicle rental bookings.

Author  : Graduate Software Developer
Version : 1.0.0
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import re
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
#  GLOBAL DATA STORE  (in-memory booking list, persisted to JSON)
# ─────────────────────────────────────────────────────────────────────────────
BOOKINGS_FILE = "wearecars_bookings.json"  # local JSON persistence file

# Load existing bookings from file on startup
def load_bookings():
    """Load bookings list from JSON file, or return empty list."""
    if os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE, "r") as f:
            return json.load(f)
    return []

def save_bookings(bookings):
    """Persist bookings list to JSON file."""
    with open(BOOKINGS_FILE, "w") as f:
        json.dump(bookings, f, indent=2)

bookings = load_bookings()   # global booking list shared across frames


# ─────────────────────────────────────────────────────────────────────────────
#  PRICING CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
BASE_RATE       = 25    # £ per day (base rate)
CAR_PRICES      = {"City Car": 0, "Family Car": 50, "Sports Car": 75, "SUV": 65}
FUEL_PRICES     = {"Petrol": 0, "Diesel": 0, "Hybrid": 30, "Full Electric": 50}
MILEAGE_RATE    = 10    # £ per day extra
BREAKDOWN_RATE  = 2     # £ per day extra


# ─────────────────────────────────────────────────────────────────────────────
#  COLOUR PALETTE  (professional dark-blue automotive theme)
# ─────────────────────────────────────────────────────────────────────────────
C = {
    "bg_dark":   "#0D1B2A",   # deep navy
    "bg_mid":    "#1B2A3B",   # panel background
    "bg_card":   "#243447",   # card / entry background
    "accent":    "#E8A838",   # amber accent (car badge feel)
    "accent2":   "#4FC3F7",   # light-blue highlight
    "text_main": "#F0F4F8",   # primary text
    "text_dim":  "#8FA3B1",   # secondary / hint text
    "danger":    "#E53935",   # error / delete
    "success":   "#43A047",   # confirm / save
    "white":     "#FFFFFF",
    "entry_bg":  "#1A2B3C",
    "border":    "#2E4057",
}

FONT_TITLE   = ("Segoe UI", 22, "bold")
FONT_HEAD    = ("Segoe UI", 13, "bold")
FONT_SUBHEAD = ("Segoe UI", 11, "bold")
FONT_BODY    = ("Segoe UI", 10)
FONT_SMALL   = ("Segoe UI", 9)
FONT_MONO    = ("Courier New", 10)


# ─────────────────────────────────────────────────────────────────────────────
#  HELPER – styled widget factories
# ─────────────────────────────────────────────────────────────────────────────

def make_frame(parent, **kw):
    """Return a dark-themed Frame."""
    return tk.Frame(parent, bg=C["bg_mid"], **kw)

def make_label(parent, text, font=FONT_BODY, fg=None, **kw):
    """Return a styled Label."""
    return tk.Label(parent, text=text, font=font,
                    fg=fg or C["text_main"], bg=C["bg_mid"], **kw)

def make_entry(parent, textvariable=None, width=28, show="", **kw):
    """Return a styled Entry widget."""
    return tk.Entry(parent, textvariable=textvariable, width=width, show=show,
                    bg=C["entry_bg"], fg=C["text_main"], insertbackground=C["accent"],
                    relief="flat", font=FONT_BODY,
                    highlightthickness=1, highlightbackground=C["border"],
                    highlightcolor=C["accent"], **kw)

def make_button(parent, text, command, bg=None, fg=None, width=18, **kw):
    """Return a flat styled Button."""
    return tk.Button(parent, text=text, command=command,
                     bg=bg or C["accent"], fg=fg or C["bg_dark"],
                     font=FONT_SUBHEAD, relief="flat",
                     activebackground=C["accent2"], activeforeground=C["bg_dark"],
                     cursor="hand2", width=width, pady=6, **kw)

def make_separator(parent, pady=8):
    """Return a thin separator line."""
    sep = tk.Frame(parent, height=1, bg=C["border"])
    sep.pack(fill="x", pady=pady)
    return sep


# ─────────────────────────────────────────────────────────────────────────────
#  SPLASH SCREEN  (shown for 3 seconds before login)
# ─────────────────────────────────────────────────────────────────────────────

class SplashScreen(tk.Toplevel):
    """
    Splash screen displayed for 3 seconds when the application launches.
    Shows the WeAreCars brand, a welcome message, and loading progress bar.
    """

    def __init__(self, root, on_done):
        super().__init__(root)
        self.on_done = on_done

        # Window configuration – no title bar, centred
        self.overrideredirect(True)   # remove title bar / border
        self.configure(bg=C["bg_dark"])

        # Centre the splash (600 × 380) on screen
        w, h = 600, 380
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - w) // 2
        y  = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self._build_ui()
        self._animate_progress(0)   # start progress bar animation

    def _build_ui(self):
        """Construct all splash UI elements."""

        # Top decorative stripe
        stripe = tk.Frame(self, bg=C["accent"], height=6)
        stripe.pack(fill="x")

        # Main content area
        body = tk.Frame(self, bg=C["bg_dark"])
        body.pack(expand=True, fill="both", padx=40, pady=30)

        # Car emoji icon (large display)
        tk.Label(body, text="🚗", font=("Segoe UI Emoji", 54),
                 bg=C["bg_dark"]).pack(pady=(10, 0))

        # Brand name
        tk.Label(body, text="WeAreCars",
                 font=("Segoe UI", 32, "bold"),
                 fg=C["accent"], bg=C["bg_dark"]).pack()

        # Tagline
        tk.Label(body, text="Car Rental Management System",
                 font=("Segoe UI", 12), fg=C["text_dim"],
                 bg=C["bg_dark"]).pack(pady=(2, 16))

        make_separator(body, pady=4)

        # Welcome + instructions panel
        instructions = (
            "Welcome, WeAreCars Staff Member!\n\n"
            "• Login using your staff credentials\n"
            "• Manage bookings from the dashboard\n"
            "• Add, view, update or delete rental records"
        )
        tk.Label(body, text=instructions, font=FONT_BODY,
                 fg=C["text_main"], bg=C["bg_dark"],
                 justify="left", wraplength=480).pack(pady=6)

        # Progress bar container
        bar_frame = tk.Frame(body, bg=C["bg_dark"])
        bar_frame.pack(fill="x", pady=(18, 4))

        self.progress_var = tk.IntVar(value=0)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Splash.Horizontal.TProgressbar",
                        troughcolor=C["bg_mid"],
                        background=C["accent"],
                        thickness=8)

        self.progress = ttk.Progressbar(bar_frame,
                                        variable=self.progress_var,
                                        maximum=100,
                                        style="Splash.Horizontal.TProgressbar")
        self.progress.pack(fill="x")

        # Loading label
        self.loading_lbl = tk.Label(body, text="Loading…",
                                    font=FONT_SMALL, fg=C["text_dim"],
                                    bg=C["bg_dark"])
        self.loading_lbl.pack()

        # Bottom stripe
        tk.Frame(self, bg=C["accent"], height=6).pack(fill="x", side="bottom")

    def _animate_progress(self, step):
        """
        Recursively increment progress bar over 3 seconds (300 steps × 10 ms).
        Calls on_done callback when complete.
        """
        if step <= 100:
            self.progress_var.set(step)
            msgs = {0: "Loading…", 30: "Initialising database…",
                    60: "Preparing dashboard…", 90: "Almost ready…", 100: "Done!"}
            if step in msgs:
                self.loading_lbl.config(text=msgs[step])
            # 3000 ms / 100 steps = 30 ms per step
            self.after(30, self._animate_progress, step + 1)
        else:
            self.after(100, self._finish)   # brief pause then close

    def _finish(self):
        """Destroy splash and invoke the callback to show login."""
        self.destroy()
        self.on_done()


# ─────────────────────────────────────────────────────────────────────────────
#  LOGIN FRAME
# ─────────────────────────────────────────────────────────────────────────────

class LoginFrame(tk.Frame):
    """
    Staff login page.
    Fixed credentials: sta001 / givemethekeys123
    Includes show/hide password toggle.
    """

    # Fixed staff credentials (in production these would be hashed)
    VALID_USER = "sta001"
    VALID_PASS = "givemethekeys123"

    def __init__(self, parent, on_login_success):
        super().__init__(parent, bg=C["bg_dark"])
        self.on_login_success = on_login_success
        self._build_ui()

    def _build_ui(self):
        """Build login card centred on screen."""

        # Outer padding frame
        outer = tk.Frame(self, bg=C["bg_dark"])
        outer.place(relx=0.5, rely=0.5, anchor="center")

        # Card background
        card = tk.Frame(outer, bg=C["bg_mid"], padx=40, pady=40)
        card.pack()

        # Logo / branding
        tk.Label(card, text="🚗  WeAreCars",
                 font=("Segoe UI", 20, "bold"),
                 fg=C["accent"], bg=C["bg_mid"]).pack(pady=(0, 4))

        tk.Label(card, text="Staff Login Portal",
                 font=FONT_BODY, fg=C["text_dim"],
                 bg=C["bg_mid"]).pack(pady=(0, 24))

        # ── Username row ──────────────────────────────────────────────────
        tk.Label(card, text="Username", font=FONT_SUBHEAD,
                 fg=C["text_main"], bg=C["bg_mid"],
                 anchor="w").pack(fill="x")

        self.username_var = tk.StringVar()
        user_entry = make_entry(card, textvariable=self.username_var, width=30)
        user_entry.pack(pady=(4, 14))
        user_entry.bind("<Return>", lambda e: self.pass_entry.focus())
        user_entry.focus()   # auto-focus username field on load

        # ── Password row ──────────────────────────────────────────────────
        tk.Label(card, text="Password", font=FONT_SUBHEAD,
                 fg=C["text_main"], bg=C["bg_mid"],
                 anchor="w").pack(fill="x")

        pass_row = tk.Frame(card, bg=C["bg_mid"])
        pass_row.pack(pady=(4, 6))

        self.password_var = tk.StringVar()
        self.pass_entry = make_entry(pass_row, textvariable=self.password_var,
                                     width=25, show="•")
        self.pass_entry.pack(side="left")
        self.pass_entry.bind("<Return>", lambda e: self._attempt_login())

        # Show / Hide password toggle button
        self.show_pass = tk.BooleanVar(value=False)
        self.eye_btn = tk.Button(
            pass_row, text="👁", font=("Segoe UI Emoji", 12),
            bg=C["entry_bg"], fg=C["text_dim"], relief="flat",
            bd=0, cursor="hand2", activebackground=C["bg_card"],
            command=self._toggle_password
        )
        self.eye_btn.pack(side="left", padx=(4, 0))

        # Tooltip hint for show password button
        self._add_tooltip(self.eye_btn, "Show / Hide Password")

        # ── Error message label (hidden until needed) ─────────────────────
        self.err_lbl = tk.Label(card, text="", font=FONT_SMALL,
                                fg=C["danger"], bg=C["bg_mid"])
        self.err_lbl.pack(pady=(2, 10))

        # ── Login button ──────────────────────────────────────────────────
        make_button(card, "🔑  Login", self._attempt_login,
                    bg=C["accent"], width=30).pack(pady=(8, 0))

        # Hint for demo
        tk.Label(card, text="Hint: sta001 / givemethekeys123",
                 font=FONT_SMALL, fg=C["text_dim"],
                 bg=C["bg_mid"]).pack(pady=(10, 0))

    def _toggle_password(self):
        """Toggle the password field between hidden (•) and visible text."""
        self.show_pass.set(not self.show_pass.get())
        # Update show character; empty string means visible
        self.pass_entry.config(show="" if self.show_pass.get() else "•")
        self.eye_btn.config(
            fg=C["accent"] if self.show_pass.get() else C["text_dim"]
        )

    def _attempt_login(self):
        """Validate credentials and proceed to dashboard or show error."""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        # Input presence check
        if not username or not password:
            self.err_lbl.config(text="⚠  Please enter both username and password.")
            return

        # Credential validation
        if username == self.VALID_USER and password == self.VALID_PASS:
            self.err_lbl.config(text="")
            self.on_login_success()          # proceed to dashboard
        else:
            self.err_lbl.config(text="✖  Incorrect username or password.")
            self.password_var.set("")        # clear password field on failure
            self.pass_entry.focus()

    def _add_tooltip(self, widget, text):
        """Attach a simple hover tooltip to a widget."""
        tip = None

        def show(event):
            nonlocal tip
            tip = tk.Toplevel(widget)
            tip.overrideredirect(True)
            tip.configure(bg=C["bg_card"])
            tk.Label(tip, text=text, font=FONT_SMALL,
                     bg=C["bg_card"], fg=C["text_main"],
                     padx=6, pady=3).pack()
            x = widget.winfo_rootx() + 25
            y = widget.winfo_rooty() + 20
            tip.geometry(f"+{x}+{y}")

        def hide(event):
            nonlocal tip
            if tip:
                tip.destroy()
                tip = None

        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD FRAME
# ─────────────────────────────────────────────────────────────────────────────

class DashboardFrame(tk.Frame):
    """
    Main dashboard shown after login.
    Displays:
      - Summary stats (total bookings, total revenue)
      - Analytics bar chart (car type breakdown)
      - Quick-action buttons (Add / View / Logout)
    """

    def __init__(self, parent, controller):
        super().__init__(parent, bg=C["bg_dark"])
        self.controller = controller   # reference to main App for page switching
        self._build_ui()

    def _build_ui(self):
        """Construct dashboard layout."""

        # ── Top header bar ────────────────────────────────────────────────
        header = tk.Frame(self, bg=C["bg_mid"], padx=20, pady=12)
        header.pack(fill="x")

        tk.Label(header, text="🚗  WeAreCars  —  Staff Dashboard",
                 font=FONT_TITLE, fg=C["accent"],
                 bg=C["bg_mid"]).pack(side="left")

        make_button(header, "⬅  Logout", self.controller.show_login,
                    bg=C["danger"], fg=C["white"], width=12).pack(side="right")

        # ── Scrollable content area ───────────────────────────────────────
        canvas = tk.Canvas(self, bg=C["bg_dark"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg=C["bg_dark"])

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Enable mousewheel scrolling
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        self._populate(self.scroll_frame)

    def _populate(self, parent):
        """Fill the scrollable area with stats, chart and action buttons."""

        pad = dict(padx=20, pady=8)

        # ── KPI stats row ─────────────────────────────────────────────────
        stats_row = tk.Frame(parent, bg=C["bg_dark"])
        stats_row.pack(fill="x", **pad)

        total_bookings = len(bookings)
        total_revenue  = sum(b.get("total_price", 0) for b in bookings)
        pending        = sum(1 for b in bookings if b.get("status") == "Active")

        kpis = [
            ("📋  Total Bookings", str(total_bookings), C["accent2"]),
            ("💷  Total Revenue",  f"£{total_revenue:,.2f}", C["success"]),
            ("🚦  Active Rentals", str(pending), C["accent"]),
        ]

        for label, value, color in kpis:
            card = tk.Frame(stats_row, bg=C["bg_mid"], padx=20, pady=16)
            card.pack(side="left", expand=True, fill="both", padx=8)
            tk.Label(card, text=label, font=FONT_SMALL,
                     fg=C["text_dim"], bg=C["bg_mid"]).pack(anchor="w")
            tk.Label(card, text=value, font=("Segoe UI", 22, "bold"),
                     fg=color, bg=C["bg_mid"]).pack(anchor="w")

        # ── Analytics – car type bar chart (Canvas-drawn) ─────────────────
        tk.Label(parent, text="📊  Bookings by Car Type",
                 font=FONT_HEAD, fg=C["text_main"],
                 bg=C["bg_dark"]).pack(anchor="w", **pad)

        chart_frame = tk.Frame(parent, bg=C["bg_mid"], padx=16, pady=16)
        chart_frame.pack(fill="x", padx=20, pady=4)

        self._draw_bar_chart(chart_frame)

        # ── Quick actions ─────────────────────────────────────────────────
        tk.Label(parent, text="⚡  Quick Actions",
                 font=FONT_HEAD, fg=C["text_main"],
                 bg=C["bg_dark"]).pack(anchor="w", **pad)

        actions_row = tk.Frame(parent, bg=C["bg_dark"])
        actions_row.pack(fill="x", padx=20, pady=4)

        action_btns = [
            ("➕  Add Booking",    self.controller.show_add_booking,   C["success"]),
            ("📋  View Bookings",  self.controller.show_view_bookings, C["accent2"]),
            ("✏️  Update Booking", self.controller.show_update_booking, C["accent"]),
            ("🗑️  Delete Booking", self.controller.show_delete_booking, C["danger"]),
        ]

        for text, cmd, color in action_btns:
            make_button(actions_row, text, cmd,
                        bg=color, fg=C["white"] if color != C["accent"] else C["bg_dark"],
                        width=16).pack(side="left", padx=8, pady=4)

        # ── Recent bookings table ─────────────────────────────────────────
        tk.Label(parent, text="🕑  Recent Bookings",
                 font=FONT_HEAD, fg=C["text_main"],
                 bg=C["bg_dark"]).pack(anchor="w", **pad)

        self._draw_recent_table(parent)

    def _draw_bar_chart(self, parent):
        """Draw a simple canvas bar chart for car-type booking counts."""
        car_types = list(CAR_PRICES.keys())
        counts = {ct: 0 for ct in car_types}
        for b in bookings:
            ct = b.get("car_type", "")
            if ct in counts:
                counts[ct] += 1

        max_count = max(counts.values(), default=1) or 1
        bar_colors = [C["accent"], C["accent2"], C["success"], C["danger"]]

        chart_w, chart_h = 560, 150
        c = tk.Canvas(parent, width=chart_w, height=chart_h,
                      bg=C["bg_mid"], highlightthickness=0)
        c.pack()

        bar_w   = 80
        spacing = 40
        start_x = 40

        for i, ct in enumerate(car_types):
            count  = counts[ct]
            x0     = start_x + i * (bar_w + spacing)
            x1     = x0 + bar_w
            bar_h  = int((count / max_count) * 100) if max_count else 0
            y0     = chart_h - 30 - bar_h
            y1     = chart_h - 30

            # Draw bar
            c.create_rectangle(x0, y0, x1, y1,
                                fill=bar_colors[i], outline="")

            # Count label above bar
            c.create_text((x0 + x1) // 2, y0 - 8,
                          text=str(count), fill=C["text_main"],
                          font=FONT_SMALL)

            # Car type label below bar
            short = ct.replace(" Car", "").replace("ful Electric", ".E")
            c.create_text((x0 + x1) // 2, chart_h - 14,
                          text=short, fill=C["text_dim"],
                          font=FONT_SMALL)

    def _draw_recent_table(self, parent):
        """Display the 5 most recent bookings in a Treeview table."""
        cols = ("ID", "Name", "Car Type", "Days", "Total", "Status")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Treeview",
                        background=C["bg_card"],
                        foreground=C["text_main"],
                        fieldbackground=C["bg_card"],
                        rowheight=28,
                        font=FONT_BODY)
        style.configure("Dark.Treeview.Heading",
                        background=C["bg_mid"],
                        foreground=C["accent"],
                        font=FONT_SUBHEAD)
        style.map("Dark.Treeview",
                  background=[("selected", C["accent"])],
                  foreground=[("selected", C["bg_dark"])])

        tree = ttk.Treeview(parent, columns=cols, show="headings",
                            height=5, style="Dark.Treeview")

        col_widths = [50, 150, 120, 60, 90, 80]
        for col, w in zip(cols, col_widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        # Show last 5 bookings (most recent first)
        for b in reversed(bookings[-5:]):
            name = f"{b.get('first_name','')} {b.get('surname','')}"
            tree.insert("", "end", values=(
                b.get("id", ""),
                name,
                b.get("car_type", ""),
                b.get("days", ""),
                f"£{b.get('total_price', 0):.2f}",
                b.get("status", "Active")
            ))

        tree.pack(fill="x", padx=20, pady=(0, 20))

    def refresh(self):
        """Refresh dashboard by rebuilding the content area."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self._populate(self.scroll_frame)


# ─────────────────────────────────────────────────────────────────────────────
#  ADD BOOKING FRAME
# ─────────────────────────────────────────────────────────────────────────────

class AddBookingFrame(tk.Frame):
    """
    New booking form.
    Collects all customer and rental details, validates inputs,
    calculates total price, shows confirmation summary and saves booking.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, bg=C["bg_dark"])
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        """Build the booking form layout."""

        # ── Header ────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=C["bg_mid"], padx=20, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="➕  Add New Booking",
                 font=FONT_TITLE, fg=C["accent"],
                 bg=C["bg_mid"]).pack(side="left")
        make_button(header, "⬅  Dashboard",
                    self.controller.show_dashboard,
                    bg=C["bg_card"], fg=C["text_main"],
                    width=14).pack(side="right")

        # ── Scrollable form ───────────────────────────────────────────────
        canvas = tk.Canvas(self, bg=C["bg_dark"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        form_frame = tk.Frame(canvas, bg=C["bg_dark"])
        form_frame.bind("<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=form_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        self._build_form(form_frame)

    def _build_form(self, parent):
        """Populate form sections inside the scrollable frame."""

        # ── Section: Customer Details ─────────────────────────────────────
        self._section_label(parent, "👤  Customer Details")
        cust = tk.Frame(parent, bg=C["bg_mid"], padx=20, pady=16)
        cust.pack(fill="x", padx=20, pady=(0, 12))

        self.first_name_var = tk.StringVar()
        self.surname_var    = tk.StringVar()
        self.address_var    = tk.StringVar()
        self.age_var        = tk.StringVar()

        self._form_row(cust, "Customer First Name *", self.first_name_var)
        self._form_row(cust, "Customer Surname *",    self.surname_var)
        self._form_row(cust, "Customer Address *",    self.address_var, width=50)
        self._form_row(cust, "Customer Age *",        self.age_var)

        # Driving licence radio (Yes / No)
        lic_frame = tk.Frame(cust, bg=C["bg_mid"])
        lic_frame.pack(fill="x", pady=4)
        tk.Label(lic_frame, text="Valid Driving Licence *",
                 font=FONT_BODY, fg=C["text_main"],
                 bg=C["bg_mid"], width=24, anchor="w").pack(side="left")
        self.licence_var = tk.StringVar(value="Yes")
        for val in ("Yes", "No"):
            tk.Radiobutton(lic_frame, text=val, variable=self.licence_var,
                           value=val, bg=C["bg_mid"], fg=C["text_main"],
                           selectcolor=C["entry_bg"], activebackground=C["bg_mid"],
                           font=FONT_BODY).pack(side="left", padx=8)

        # ── Section: Rental Options ───────────────────────────────────────
        self._section_label(parent, "🚗  Rental Options")
        rental = tk.Frame(parent, bg=C["bg_mid"], padx=20, pady=16)
        rental.pack(fill="x", padx=20, pady=(0, 12))

        # Number of days
        days_frame = tk.Frame(rental, bg=C["bg_mid"])
        days_frame.pack(fill="x", pady=4)
        tk.Label(days_frame, text="Number of Days * (1–28)",
                 font=FONT_BODY, fg=C["text_main"],
                 bg=C["bg_mid"], width=24, anchor="w").pack(side="left")
        self.days_var = tk.IntVar(value=1)
        tk.Spinbox(days_frame, from_=1, to=28, textvariable=self.days_var,
                   width=8, bg=C["entry_bg"], fg=C["text_main"],
                   buttonbackground=C["bg_card"], relief="flat",
                   font=FONT_BODY, insertbackground=C["accent"],
                   command=self._update_price_preview).pack(side="left", padx=8)

        # Car type
        self.car_type_var = tk.StringVar(value="City Car")
        self._option_row(rental, "Car Type *", self.car_type_var,
                         list(CAR_PRICES.keys()),
                         lambda _: self._update_price_preview())

        # Fuel type
        self.fuel_var = tk.StringVar(value="Petrol")
        self._option_row(rental, "Fuel Type *", self.fuel_var,
                         list(FUEL_PRICES.keys()),
                         lambda _: self._update_price_preview())

        # ── Section: Optional Extras ──────────────────────────────────────
        self._section_label(parent, "➕  Optional Extras")
        extras = tk.Frame(parent, bg=C["bg_mid"], padx=20, pady=16)
        extras.pack(fill="x", padx=20, pady=(0, 12))

        self.mileage_var   = tk.BooleanVar(value=False)
        self.breakdown_var = tk.BooleanVar(value=False)

        self._check_row(extras, "Unlimited Mileage (+£10/day)",
                        self.mileage_var)
        self._check_row(extras, "Breakdown Cover (+£2/day)",
                        self.breakdown_var)

        # ── Price Preview ─────────────────────────────────────────────────
        price_frame = tk.Frame(parent, bg=C["bg_card"], padx=20, pady=12)
        price_frame.pack(fill="x", padx=20, pady=(0, 12))

        tk.Label(price_frame, text="💷  Estimated Total",
                 font=FONT_SUBHEAD, fg=C["text_dim"],
                 bg=C["bg_card"]).pack(side="left")

        self.price_preview_lbl = tk.Label(price_frame, text="£0.00",
                                          font=("Segoe UI", 18, "bold"),
                                          fg=C["success"], bg=C["bg_card"])
        self.price_preview_lbl.pack(side="right")

        # Bind spinbox/checkbox changes to refresh price
        self.mileage_var.trace_add("write",   lambda *a: self._update_price_preview())
        self.breakdown_var.trace_add("write",  lambda *a: self._update_price_preview())
        self.days_var.trace_add("write",       lambda *a: self._update_price_preview())
        self._update_price_preview()  # initial calculation

        # ── Action buttons ────────────────────────────────────────────────
        btn_row = tk.Frame(parent, bg=C["bg_dark"])
        btn_row.pack(pady=16, padx=20)

        make_button(btn_row, "📋  Preview & Confirm",
                    self._confirm_booking, bg=C["accent"], width=20).pack(
                    side="left", padx=8)
        make_button(btn_row, "🔄  Clear Form",
                    self._clear_form, bg=C["bg_card"],
                    fg=C["text_main"], width=14).pack(side="left", padx=8)

    # ── Form helper builders ──────────────────────────────────────────────

    def _section_label(self, parent, text):
        """Render a bold section heading."""
        row = tk.Frame(parent, bg=C["bg_dark"])
        row.pack(fill="x", padx=20, pady=(14, 2))
        tk.Label(row, text=text, font=FONT_HEAD,
                 fg=C["accent2"], bg=C["bg_dark"]).pack(side="left")

    def _form_row(self, parent, label, var, width=30):
        """Render a label + entry pair."""
        row = tk.Frame(parent, bg=C["bg_mid"])
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, font=FONT_BODY,
                 fg=C["text_main"], bg=C["bg_mid"],
                 width=24, anchor="w").pack(side="left")
        make_entry(row, textvariable=var, width=width).pack(side="left", padx=8)

    def _option_row(self, parent, label, var, options, on_change=None):
        """Render a label + OptionMenu dropdown."""
        row = tk.Frame(parent, bg=C["bg_mid"])
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, font=FONT_BODY,
                 fg=C["text_main"], bg=C["bg_mid"],
                 width=24, anchor="w").pack(side="left")
        menu = tk.OptionMenu(row, var, *options,
                             command=on_change)
        menu.config(bg=C["entry_bg"], fg=C["text_main"],
                    activebackground=C["bg_card"],
                    activeforeground=C["text_main"],
                    relief="flat", font=FONT_BODY,
                    highlightthickness=0, width=18)
        menu["menu"].config(bg=C["bg_card"], fg=C["text_main"],
                            font=FONT_BODY)
        menu.pack(side="left", padx=8)

    def _check_row(self, parent, label, var):
        """Render a checkbox option row."""
        row = tk.Frame(parent, bg=C["bg_mid"])
        row.pack(fill="x", pady=4)
        tk.Checkbutton(row, text=label, variable=var,
                       bg=C["bg_mid"], fg=C["text_main"],
                       selectcolor=C["entry_bg"],
                       activebackground=C["bg_mid"],
                       font=FONT_BODY).pack(side="left")

    # ── Price calculation ─────────────────────────────────────────────────

    def _calculate_total(self):
        """
        Compute the total rental price based on:
        - Number of days × base rate (£25/day)
        - Car type surcharge (flat)
        - Fuel type surcharge (flat)
        - Optional extras per day
        Returns (days, breakdown dict, total) tuple.
        """
        try:
            days = int(self.days_var.get())
        except (ValueError, tk.TclError):
            days = 1

        days = max(1, min(28, days))   # clamp to valid range

        base       = days * BASE_RATE
        car_extra  = CAR_PRICES.get(self.car_type_var.get(), 0)
        fuel_extra = FUEL_PRICES.get(self.fuel_var.get(), 0)
        mileage    = days * MILEAGE_RATE  if self.mileage_var.get() else 0
        breakdown  = days * BREAKDOWN_RATE if self.breakdown_var.get() else 0

        total = base + car_extra + fuel_extra + mileage + breakdown

        breakdown_dict = {
            "Base rate":       f"£{BASE_RATE}/day × {days} days = £{base}",
            "Car type":        f"+£{car_extra} ({self.car_type_var.get()})",
            "Fuel type":       f"+£{fuel_extra} ({self.fuel_var.get()})",
            "Unlimited mileage": f"+£{mileage}" if mileage else "Not selected",
            "Breakdown cover": f"+£{breakdown}" if breakdown else "Not selected",
        }

        return days, breakdown_dict, total

    def _update_price_preview(self):
        """Refresh the live price preview label."""
        _, _, total = self._calculate_total()
        self.price_preview_lbl.config(text=f"£{total:.2f}")

    # ── Validation ────────────────────────────────────────────────────────

    def _validate(self):
        """
        Validate all mandatory form fields.
        Returns (True, None) if valid, (False, error_message) otherwise.
        """
        name    = self.first_name_var.get().strip()
        surname = self.surname_var.get().strip()
        address = self.address_var.get().strip()
        age_str = self.age_var.get().strip()

        if not name:
            return False, "Customer First Name is required."
        if not re.match(r"^[A-Za-z\-']{1,50}$", name):
            return False, "First name must contain only letters (max 50 chars)."

        if not surname:
            return False, "Customer Surname is required."
        if not re.match(r"^[A-Za-z\-']{1,50}$", surname):
            return False, "Surname must contain only letters (max 50 chars)."

        if not address:
            return False, "Customer Address is required."
        if len(address) < 5:
            return False, "Please enter a valid full address."

        if not age_str:
            return False, "Customer Age is required."
        try:
            age = int(age_str)
            if age < 18 or age > 100:
                return False, "Customer must be aged 18–100 to rent a car."
        except ValueError:
            return False, "Age must be a whole number."

        if self.licence_var.get() == "No":
            return False, "⛔  Booking cannot proceed without a valid driving licence."

        try:
            days = int(self.days_var.get())
            if days < 1 or days > 28:
                return False, "Number of days must be between 1 and 28."
        except (ValueError, tk.TclError):
            return False, "Number of days must be a valid integer."

        return True, None

    # ── Actions ───────────────────────────────────────────────────────────

    def _confirm_booking(self):
        """Validate inputs and show the summary confirmation dialog."""
        ok, err = self._validate()
        if not ok:
            messagebox.showerror("Validation Error", err, parent=self)
            return

        days, price_breakdown, total = self._calculate_total()

        # Build confirmation summary text
        summary_lines = [
            f"  Customer    : {self.first_name_var.get().strip()} {self.surname_var.get().strip()}",
            f"  Address     : {self.address_var.get().strip()}",
            f"  Age         : {self.age_var.get().strip()}",
            f"  Licence     : {self.licence_var.get()}",
            "─" * 42,
            f"  Car Type    : {self.car_type_var.get()}",
            f"  Fuel        : {self.fuel_var.get()}",
            f"  Days        : {days}",
            "─" * 42,
            "  PRICE BREAKDOWN:",
        ]
        for k, v in price_breakdown.items():
            summary_lines.append(f"    {k:<22}: {v}")
        summary_lines += [
            "─" * 42,
            f"  TOTAL PRICE : £{total:.2f}",
        ]

        summary = "\n".join(summary_lines)

        # Confirmation dialog
        confirm = messagebox.askyesno(
            "Confirm Booking",
            f"Please review the booking details:\n\n{summary}\n\n"
            "Click YES to save this booking, NO to go back and edit.",
            parent=self
        )

        if confirm:
            self._save_booking(days, total)

    def _save_booking(self, days, total):
        """Save the validated booking to the global bookings list and JSON file."""
        # Generate simple sequential booking ID
        new_id = f"WC{len(bookings) + 1:04d}"

        record = {
            "id":          new_id,
            "first_name":  self.first_name_var.get().strip(),
            "surname":     self.surname_var.get().strip(),
            "address":     self.address_var.get().strip(),
            "age":         int(self.age_var.get().strip()),
            "licence":     self.licence_var.get(),
            "days":        days,
            "car_type":    self.car_type_var.get(),
            "fuel_type":   self.fuel_var.get(),
            "mileage":     self.mileage_var.get(),
            "breakdown":   self.breakdown_var.get(),
            "total_price": total,
            "status":      "Active",
            "created_at":  datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        bookings.append(record)
        save_bookings(bookings)

        messagebox.showinfo(
            "Booking Saved",
            f"✅  Booking {new_id} has been saved successfully!\n\n"
            f"Customer: {record['first_name']} {record['surname']}\n"
            f"Total: £{total:.2f}",
            parent=self
        )
        self._clear_form()
        self.controller.show_dashboard()   # return to refreshed dashboard

    def _clear_form(self):
        """Reset all form fields to default values."""
        self.first_name_var.set("")
        self.surname_var.set("")
        self.address_var.set("")
        self.age_var.set("")
        self.licence_var.set("Yes")
        self.days_var.set(1)
        self.car_type_var.set("City Car")
        self.fuel_var.set("Petrol")
        self.mileage_var.set(False)
        self.breakdown_var.set(False)
        self._update_price_preview()


# ─────────────────────────────────────────────────────────────────────────────
#  VIEW BOOKINGS FRAME
# ─────────────────────────────────────────────────────────────────────────────

class ViewBookingsFrame(tk.Frame):
    """
    Displays all current bookings in a searchable, scrollable table.
    Double-click a booking to view full details.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, bg=C["bg_dark"])
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=C["bg_mid"], padx=20, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="📋  All Bookings",
                 font=FONT_TITLE, fg=C["accent"],
                 bg=C["bg_mid"]).pack(side="left")
        make_button(header, "⬅  Dashboard",
                    self.controller.show_dashboard,
                    bg=C["bg_card"], fg=C["text_main"],
                    width=14).pack(side="right")

        # Search bar
        search_row = tk.Frame(self, bg=C["bg_dark"], padx=20, pady=10)
        search_row.pack(fill="x")
        tk.Label(search_row, text="🔍  Search:",
                 font=FONT_BODY, fg=C["text_dim"],
                 bg=C["bg_dark"]).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._refresh_table())
        make_entry(search_row, textvariable=self.search_var, width=30).pack(
            side="left", padx=8)

        # Treeview table
        cols = ("ID", "Name", "Car Type", "Fuel", "Days", "Total", "Status", "Date")
        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                 style="Dark.Treeview")

        col_widths = [70, 150, 110, 110, 50, 80, 70, 130]
        for col, w in zip(cols, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=20, pady=8)
        self.tree.bind("<Double-1>", self._view_detail)

        # Total count label
        self.count_lbl = tk.Label(self, text="",
                                  font=FONT_SMALL, fg=C["text_dim"],
                                  bg=C["bg_dark"])
        self.count_lbl.pack(anchor="e", padx=20, pady=4)

        self._refresh_table()

    def _refresh_table(self):
        """Populate / filter the Treeview with current bookings."""
        query = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())

        shown = 0
        for b in reversed(bookings):
            name = f"{b.get('first_name','')} {b.get('surname','')}".lower()
            if query and query not in name and query not in b.get("id","").lower():
                continue
            full_name = f"{b.get('first_name','')} {b.get('surname','')}"
            self.tree.insert("", "end", iid=b["id"], values=(
                b.get("id", ""),
                full_name,
                b.get("car_type", ""),
                b.get("fuel_type", ""),
                b.get("days", ""),
                f"£{b.get('total_price', 0):.2f}",
                b.get("status", "Active"),
                b.get("created_at", ""),
            ))
            shown += 1

        self.count_lbl.config(text=f"Showing {shown} of {len(bookings)} bookings")

    def _view_detail(self, event):
        """Show full booking detail on double-click."""
        sel = self.tree.focus()
        if not sel:
            return
        booking = next((b for b in bookings if b["id"] == sel), None)
        if not booking:
            return

        detail = (
            f"Booking ID  : {booking['id']}\n"
            f"Name        : {booking['first_name']} {booking['surname']}\n"
            f"Address     : {booking['address']}\n"
            f"Age         : {booking['age']}\n"
            f"Licence     : {booking['licence']}\n"
            f"─────────────────────────────\n"
            f"Car Type    : {booking['car_type']}\n"
            f"Fuel Type   : {booking['fuel_type']}\n"
            f"Days        : {booking['days']}\n"
            f"Mileage     : {'Yes' if booking['mileage'] else 'No'}\n"
            f"Breakdown   : {'Yes' if booking['breakdown'] else 'No'}\n"
            f"─────────────────────────────\n"
            f"Total Price : £{booking['total_price']:.2f}\n"
            f"Status      : {booking['status']}\n"
            f"Created     : {booking['created_at']}"
        )
        messagebox.showinfo(f"Booking {sel}", detail, parent=self)

    def refresh(self):
        """Public refresh called when frame is switched to."""
        self._refresh_table()


# ─────────────────────────────────────────────────────────────────────────────
#  UPDATE BOOKING FRAME
# ─────────────────────────────────────────────────────────────────────────────

class UpdateBookingFrame(tk.Frame):
    """
    Allows staff to search for a booking by ID and edit its details.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, bg=C["bg_dark"])
        self.controller = controller
        self.current_booking = None
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=C["bg_mid"], padx=20, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="✏️  Update Booking",
                 font=FONT_TITLE, fg=C["accent"],
                 bg=C["bg_mid"]).pack(side="left")
        make_button(header, "⬅  Dashboard",
                    self.controller.show_dashboard,
                    bg=C["bg_card"], fg=C["text_main"],
                    width=14).pack(side="right")

        # Search area
        search_panel = tk.Frame(self, bg=C["bg_mid"], padx=20, pady=16)
        search_panel.pack(fill="x", padx=20, pady=12)

        tk.Label(search_panel, text="Enter Booking ID to update:",
                 font=FONT_SUBHEAD, fg=C["text_main"],
                 bg=C["bg_mid"]).pack(anchor="w")

        row = tk.Frame(search_panel, bg=C["bg_mid"])
        row.pack(fill="x", pady=8)

        self.search_id_var = tk.StringVar()
        make_entry(row, textvariable=self.search_id_var, width=20).pack(side="left")
        make_button(row, "🔍  Find",
                    self._find_booking, width=10).pack(side="left", padx=8)

        self.find_err = tk.Label(search_panel, text="",
                                 font=FONT_SMALL, fg=C["danger"],
                                 bg=C["bg_mid"])
        self.find_err.pack(anchor="w")

        # Editable fields (initially hidden)
        self.edit_frame = tk.Frame(self, bg=C["bg_mid"], padx=20, pady=16)

        self.u_days_var   = tk.IntVar(value=1)
        self.u_car_var    = tk.StringVar(value="City Car")
        self.u_fuel_var   = tk.StringVar(value="Petrol")
        self.u_mileage    = tk.BooleanVar(value=False)
        self.u_breakdown  = tk.BooleanVar(value=False)
        self.u_status_var = tk.StringVar(value="Active")

        fields = [
            ("Number of Days (1–28)", None, "spinbox"),
            ("Car Type",   None, "option_car"),
            ("Fuel Type",  None, "option_fuel"),
            ("Status",     None, "option_status"),
        ]

        tk.Label(self.edit_frame, text="Editable Fields:",
                 font=FONT_SUBHEAD, fg=C["accent2"],
                 bg=C["bg_mid"]).pack(anchor="w", pady=(0, 8))

        # Days spinbox
        r1 = tk.Frame(self.edit_frame, bg=C["bg_mid"])
        r1.pack(fill="x", pady=4)
        tk.Label(r1, text="Number of Days (1–28)",
                 font=FONT_BODY, fg=C["text_main"],
                 bg=C["bg_mid"], width=24, anchor="w").pack(side="left")
        tk.Spinbox(r1, from_=1, to=28, textvariable=self.u_days_var,
                   width=8, bg=C["entry_bg"], fg=C["text_main"],
                   relief="flat", font=FONT_BODY).pack(side="left", padx=8)

        # Car type dropdown
        r2 = tk.Frame(self.edit_frame, bg=C["bg_mid"])
        r2.pack(fill="x", pady=4)
        tk.Label(r2, text="Car Type", font=FONT_BODY,
                 fg=C["text_main"], bg=C["bg_mid"],
                 width=24, anchor="w").pack(side="left")
        m2 = tk.OptionMenu(r2, self.u_car_var, *CAR_PRICES.keys())
        m2.config(bg=C["entry_bg"], fg=C["text_main"], relief="flat",
                  font=FONT_BODY, width=18)
        m2["menu"].config(bg=C["bg_card"], fg=C["text_main"], font=FONT_BODY)
        m2.pack(side="left", padx=8)

        # Fuel type dropdown
        r3 = tk.Frame(self.edit_frame, bg=C["bg_mid"])
        r3.pack(fill="x", pady=4)
        tk.Label(r3, text="Fuel Type", font=FONT_BODY,
                 fg=C["text_main"], bg=C["bg_mid"],
                 width=24, anchor="w").pack(side="left")
        m3 = tk.OptionMenu(r3, self.u_fuel_var, *FUEL_PRICES.keys())
        m3.config(bg=C["entry_bg"], fg=C["text_main"], relief="flat",
                  font=FONT_BODY, width=18)
        m3["menu"].config(bg=C["bg_card"], fg=C["text_main"], font=FONT_BODY)
        m3.pack(side="left", padx=8)

        # Mileage / Breakdown checkboxes
        r4 = tk.Frame(self.edit_frame, bg=C["bg_mid"])
        r4.pack(fill="x", pady=4)
        tk.Checkbutton(r4, text="Unlimited Mileage (+£10/day)",
                       variable=self.u_mileage, bg=C["bg_mid"],
                       fg=C["text_main"], selectcolor=C["entry_bg"],
                       font=FONT_BODY).pack(side="left", padx=(0, 20))
        tk.Checkbutton(r4, text="Breakdown Cover (+£2/day)",
                       variable=self.u_breakdown, bg=C["bg_mid"],
                       fg=C["text_main"], selectcolor=C["entry_bg"],
                       font=FONT_BODY).pack(side="left")

        # Status dropdown
        r5 = tk.Frame(self.edit_frame, bg=C["bg_mid"])
        r5.pack(fill="x", pady=4)
        tk.Label(r5, text="Status", font=FONT_BODY,
                 fg=C["text_main"], bg=C["bg_mid"],
                 width=24, anchor="w").pack(side="left")
        m5 = tk.OptionMenu(r5, self.u_status_var, "Active", "Completed", "Cancelled")
        m5.config(bg=C["entry_bg"], fg=C["text_main"], relief="flat",
                  font=FONT_BODY, width=18)
        m5["menu"].config(bg=C["bg_card"], fg=C["text_main"], font=FONT_BODY)
        m5.pack(side="left", padx=8)

        # Save button
        make_button(self.edit_frame, "💾  Save Changes",
                    self._save_update, bg=C["success"],
                    fg=C["white"], width=18).pack(pady=16)

    def _find_booking(self):
        """Find booking by ID and populate edit fields."""
        bid = self.search_id_var.get().strip().upper()
        booking = next((b for b in bookings if b["id"] == bid), None)

        if not booking:
            self.find_err.config(text=f"Booking ID '{bid}' not found.")
            self.edit_frame.pack_forget()
            self.current_booking = None
            return

        self.find_err.config(text="")
        self.current_booking = booking

        # Pre-fill editable fields with current values
        self.u_days_var.set(booking["days"])
        self.u_car_var.set(booking["car_type"])
        self.u_fuel_var.set(booking["fuel_type"])
        self.u_mileage.set(booking.get("mileage", False))
        self.u_breakdown.set(booking.get("breakdown", False))
        self.u_status_var.set(booking.get("status", "Active"))

        self.edit_frame.pack(fill="x", padx=20, pady=4)

    def _save_update(self):
        """Recalculate price and save updated booking fields."""
        if not self.current_booking:
            return

        days = int(self.u_days_var.get())
        if not (1 <= days <= 28):
            messagebox.showerror("Validation", "Days must be 1–28.", parent=self)
            return

        # Recalculate total
        base  = days * BASE_RATE
        car   = CAR_PRICES.get(self.u_car_var.get(), 0)
        fuel  = FUEL_PRICES.get(self.u_fuel_var.get(), 0)
        mil   = days * MILEAGE_RATE  if self.u_mileage.get() else 0
        brk   = days * BREAKDOWN_RATE if self.u_breakdown.get() else 0
        total = base + car + fuel + mil + brk

        # Update the booking record in-place
        self.current_booking.update({
            "days":        days,
            "car_type":    self.u_car_var.get(),
            "fuel_type":   self.u_fuel_var.get(),
            "mileage":     self.u_mileage.get(),
            "breakdown":   self.u_breakdown.get(),
            "status":      self.u_status_var.get(),
            "total_price": total,
        })

        save_bookings(bookings)

        messagebox.showinfo(
            "Updated",
            f"✅  Booking {self.current_booking['id']} updated.\n"
            f"New total: £{total:.2f}",
            parent=self
        )
        self.edit_frame.pack_forget()
        self.search_id_var.set("")
        self.current_booking = None
        self.controller.show_dashboard()

    def refresh(self):
        """Reset frame state when navigated to."""
        self.search_id_var.set("")
        self.find_err.config(text="")
        self.current_booking = None
        self.edit_frame.pack_forget()


# ─────────────────────────────────────────────────────────────────────────────
#  DELETE BOOKING FRAME
# ─────────────────────────────────────────────────────────────────────────────

class DeleteBookingFrame(tk.Frame):
    """
    Allows staff to search for and permanently delete a booking by ID.
    Requires a confirmation dialog before deletion.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, bg=C["bg_dark"])
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=C["bg_mid"], padx=20, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="🗑️  Delete Booking",
                 font=FONT_TITLE, fg=C["danger"],
                 bg=C["bg_mid"]).pack(side="left")
        make_button(header, "⬅  Dashboard",
                    self.controller.show_dashboard,
                    bg=C["bg_card"], fg=C["text_main"],
                    width=14).pack(side="right")

        # Search panel
        panel = tk.Frame(self, bg=C["bg_mid"], padx=20, pady=20)
        panel.pack(fill="x", padx=20, pady=20)

        tk.Label(panel, text="Enter Booking ID to delete:",
                 font=FONT_SUBHEAD, fg=C["text_main"],
                 bg=C["bg_mid"]).pack(anchor="w")

        row = tk.Frame(panel, bg=C["bg_mid"])
        row.pack(fill="x", pady=8)

        self.del_id_var = tk.StringVar()
        make_entry(row, textvariable=self.del_id_var, width=20).pack(side="left")
        make_button(row, "🔍  Find",
                    self._find_booking, width=10).pack(side="left", padx=8)

        self.find_err = tk.Label(panel, text="",
                                 font=FONT_SMALL, fg=C["danger"],
                                 bg=C["bg_mid"])
        self.find_err.pack(anchor="w")

        # Detail preview (shown after finding)
        self.preview_lbl = tk.Label(panel, text="",
                                    font=FONT_MONO, fg=C["text_main"],
                                    bg=C["bg_card"], justify="left",
                                    padx=12, pady=12)
        self.delete_btn = make_button(panel, "🗑️  Confirm Delete",
                                      self._confirm_delete,
                                      bg=C["danger"], fg=C["white"], width=20)

        self.found_booking = None

    def _find_booking(self):
        """Find and preview a booking before deletion."""
        bid = self.del_id_var.get().strip().upper()
        booking = next((b for b in bookings if b["id"] == bid), None)

        if not booking:
            self.find_err.config(text=f"Booking ID '{bid}' not found.")
            self.preview_lbl.pack_forget()
            self.delete_btn.pack_forget()
            self.found_booking = None
            return

        self.find_err.config(text="")
        self.found_booking = booking

        preview = (
            f"  ID     : {booking['id']}\n"
            f"  Name   : {booking['first_name']} {booking['surname']}\n"
            f"  Car    : {booking['car_type']}  |  Fuel: {booking['fuel_type']}\n"
            f"  Days   : {booking['days']}  |  Total: £{booking['total_price']:.2f}\n"
            f"  Status : {booking.get('status','Active')}"
        )
        self.preview_lbl.config(text=preview)
        self.preview_lbl.pack(fill="x", pady=(12, 6))
        self.delete_btn.pack(pady=4)

    def _confirm_delete(self):
        """Ask for confirmation then delete the booking."""
        if not self.found_booking:
            return

        bid  = self.found_booking["id"]
        name = f"{self.found_booking['first_name']} {self.found_booking['surname']}"

        ok = messagebox.askyesno(
            "Confirm Deletion",
            f"⚠️  Are you sure you want to permanently delete booking {bid}?\n\n"
            f"Customer: {name}\nThis action cannot be undone.",
            parent=self
        )
        if not ok:
            return

        bookings.remove(self.found_booking)
        save_bookings(bookings)

        messagebox.showinfo("Deleted",
                            f"✅  Booking {bid} has been deleted.",
                            parent=self)

        # Reset UI
        self.preview_lbl.pack_forget()
        self.delete_btn.pack_forget()
        self.del_id_var.set("")
        self.found_booking = None
        self.controller.show_dashboard()

    def refresh(self):
        """Reset state when navigated to."""
        self.del_id_var.set("")
        self.find_err.config(text="")
        self.preview_lbl.pack_forget()
        self.delete_btn.pack_forget()
        self.found_booking = None


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN APPLICATION CONTROLLER
# ─────────────────────────────────────────────────────────────────────────────

class WeAreCarsApp(tk.Tk):
    """
    Root application window.
    Manages frame switching (login ↔ dashboard ↔ add/view/update/delete).
    Uses a splash screen on startup.
    """

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("WeAreCars – Car Rental Management System")
        self.geometry("1100x720")
        self.minsize(900, 620)
        self.configure(bg=C["bg_dark"])

        # Try to set an icon (silently skip if unavailable)
        try:
            self.iconbitmap("wearecars.ico")
        except Exception:
            pass

        # Hide main window until splash is done
        self.withdraw()

        # Frame container
        self.container = tk.Frame(self, bg=C["bg_dark"])
        self.container.pack(fill="both", expand=True)

        # Instantiate all frames (lazy – only shown when needed)
        self.frames = {}
        self._init_frames()

        # Show splash screen first (3 seconds)
        SplashScreen(self, self._on_splash_done)

    def _init_frames(self):
        """Create all application frames and store in dict."""
        self.frames["login"]   = LoginFrame(self.container,
                                            on_login_success=self.show_dashboard)
        self.frames["dashboard"] = DashboardFrame(self.container, self)
        self.frames["add"]       = AddBookingFrame(self.container, self)
        self.frames["view"]      = ViewBookingsFrame(self.container, self)
        self.frames["update"]    = UpdateBookingFrame(self.container, self)
        self.frames["delete"]    = DeleteBookingFrame(self.container, self)

        # Pack all frames in the container (only one visible at a time)
        for frame in self.frames.values():
            frame.place(relwidth=1, relheight=1)

    def _show_frame(self, name):
        """Bring the named frame to the front."""
        frame = self.frames[name]
        frame.tkraise()
        # Refresh data-driven frames when shown
        if hasattr(frame, "refresh"):
            frame.refresh()

    def _on_splash_done(self):
        """Called when splash screen closes – show main window at login."""
        self.deiconify()   # make main window visible
        self._show_frame("login")

    # ── Navigation methods (called by buttons) ────────────────────────────

    def show_login(self):
        """Navigate to login frame (also used for logout)."""
        self._show_frame("login")

    def show_dashboard(self):
        """Navigate to the main dashboard."""
        self._show_frame("dashboard")

    def show_add_booking(self):
        """Navigate to the Add Booking form."""
        self._show_frame("add")

    def show_view_bookings(self):
        """Navigate to the View Bookings table."""
        self._show_frame("view")

    def show_update_booking(self):
        """Navigate to the Update Booking form."""
        self._show_frame("update")

    def show_delete_booking(self):
        """Navigate to the Delete Booking form."""
        self._show_frame("delete")


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = WeAreCarsApp()
    app.mainloop()
