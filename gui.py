"""
GUI for Civic Transparency Toolkit.
Built with CustomTkinter for a modern desktop look.
"""

import logging
import os
import re
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

logger = logging.getLogger(__name__)
from datetime import datetime

try:
    import customtkinter as ctk
except ImportError:
    raise ImportError(
        "customtkinter is required. Install with: pip install customtkinter"
    )

from config import load_config, save_config, import_sources_from_file, auto_populate_config_from_sources, _log_debug
from pipeline import (
    PipelineRunner, LANES, PROMPT_NAMES, PROMPT_DESCRIPTIONS, PROMPT_FILES,
    load_prompt_text, substitute_variables,
)


# ---------------------------------------------------------------------------
# Color palette — Google Material Design 3 light theme
# Based on M3 baseline blue primary with proper surface elevation tones
# ---------------------------------------------------------------------------
COLORS = {
    # Surfaces (M3 elevation hierarchy)
    "bg_dark": "#FEF7FF",        # M3 surface — very light purple tint
    "bg_sidebar": "#FFFFFF",      # M3 surface container lowest
    "bg_card": "#E8DEF8",        # M3 secondary container (light purple)
    "output_bg": "#FFFBFE",      # M3 surface — near-white
    "surface_1": "#F3EDF7",      # M3 surface container low
    "surface_2": "#ECE6F0",      # M3 surface container
    "surface_3": "#E8DEF8",      # M3 surface container high

    # Primary (M3 baseline blue-purple)
    "accent": "#6750A4",         # M3 primary
    "accent_hover": "#4F378B",   # M3 primary — pressed state
    "on_primary": "#FFFFFF",     # M3 on-primary (text on primary buttons)

    # Secondary / tonal
    "secondary": "#625B71",      # M3 secondary
    "secondary_container": "#E8DEF8",  # M3 secondary container
    "on_secondary_container": "#1D192B",  # M3 on-secondary-container

    # Text
    "text": "#1C1B1F",           # M3 on-surface
    "text_dim": "#49454F",       # M3 on-surface-variant
    "text_light": "#79747E",     # M3 outline

    # Status
    "success": "#386A20",        # M3 tertiary (green tone)
    "warning": "#7D5700",        # M3 tertiary (amber tone)
    "error": "#B3261E",          # M3 error
    "error_hover": "#8C1D18",    # M3 error — pressed

    # Stage indicators
    "stage_pending": "#CAC4D0",  # M3 outline-variant
    "stage_active": "#6750A4",   # M3 primary
    "stage_done": "#386A20",     # M3 green/tertiary

    # Borders & outlines
    "border": "#CAC4D0",         # M3 outline-variant
    "outline": "#79747E",        # M3 outline
}

# M3 corner radius values
RADIUS = {
    "none": 0,
    "small": 8,       # M3 small — chips, compact elements
    "medium": 12,     # M3 medium — cards, dialogs
    "large": 16,      # M3 large — FABs, sheets
    "full": 20,       # M3 full — buttons (pill shape)
}

# Human-readable source type labels ↔ internal A/B/C codes
TYPE_LABELS = {"A": "Official Record", "B": "News", "C": "Community"}
TYPE_CODES = {v: k for k, v in TYPE_LABELS.items()}  # reverse lookup


def _add_context_menu(widget):
    """Add a right-click Copy / Paste / Select All menu to any text widget."""
    menu = tk.Menu(widget, tearoff=0)

    # Detect the inner text widget — CTkTextbox wraps a tk.Text,
    # CTkEntry wraps a tk.Entry; both live in ._textbox or ._entry
    inner = getattr(widget, "_textbox", None) or getattr(widget, "_entry", None) or widget

    def _copy():
        try:
            widget.clipboard_clear()
            text = inner.selection_get()
            widget.clipboard_append(text)
        except tk.TclError:
            pass  # nothing selected

    def _paste():
        try:
            # Focus the inner widget first so the paste targets it
            inner.focus_set()
            # Generate the same <<Paste>> event that Ctrl+V uses —
            # this lets CustomTkinter handle the insert properly
            inner.event_generate("<<Paste>>")
        except tk.TclError:
            pass

    def _select_all():
        try:
            inner.tag_add("sel", "1.0", "end")  # CTkTextbox (Text widget)
        except Exception:
            try:
                inner.select_range(0, "end")  # CTkEntry (Entry widget)
            except Exception:
                pass

    def _cut():
        try:
            inner.focus_set()
            inner.event_generate("<<Cut>>")
        except tk.TclError:
            pass

    menu.add_command(label="Cut", command=_cut)
    menu.add_command(label="Copy", command=_copy)
    menu.add_command(label="Paste", command=_paste)
    menu.add_separator()
    menu.add_command(label="Select All", command=_select_all)

    def _show_menu(event):
        menu.tk_popup(event.x_root, event.y_root)

    # Bind to both the outer CTk widget and the inner tk widget
    inner.bind("<Button-3>", _show_menu)
    widget.bind("<Button-3>", _show_menu)


class CivicTransparencyApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Civic Transparency Toolkit")
        self.geometry("1050x700")
        self.minsize(900, 600)

        ctk.set_default_color_theme("blue")

        # State
        self.config_data = load_config()

        # Apply saved theme preference (default to light)
        theme = self.config_data.get("theme", "light")
        if theme not in ("light", "dark"):
            theme = "light"
        ctk.set_appearance_mode(theme)
        self.runner = None
        self.is_running = False
        self.current_stage = None
        self.stage_statuses = {}  # {prompt_num: "pending" | "running" | "done" | "error"}
        self.stage_outputs = {}
        self._approval_event = threading.Event()
        self._approved = False
        self._selected_single_step = None  # Which step is picked in "Run a Single Step" mode
        self._dot_animation_id = None      # after() ID for the pulsing dot animation
        self._dot_phase = 0                # Current phase (0-2) of the three-dot pulse
        self._md_styled_up_to = 0          # Last line number already styled by incremental pass

        # Build UI
        self._build_layout()
        self._check_first_run()

    # -----------------------------------------------------------------------
    # Layout
    # -----------------------------------------------------------------------
    def _build_layout(self):
        """Build the main 3-panel layout."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Left sidebar — M3 navigation rail / drawer ---
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0,
                                     fg_color=COLORS["surface_1"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self._build_sidebar()

        # --- Main content area — M3 surface ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=0,
                                        fg_color=COLORS["bg_dark"])
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self._build_main_area()

    def _build_sidebar(self):
        """Build the left sidebar with Material Design 3 navigation."""
        # App title — M3 headline small
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(24, 6))

        ctk.CTkLabel(
            title_frame, text="Civic Transparency",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_frame, text="Toolkit",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")

        city = self.config_data.get("city_name", "")
        state = self.config_data.get("state", "")
        city_text = f"{city}, {state}" if city else "No city configured"
        self.city_label = ctk.CTkLabel(
            title_frame, text=city_text,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_dim"],
        )
        self.city_label.pack(anchor="w", pady=(4, 0))

        # Divider — M3 divider
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(
            fill="x", padx=20, pady=16
        )

        # Lane selector — M3 label large
        ctk.CTkLabel(
            self.sidebar, text="What would you like to do?",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=22)

        # Initialize with display name (not internal key) so _get_lane_key() works immediately
        _init_lane_key = self.config_data.get("last_lane", "daily_production")
        _init_display = LANES.get(_init_lane_key, LANES["daily_production"])["name"]
        self.lane_var = ctk.StringVar(value=_init_display)
        self.lane_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=[LANES[k]["name"] for k in LANES],
            variable=self.lane_var,
            command=self._on_lane_change,
            width=236,
            height=40,
            corner_radius=RADIUS["small"],
            fg_color=COLORS["secondary_container"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            text_color=COLORS["on_secondary_container"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=13),
            dropdown_fg_color=COLORS["bg_sidebar"],
            dropdown_hover_color=COLORS["surface_2"],
            dropdown_text_color=COLORS["text"],
        )
        self.lane_menu.pack(padx=22, pady=(6, 12))

        # Progress / stage area — M3 switch-like toggle
        self.detail_visible = ctk.BooleanVar(value=False)
        detail_toggle = ctk.CTkCheckBox(
            self.sidebar, text="Show step-by-step details",
            variable=self.detail_visible,
            command=self._toggle_stage_detail,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLORS["text_dim"],
            checkbox_width=18, checkbox_height=18,
            border_width=2,
            border_color=COLORS["outline"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["surface_2"],
            corner_radius=4,
        )
        detail_toggle.pack(anchor="w", padx=24, pady=(6, 6))

        # Simple progress summary (shown by default)
        self.simple_progress_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.simple_progress_frame.pack(fill="x", padx=22, pady=(6, 0))
        self.simple_progress_label = ctk.CTkLabel(
            self.simple_progress_frame, text="Ready to go",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_dim"],
            wraplength=220, justify="left",
        )
        self.simple_progress_label.pack(anchor="w")

        # Detailed stage list (hidden by default)
        self.stages_frame = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent",
            corner_radius=RADIUS["small"],
        )
        # Don't pack yet — shown via toggle

        self.stage_buttons = {}
        self._update_stage_list()

        # Spacer — saved as instance var so _toggle_stage_detail can pack before it
        self._sidebar_spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self._sidebar_spacer.pack(fill="both", expand=True)

        # Bottom buttons — M3 navigation area
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(
            fill="x", padx=20, pady=(12, 8)
        )

        btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkLabel(
            btn_frame, text="Setup",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=COLORS["text_light"],
        ).pack(anchor="w", padx=6, pady=(0, 6))

        for text, cmd in [
            ("Settings", self._open_settings),
            ("City & Sources", self._open_city_config),
            ("Import Sources", self._import_sources),
            ("Export Template", self._export_source_template),
        ]:
            ctk.CTkButton(
                btn_frame, text=text,
                command=cmd,
                fg_color="transparent",
                hover_color=COLORS["surface_2"],
                text_color=COLORS["text"],
                height=36,
                corner_radius=RADIUS["full"],
                font=ctk.CTkFont(family="Segoe UI", size=13),
                border_width=1,
                border_color=COLORS["border"],
            ).pack(fill="x", pady=2)

    def _toggle_stage_detail(self):
        """Toggle between simple progress summary and detailed stage list."""
        if self.detail_visible.get():
            self.simple_progress_frame.pack_forget()
            # Pack stages_frame right after the checkbox (before the spacer)
            self.stages_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10),
                                   before=self._sidebar_spacer)
        else:
            self.stages_frame.pack_forget()
            self.simple_progress_frame.pack(fill="x", padx=20, pady=(5, 0),
                                            before=self._sidebar_spacer)

    def _build_main_area(self):
        """Build the main content area with M3-styled toolbar, output, and controls."""
        # Row layout: 0=toolbar, 1=topic (conditional), 2=output, 3=status, 4=approve
        self.main_frame.grid_rowconfigure(2, weight=1)

        # Toolbar — M3 top app bar style
        toolbar = ctk.CTkFrame(self.main_frame, height=60, fg_color=COLORS["surface_1"],
                                corner_radius=0)
        toolbar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        toolbar.grid_columnconfigure(3, weight=1)

        # M3 filled button (primary action)
        self.run_btn = ctk.CTkButton(
            toolbar, text="Go",
            command=self._run_complete,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["on_primary"],
            height=40, width=120,
            corner_radius=RADIUS["full"],
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
        )
        self.run_btn.grid(row=0, column=0, padx=(16, 6), pady=10)

        # M3 tonal button (secondary action)
        self.step_btn = ctk.CTkButton(
            toolbar, text="Go Step-by-Step",
            command=self._run_step_by_step,
            fg_color=COLORS["secondary_container"],
            hover_color=COLORS["surface_2"],
            text_color=COLORS["on_secondary_container"],
            height=40, width=160,
            corner_radius=RADIUS["full"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self.step_btn.grid(row=0, column=1, padx=6, pady=10)

        # M3 error-filled button
        self.cancel_btn = ctk.CTkButton(
            toolbar, text="Stop",
            command=self._cancel_run,
            fg_color=COLORS["error"],
            hover_color=COLORS["error_hover"],
            text_color="#FFFFFF",
            height=40, width=80,
            corner_radius=RADIUS["full"],
            state="disabled",
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self.cancel_btn.grid(row=0, column=2, padx=6, pady=10, sticky="w")

        # M3 outlined button
        self.save_btn = ctk.CTkButton(
            toolbar, text="Save",
            command=self._save_output,
            fg_color="transparent",
            hover_color=COLORS["surface_2"],
            text_color=COLORS["accent"],
            height=40, width=80,
            corner_radius=RADIUS["full"],
            border_width=1,
            border_color=COLORS["outline"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self.save_btn.grid(row=0, column=4, padx=(6, 16), pady=10, sticky="e")

        # Topic input — M3 text field style
        self.topic_frame = ctk.CTkFrame(self.main_frame, fg_color=COLORS["surface_1"],
                                         corner_radius=0, height=56)
        ctk.CTkLabel(self.topic_frame,
                      text="What topic should the toolkit research and write about?",
                      text_color=COLORS["text_dim"],
                      font=ctk.CTkFont(family="Segoe UI", size=13)).pack(anchor="w", padx=16, pady=(10, 0))
        self.topic_entry = ctk.CTkEntry(
            self.topic_frame, width=600,
            placeholder_text='e.g., "What\'s happening with the new development on Main Street?"',
            fg_color=COLORS["output_bg"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(family="Segoe UI", size=14),
            height=40,
            corner_radius=RADIUS["small"],
            border_width=1,
            border_color=COLORS["outline"],
        )
        self.topic_entry.pack(anchor="w", padx=16, pady=(4, 12))
        _add_context_menu(self.topic_entry)
        # Don't grid topic_frame yet — shown via _on_lane_change

        # Story input — multi-line text area for steps that audit/rewrite existing content
        # Steps 2, 4, 5, 7, 8 need story text pasted in when run standalone
        self.story_input_frame = ctk.CTkFrame(self.main_frame, fg_color=COLORS["surface_1"],
                                               corner_radius=0)
        ctk.CTkLabel(self.story_input_frame,
                      text="Paste the story or content you want this step to process:",
                      text_color=COLORS["text_dim"],
                      font=ctk.CTkFont(family="Segoe UI", size=13)).pack(anchor="w", padx=16, pady=(10, 0))
        self.story_input_text = ctk.CTkTextbox(
            self.story_input_frame, height=160,
            fg_color=COLORS["output_bg"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
            wrap="word",
            corner_radius=RADIUS["small"],
            border_width=1,
            border_color=COLORS["outline"],
        )
        self.story_input_text.pack(fill="x", padx=16, pady=(4, 12))
        _add_context_menu(self.story_input_text)
        # Don't grid story_input_frame yet — shown via _select_single_step

        # Which steps need which input type when run standalone
        self._steps_needing_story = {2, 4, 5, 6, 7, 8}  # need previous_output pasted in
        self._steps_needing_topic = {9}                    # need a topic typed in

        # Output area — M3 surface container with readable font
        self.output_text = ctk.CTkTextbox(
            self.main_frame,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color=COLORS["output_bg"],
            text_color=COLORS["text"],
            wrap="word",
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=RADIUS["medium"],
        )
        self.output_text.grid(row=2, column=0, sticky="nsew", padx=14, pady=(12, 6))
        _add_context_menu(self.output_text)

        # Markdown-style text tags for rich output rendering
        # CTkTextbox wraps a tk.Text in ._textbox — configure tags there
        inner_text = self.output_text._textbox
        inner_text.tag_configure("md_h1",
            font=("Segoe UI", 16, "bold"),
            foreground=COLORS["accent"],
            spacing1=8, spacing3=4)
        inner_text.tag_configure("md_h2",
            font=("Segoe UI", 15, "bold"),
            foreground=COLORS["accent"],
            spacing1=6, spacing3=3)
        inner_text.tag_configure("md_h3",
            font=("Segoe UI", 14, "bold"),
            foreground=COLORS["secondary"],
            spacing1=4, spacing3=2)
        inner_text.tag_configure("md_bold",
            font=("Segoe UI", 14, "bold"))
        inner_text.tag_configure("md_hr",
            font=("Segoe UI", 2),
            foreground=COLORS["border"],
            spacing1=6, spacing3=6)

        # Live Activity Strip — M3 bottom bar (consolidated status + progress)
        self.activity_strip = ctk.CTkFrame(
            self.main_frame, height=66, fg_color=COLORS["surface_1"],
            corner_radius=0,
        )
        self.activity_strip.grid(row=3, column=0, sticky="ew", padx=0, pady=0)
        self.activity_strip.grid_columnconfigure(0, weight=1)
        self.activity_strip.grid_rowconfigure(0, weight=0)
        self.activity_strip.grid_rowconfigure(1, weight=0)

        # Top row: status text (left) + step counter (right)
        top_row = ctk.CTkFrame(self.activity_strip, fg_color="transparent")
        top_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(8, 0))
        top_row.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            top_row, text="Ready",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS["text_dim"],
            anchor="w",
        )
        self.status_label.grid(row=0, column=0, sticky="w")

        # Animated dots — three circles that pulse during work
        self.dot_label = ctk.CTkLabel(
            top_row, text="",
            font=ctk.CTkFont(family="Segoe UI", size=16),
            text_color=COLORS["accent"],
            anchor="w", width=60,
        )
        self.dot_label.grid(row=0, column=1, padx=(8, 4))

        # Step counter: "Step 2 of 5"
        self.step_counter_label = ctk.CTkLabel(
            top_row, text="",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text_dim"],
            anchor="e",
        )
        self.step_counter_label.grid(row=0, column=2, sticky="e")

        # Bottom row: progress bar spanning full width
        self.progress_bar = ctk.CTkProgressBar(
            self.activity_strip,
            height=6,
            progress_color=COLORS["accent"],
            fg_color=COLORS["surface_2"],
            corner_radius=3,
        )
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(6, 10))
        self.progress_bar.set(0)

        # Approval button (hidden unless step-by-step) — M3 filled tonal
        self.approve_frame = ctk.CTkFrame(self.main_frame, fg_color=COLORS["surface_1"],
                                           height=56, corner_radius=0)
        self.approve_btn = ctk.CTkButton(
            self.approve_frame, text="Looks Good — Continue",
            command=self._approve_stage,
            fg_color=COLORS["success"],
            text_color="#FFFFFF",
            hover_color="#2D5A18",
            height=44, width=280,
            corner_radius=RADIUS["full"],
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
        )
        self.approve_btn.pack(pady=8)
        # Don't grid approve_frame yet — shown only in step-by-step mode

    # -----------------------------------------------------------------------
    # Stage list management
    # -----------------------------------------------------------------------
    def _update_stage_list(self):
        """Rebuild the stage button list based on current lane."""
        for widget in self.stages_frame.winfo_children():
            widget.destroy()
        self.stage_buttons.clear()

        lane_key = self._get_lane_key()
        lane = LANES.get(lane_key, LANES["daily_production"])
        stages = lane["stages"]

        if not stages:
            # Single-prompt mode: show all 9
            stages = list(range(1, 10))

        for num in stages:
            status = self.stage_statuses.get(num, "pending")
            btn = self._create_stage_button(num, status)
            btn.pack(fill="x", pady=2, padx=5)
            self.stage_buttons[num] = btn

    # Friendly step descriptions for the simple progress view
    STEP_DESCRIPTIONS = {
        1: "Searching your sources...",
        2: "Writing stories...",
        3: "Looking for hidden patterns...",
        4: "Verifying signals...",
        5: "Checking facts...",
        6: "Checking First Amendment issues...",
        7: "Finishing up your stories...",
        8: "Checking source integrity...",
        9: "Researching and writing...",
    }

    def _update_simple_progress(self, prompt_num=None, status=None):
        """Update the simple one-line progress display."""
        if not prompt_num:
            self.simple_progress_label.configure(text="Ready to go")
            return
        if status == "running":
            desc = self.STEP_DESCRIPTIONS.get(prompt_num, f"Running step {prompt_num}...")
            self.simple_progress_label.configure(text=desc, text_color=COLORS["accent"])
        elif status == "done":
            done_count = sum(1 for s in self.stage_statuses.values() if s == "done")
            lane_key = self._get_lane_key()
            total = len(LANES.get(lane_key, {}).get("stages", []))
            if total and done_count >= total:
                self.simple_progress_label.configure(
                    text="All done! Your stories are ready.",
                    text_color=COLORS["success"])
            else:
                self.simple_progress_label.configure(
                    text=f"Step {done_count} of {total} complete",
                    text_color=COLORS["text_dim"])
        elif status == "error":
            self.simple_progress_label.configure(
                text="Something went wrong. Check the output for details.",
                text_color=COLORS["error"])

    # -------------------------------------------------------------------
    # Live Activity Strip — dot animation + step counter
    # -------------------------------------------------------------------

    def _start_dot_animation(self):
        """Start the pulsing three-dot animation in the activity strip."""
        self._dot_phase = 0
        self._tick_dots()

    def _tick_dots(self):
        """Advance the dot animation by one frame. Cycles: ●○○ → ●●○ → ●●● → repeat."""
        filled = self._dot_phase + 1  # 1, 2, or 3 filled dots
        dots = "●" * filled + "○" * (3 - filled)
        # Space them out for readability
        spaced = "  ".join(dots)
        self.dot_label.configure(text=spaced)
        self._dot_phase = (self._dot_phase + 1) % 3
        self._dot_animation_id = self.after(600, self._tick_dots)

    def _stop_dot_animation(self):
        """Stop the dot animation and clear the dots."""
        if self._dot_animation_id is not None:
            self.after_cancel(self._dot_animation_id)
            self._dot_animation_id = None
        self.dot_label.configure(text="")

    def _update_activity_strip(self, prompt_num=None, status=None, lane_key=None):
        """Update the activity strip status text, dots, and step counter."""
        if not lane_key:
            lane_key = self._get_lane_key()
        stages = LANES.get(lane_key, {}).get("stages", [])
        total = len(stages)

        if not prompt_num:
            # Reset / idle state
            self.status_label.configure(text="Ready", text_color=COLORS["text_dim"])
            self.step_counter_label.configure(text="")
            self._stop_dot_animation()
            self.progress_bar.set(0)
            return

        if status == "running":
            desc = self.STEP_DESCRIPTIONS.get(prompt_num, f"Running step {prompt_num}...")
            self.status_label.configure(text=desc, text_color=COLORS["accent"])
            if total > 0:
                idx = (stages.index(prompt_num) + 1) if prompt_num in stages else 1
                self.step_counter_label.configure(text=f"Step {idx} of {total}")
            else:
                # Single-step mode — no counter needed
                name = PROMPT_NAMES.get(prompt_num, f"Step {prompt_num}")
                self.step_counter_label.configure(text=name)
            # Start animation if not already running
            if self._dot_animation_id is None:
                self._start_dot_animation()

        elif status == "done":
            done_count = sum(1 for s in self.stage_statuses.values() if s == "done")
            if total and done_count >= total:
                self.status_label.configure(
                    text="All done! Your stories are ready.",
                    text_color=COLORS["success"])
                self.step_counter_label.configure(text=f"{total} of {total} complete")
                self._stop_dot_animation()
                self.progress_bar.set(1.0)
            else:
                self.step_counter_label.configure(text=f"{done_count} of {total} complete")

        elif status == "error":
            self.status_label.configure(
                text="Something went wrong — check output above",
                text_color=COLORS["error"])
            self._stop_dot_animation()

    def _create_stage_button(self, prompt_num, status="pending"):
        """Create an M3-styled stage indicator button."""
        indicators = {"pending": "○", "running": "●", "done": "✓", "error": "✕"}
        colors = {
            "pending": COLORS["stage_pending"],
            "running": COLORS["stage_active"],
            "done": COLORS["stage_done"],
            "error": COLORS["error"],
        }
        bg_colors = {
            "pending": "transparent",
            "running": COLORS["surface_2"],
            "done": "transparent",
            "error": "transparent",
        }

        indicator = indicators.get(status, "○")
        color = colors.get(status, COLORS["stage_pending"])
        bg = bg_colors.get(status, "transparent")
        name = PROMPT_NAMES.get(prompt_num, f"Step {prompt_num}")

        btn = ctk.CTkButton(
            self.stages_frame,
            text=f"  {indicator}  {name}",
            anchor="w",
            fg_color=bg,
            hover_color=COLORS["surface_2"],
            text_color=color,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=36,
            corner_radius=RADIUS["full"],
            command=lambda p=prompt_num: self._show_stage_output(p),
        )
        return btn

    def _update_stage_status(self, prompt_num, status):
        """Update a stage's visual status."""
        self.stage_statuses[prompt_num] = status
        self.after(0, self._update_stage_list)
        self.after(0, lambda: self._update_simple_progress(prompt_num, status))
        self.after(0, lambda: self._update_activity_strip(prompt_num, status))

    def _show_stage_output(self, prompt_num):
        """Show the output for a specific stage in the main text area."""
        output = self.stage_outputs.get(prompt_num, "")
        if output:
            self.output_text.delete("1.0", "end")
            self.output_text.insert("1.0", output)
            self._apply_markdown_styling()
        else:
            self.output_text.delete("1.0", "end")
            self.output_text.insert("1.0", f"No output yet for {PROMPT_NAMES.get(prompt_num, f'Step {prompt_num}')}")

    # -----------------------------------------------------------------------
    # Markdown-style rendering for the output text area
    # -----------------------------------------------------------------------
    def _style_new_lines(self):
        """Incrementally style completed lines since last call.

        Called after each token insert during streaming.  Only processes
        lines that are fully complete (i.e. followed by a newline) so we
        never mangle a line the API is still writing to.
        """
        tw = self.output_text._textbox
        total_lines = int(tw.index("end-1c").split(".")[0])
        # Only process up to the SECOND-TO-LAST line — the last line may
        # still be receiving tokens and isn't safe to transform yet.
        safe_limit = max(total_lines - 1, 0)
        start = max(self._md_styled_up_to + 1, 1)
        if start > safe_limit:
            return

        # Process each new completed line (bottom-up within the new range
        # so deletions don't shift indices of lines we haven't visited yet)
        for line_num in range(safe_limit, start - 1, -1):
            line_start = f"{line_num}.0"
            line_end = f"{line_num}.end"
            line_text = tw.get(line_start, line_end)

            # Horizontal rule
            if re.match(r"^\s*-{3,}\s*$", line_text):
                tw.delete(line_start, line_end)
                tw.insert(line_start, "─" * 60)
                tw.tag_add("md_hr", line_start, f"{line_num}.end")
                continue

            # Headings
            h_match = re.match(r"^(#{1,3})\s+(.+)$", line_text)
            if h_match:
                level = len(h_match.group(1))
                heading_text = h_match.group(2)
                tag = f"md_h{level}"
                tw.delete(line_start, line_end)
                tw.insert(line_start, heading_text)
                tw.tag_add(tag, line_start, f"{line_num}.end")
                continue

            # Inline bold — process **text** pairs within this line
            col_start = f"{line_num}.0"
            col_end = f"{line_num}.end"
            search_pos = col_start
            while True:
                pos = tw.search("**", search_pos, stopindex=col_end)
                if not pos:
                    break
                after_open = f"{pos}+2c"
                close_pos = tw.search("**", after_open, stopindex=col_end)
                if not close_pos:
                    break
                bold_text = tw.get(after_open, close_pos)
                if not bold_text.strip():
                    search_pos = f"{close_pos}+2c"
                    continue
                tw.delete(close_pos, f"{close_pos}+2c")
                tw.delete(pos, f"{pos}+2c")
                end_of_bold = f"{pos}+{len(bold_text)}c"
                tw.tag_add("md_bold", pos, end_of_bold)
                # Recalculate col_end since we deleted chars
                col_end = f"{line_num}.end"
                search_pos = end_of_bold

        self._md_styled_up_to = safe_limit

    def _apply_markdown_styling(self):
        """Final-pass styling — processes the entire textbox including the
        last line.  Called when a stage finishes or when viewing saved output.
        """
        # Reset tracker so we process everything from the top
        self._md_styled_up_to = 0
        tw = self.output_text._textbox
        total_lines = int(tw.index("end-1c").split(".")[0])

        # Process ALL lines (including the last one, which is now complete)
        for line_num in range(total_lines, 0, -1):
            line_start = f"{line_num}.0"
            line_end = f"{line_num}.end"
            line_text = tw.get(line_start, line_end)

            # Skip lines already tagged (check for any of our tags)
            tags_here = tw.tag_names(line_start)
            if any(t.startswith("md_") for t in tags_here):
                continue

            # Horizontal rule
            if re.match(r"^\s*-{3,}\s*$", line_text):
                tw.delete(line_start, line_end)
                tw.insert(line_start, "─" * 60)
                tw.tag_add("md_hr", line_start, f"{line_num}.end")
                continue

            # Headings
            h_match = re.match(r"^(#{1,3})\s+(.+)$", line_text)
            if h_match:
                level = len(h_match.group(1))
                heading_text = h_match.group(2)
                tag = f"md_h{level}"
                tw.delete(line_start, line_end)
                tw.insert(line_start, heading_text)
                tw.tag_add(tag, line_start, f"{line_num}.end")
                continue

            # Inline bold
            search_pos = f"{line_num}.0"
            col_end = f"{line_num}.end"
            while True:
                pos = tw.search("**", search_pos, stopindex=col_end)
                if not pos:
                    break
                after_open = f"{pos}+2c"
                close_pos = tw.search("**", after_open, stopindex=col_end)
                if not close_pos:
                    break
                bold_text = tw.get(after_open, close_pos)
                if not bold_text.strip():
                    search_pos = f"{close_pos}+2c"
                    continue
                tw.delete(close_pos, f"{close_pos}+2c")
                tw.delete(pos, f"{pos}+2c")
                end_of_bold = f"{pos}+{len(bold_text)}c"
                tw.tag_add("md_bold", pos, end_of_bold)
                col_end = f"{line_num}.end"
                search_pos = end_of_bold

        self._md_styled_up_to = total_lines

    # -----------------------------------------------------------------------
    # Lane management
    # -----------------------------------------------------------------------
    def _get_lane_key(self):
        """Convert the display name back to a lane key."""
        display = self.lane_var.get()
        for key, lane in LANES.items():
            if lane["name"] == display:
                return key
        return "daily_production"

    def _on_lane_change(self, _=None):
        """Handle lane dropdown change."""
        self.stage_statuses.clear()
        self.stage_outputs.clear()
        self._selected_single_step = None
        self._update_stage_list()
        self._update_simple_progress()
        self._update_activity_strip()   # Reset activity strip on lane change
        self.output_text.delete("1.0", "end")

        # Clear any previous step picker buttons
        if hasattr(self, "_step_picker_frame"):
            self._step_picker_frame.grid_forget()
            self._step_picker_frame.destroy()
            del self._step_picker_frame

        lane_key = self._get_lane_key()
        lane = LANES.get(lane_key, {})
        desc = lane.get("description", "")

        if lane_key == "single_prompt":
            # Show step picker directly in main area instead of the output textbox
            self.output_text.grid_forget()
            self.topic_frame.grid_forget()
            self.story_input_frame.grid_forget()
            self.step_btn.grid_forget()  # Hide step-by-step — not relevant for single step
            self._build_step_picker()
            # Don't show any input yet — _select_single_step handles that
        else:
            # Normal lane — show output textbox
            if hasattr(self, "_step_picker_frame"):
                self._step_picker_frame.grid_forget()
                self._step_picker_frame.destroy()
                del self._step_picker_frame
            self.step_btn.grid(row=0, column=1, padx=6, pady=10)  # Restore step-by-step button
            self.output_text.grid(row=2, column=0, sticky="nsew", padx=14, pady=(12, 6))
            self.output_text.insert("1.0", f"{lane.get('name', '')}\n\n{desc}\n\nPress 'Go' to start, or 'Go Step-by-Step' to review each step before continuing.")

            # Show the right input area for this lane
            if lane_key == "adhoc_story":
                self.story_input_frame.grid_forget()
                self.topic_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
            elif lane_key == "story_polish":
                self.topic_frame.grid_forget()
                self.story_input_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
            else:
                self.topic_frame.grid_forget()
                self.story_input_frame.grid_forget()

    def _build_step_picker(self):
        """Build a compact step selection list in the main content area."""
        self._step_picker_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=COLORS["output_bg"],
            corner_radius=RADIUS["medium"],
            border_width=1,
            border_color=COLORS["border"],
        )
        self._step_picker_frame.grid(row=2, column=0, sticky="nsew", padx=14, pady=(12, 6))

        ctk.CTkLabel(
            self._step_picker_frame, text="Pick a step to run:",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=16, pady=(12, 6))

        self._step_picker_buttons = {}

        for num in range(1, 10):
            name = PROMPT_NAMES.get(num, f"Step {num}")
            desc = PROMPT_DESCRIPTIONS.get(num, "")

            # Single compact button: "1. News Aggregator: Searches all your sources..."
            btn = ctk.CTkButton(
                self._step_picker_frame,
                text=f"  {num}.  {name}:  {desc}",
                anchor="w",
                fg_color="transparent",
                hover_color=COLORS["surface_2"],
                text_color=COLORS["text"],
                height=32,
                corner_radius=RADIUS["small"],
                border_width=0,
                font=ctk.CTkFont(family="Segoe UI", size=13),
                command=lambda n=num: self._select_single_step(n),
            )
            btn.pack(fill="x", padx=8, pady=1)

            self._step_picker_buttons[num] = btn

    def _select_single_step(self, step_num):
        """User clicked a step in the picker — highlight it and show the right input."""
        self._selected_single_step = step_num

        # Clear previous input so stale content doesn't carry over between steps
        self.story_input_text.delete("1.0", "end")
        self.topic_entry.delete(0, "end")

        # Update button styles to show selection
        for num, btn in self._step_picker_buttons.items():
            if num == step_num:
                btn.configure(
                    fg_color=COLORS["accent"],
                    text_color=COLORS["on_primary"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text"],
                )

        # Show the appropriate input area for this step
        if step_num in self._steps_needing_story:
            self.topic_frame.grid_forget()
            self.story_input_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        elif step_num in self._steps_needing_topic:
            self.story_input_frame.grid_forget()
            self.topic_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        else:
            # Steps 1, 3 — self-contained, no input needed
            self.topic_frame.grid_forget()
            self.story_input_frame.grid_forget()

        name = PROMPT_NAMES.get(step_num, f"Step {step_num}")
        self.status_label.configure(text=f"Selected: {name} — press Go to run it.")

    # -----------------------------------------------------------------------
    # Pipeline execution
    # -----------------------------------------------------------------------
    def _validate_config(self):
        """Check that minimum config is set before running."""
        if not self.config_data.get("api_key"):
            messagebox.showwarning("API Key Required",
                "Please enter your Claude API key in Settings before running the pipeline.")
            self._open_settings()
            return False
        if not self.config_data.get("city_name"):
            messagebox.showwarning("City Required",
                "Please configure your city in City Configuration before running.")
            self._open_city_config()
            return False
        return True

    def _set_running(self, running):
        """Toggle UI state for running/idle."""
        self.is_running = running
        state = "disabled" if running else "normal"
        self.run_btn.configure(state=state)
        self.step_btn.configure(state=state)
        self.cancel_btn.configure(state="normal" if running else "disabled")
        self.lane_menu.configure(state=state)
        if not running:
            self._stop_dot_animation()

    def _run_pipeline(self, step_by_step=False):
        """Shared pipeline execution logic for both run modes.

        Args:
            step_by_step: If True, pauses for user approval between stages.
        """
        if not self._validate_config():
            return

        lane_key = self._get_lane_key()

        if lane_key == "single_prompt":
            if not self._selected_single_step:
                messagebox.showinfo("Pick a Step",
                    "Click on one of the steps in the list first, then press Go.")
                return
            self._run_single_prompt_from_picker(self._selected_single_step)
            return

        self._set_running(True)
        self.stage_statuses.clear()
        self.stage_outputs.clear()
        self.output_text.delete("1.0", "end")
        self._update_stage_list()
        self.approve_frame.grid_forget()

        self.runner = PipelineRunner(self.config_data)
        topic = self.topic_entry.get() if lane_key == "adhoc_story" else None

        # For story_polish, pass the user's pasted story as initial input
        initial_input = None
        if lane_key == "story_polish":
            initial_input = self.story_input_text.get("1.0", "end").strip() or None

        stages = LANES[lane_key]["stages"]
        total = len(stages)

        def on_stage_start(num, name):
            self.current_stage = num
            self.after(0, lambda: self._update_stage_status(num, "running"))
            self.after(0, lambda: self.status_label.configure(
                text=f"{name}..."))
            idx = stages.index(num) if num in stages else 0
            self.after(0, lambda: self.progress_bar.set(idx / total))
            self.after(0, lambda: self.output_text.delete("1.0", "end"))
            self._md_styled_up_to = 0
            self.after(0, lambda: self.output_text.insert("1.0",
                f"{name}\n{'─' * 50}\n\n"))

        def on_token(text):
            def _insert_and_style(t=text):
                self.output_text.insert("end", t)
                if "\n" in t:
                    self._style_new_lines()
            self.after(0, _insert_and_style)

        def on_progress(text):
            self.after(0, lambda t=text: self.status_label.configure(text=t))

        def on_stage_complete(num, output):
            self.stage_outputs[num] = output
            self.after(0, lambda: self._update_stage_status(num, "done"))
            self.after(0, self._apply_markdown_styling)

        # Only define approval callback for step-by-step mode
        wait_for_approval = None
        if step_by_step:
            def wait_for_approval(stage_num):
                self._approval_event.clear()
                self._approved = False
                name = PROMPT_NAMES.get(stage_num, f"Step {stage_num}")
                self.after(0, lambda: self.status_label.configure(
                    text=f"{name} finished. Review the output, then click 'Looks Good' to continue."))
                self.after(0, lambda: self.approve_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=5))
                self._approval_event.wait()  # Block until user clicks approve
                self.after(0, lambda: self.approve_frame.grid_forget())
                return self._approved

        def on_lane_complete(outputs):
            # Auto-save to the user's configured output directory
            saved_dir = None
            try:
                self.runner.outputs = self.stage_outputs
                out_dir = self.config_data.get("output_directory", "")
                if out_dir and os.path.isdir(out_dir):
                    saved = self.runner.save_outputs(out_dir)
                    saved_dir = out_dir
                    logger.info(f"Auto-saved {len(saved)} files to {out_dir}")
            except Exception as save_err:
                logger.warning(f"Auto-save failed: {save_err}")

            self.after(0, lambda: self.progress_bar.set(1.0))
            self.after(0, lambda: self.status_label.configure(
                text="All done! Your stories are ready.", text_color=COLORS["success"]))
            self.after(0, self._apply_markdown_styling)
            self.after(0, lambda: self._set_running(False))
            self.after(0, lambda: self.approve_frame.grid_forget())

            if saved_dir:
                self.after(0, lambda d=saved_dir: messagebox.showinfo("Done!",
                    f"Your stories are ready and saved to:\n{d}\n\n"
                    "You can also click 'Save' to save a copy to another folder."))
            else:
                self.after(0, lambda: messagebox.showinfo("Done!",
                    "Your stories are ready!\n\n"
                    "Click 'Save' to save them to a folder on your computer."))

        def run():
            try:
                self.runner.run_lane(
                    lane_key,
                    topic=topic,
                    initial_input=initial_input,
                    on_stage_start=on_stage_start,
                    on_progress=on_progress,
                    on_token=on_token,
                    on_stage_complete=on_stage_complete,
                    on_lane_complete=on_lane_complete,
                    wait_for_approval=wait_for_approval,
                )
            except Exception as e:
                # Even on error, auto-save whatever stages completed
                try:
                    self.runner.outputs = self.stage_outputs
                    out_dir = self.config_data.get("output_directory", "")
                    if out_dir and os.path.isdir(out_dir):
                        self.runner.save_outputs(out_dir)
                except Exception:
                    pass
                self.after(0, lambda: messagebox.showerror("Something Went Wrong",
                    f"The toolkit ran into a problem:\n\n{e}\n\n"
                    "Check your API key and internet connection, then try again."))
                self.after(0, lambda: self._set_running(False))
                self.after(0, lambda: self.status_label.configure(text="Error — see message above"))

        threading.Thread(target=run, daemon=True).start()

    def _run_complete(self):
        """Run the full pipeline lane without stopping."""
        self._run_pipeline(step_by_step=False)

    def _run_step_by_step(self):
        """Run the pipeline lane with approval between stages."""
        self._run_pipeline(step_by_step=True)

    def _approve_stage(self):
        """User approves the current stage output to continue."""
        # Allow user to edit the output before continuing
        edited = self.output_text.get("1.0", "end").strip()
        if self.current_stage and edited:
            # Find the actual output (skip the header line — now uses ─ separator)
            lines = edited.split("\n", 2)
            if len(lines) > 2:
                self.stage_outputs[self.current_stage] = lines[2]
                if self.runner:
                    self.runner.outputs[self.current_stage] = lines[2]
        self._approved = True
        self._approval_event.set()

    def _cancel_run(self):
        """Cancel the currently running pipeline."""
        if self.runner:
            self.runner.cancel()
        self._approved = False
        self._approval_event.set()
        self.after(500, lambda: self._set_running(False))
        self.status_label.configure(text="Stopped.")
        self.step_counter_label.configure(text="")

    def _run_single_prompt_from_picker(self, prompt_num):
        """Run a single prompt selected from the inline step picker."""
        # Validate: if this step needs story content, check that the user pasted something
        if prompt_num in self._steps_needing_story:
            story_text = self.story_input_text.get("1.0", "end").strip()
            if not story_text:
                name = PROMPT_NAMES.get(prompt_num, f"Step {prompt_num}")
                messagebox.showinfo(
                    "Paste Your Content First",
                    f"{name} needs something to work with.\n\n"
                    f"Paste a story, draft, or content into the text area above, "
                    f"then press Go again."
                )
                return
        elif prompt_num in self._steps_needing_topic:
            topic_text = self.topic_entry.get().strip()
            if not topic_text:
                name = PROMPT_NAMES.get(prompt_num, f"Step {prompt_num}")
                messagebox.showinfo(
                    "Enter a Topic First",
                    f"{name} needs a topic to work with.\n\n"
                    f"Type a topic in the field above, then press Go again."
                )
                return

        # Switch from step picker back to output textbox
        if hasattr(self, "_step_picker_frame"):
            self._step_picker_frame.grid_forget()
            self._step_picker_frame.destroy()
            del self._step_picker_frame
        self.story_input_frame.grid_forget()
        self.topic_frame.grid_forget()
        self.output_text.grid(row=2, column=0, sticky="nsew", padx=14, pady=(12, 6))
        self._run_single_prompt_exec(prompt_num)

    def _run_single_prompt_exec(self, prompt_num):
        """Actually execute a single prompt."""

        if not self._validate_config():
            return

        self._set_running(True)
        self.current_stage = prompt_num
        self.stage_statuses = {prompt_num: "running"}
        self.stage_outputs.clear()
        self._update_stage_list()
        self._update_activity_strip(prompt_num, "running", lane_key="single_prompt")
        self.output_text.delete("1.0", "end")
        self._md_styled_up_to = 0
        name = PROMPT_NAMES.get(prompt_num, f"Step {prompt_num}")
        self.output_text.insert("1.0", f"{name}\n{'─' * 50}\n\n")

        self.runner = PipelineRunner(self.config_data)
        topic = self.topic_entry.get() or None

        # Get story content if this step needs it (pasted by user for standalone use)
        previous_output = None
        if prompt_num in self._steps_needing_story:
            previous_output = self.story_input_text.get("1.0", "end").strip() or None

        def on_token(text):
            def _insert_and_style(t=text):
                self.output_text.insert("end", t)
                if "\n" in t:
                    self._style_new_lines()
            self.after(0, _insert_and_style)

        def on_progress(text):
            self.after(0, lambda t=text: self.status_label.configure(text=t))

        def run():
            try:
                output = self.runner.run_single_stage(
                    prompt_num,
                    previous_output=previous_output,
                    topic=topic,
                    on_progress=on_progress,
                    on_token=on_token,
                )
                self.stage_outputs[prompt_num] = output
                self.after(0, lambda: self._update_stage_status(prompt_num, "done"))
                self.after(0, self._apply_markdown_styling)
                self.after(0, lambda: self.progress_bar.set(1.0))
                self.after(0, lambda: self._set_running(False))
            except Exception as e:
                self.after(0, lambda: self._update_stage_status(prompt_num, "error"))
                # Show a friendly message instead of raw exception
                err_str = str(e).lower()
                if "api key" in err_str or "authentication" in err_str or "401" in str(e):
                    friendly = "Your API key doesn't seem to be working. Check it in Settings and try again."
                elif "429" in str(e) or "rate" in err_str:
                    friendly = "Claude is busy right now (rate limited). Wait a minute and try again."
                elif "connection" in err_str or "timeout" in err_str:
                    friendly = "Couldn't reach the Claude API. Check your internet connection and try again."
                else:
                    friendly = f"Something went wrong while running this step.\n\nDetails: {e}"
                self.after(0, lambda msg=friendly: messagebox.showerror("Something Went Wrong", msg))
                self.after(0, lambda: self._set_running(False))

        threading.Thread(target=run, daemon=True).start()

    # -----------------------------------------------------------------------
    # Save output
    # -----------------------------------------------------------------------
    def _get_output_directory(self, auto=False):
        """Get the output directory — from config, or ask the user.

        If *auto* is True (auto-save after pipeline), use the saved
        directory without prompting.  Returns None if the user cancels.
        """
        saved_dir = self.config_data.get("output_directory", "")
        if auto and saved_dir and os.path.isdir(saved_dir):
            return saved_dir

        # Ask the user — use initialdir so the dialog opens where they last saved
        initial = saved_dir if saved_dir and os.path.isdir(saved_dir) else os.path.expanduser("~")
        directory = filedialog.askdirectory(
            title="Where should your stories be saved?",
            initialdir=initial,
            mustexist=True,
        )
        if not directory:
            return None

        # Remember the choice
        self.config_data["output_directory"] = directory
        from config import save_config
        save_config(self.config_data)
        return directory

    def _save_output(self):
        """Save all pipeline outputs to files."""
        if not self.stage_outputs:
            messagebox.showinfo("Nothing to Save", "No pipeline output to save yet.")
            return

        directory = self._get_output_directory(auto=False)
        if not directory:
            return

        try:
            if self.runner:
                self.runner.outputs = self.stage_outputs
                files = self.runner.save_outputs(directory)
            else:
                # Manual save (no runner available)
                from pipeline import _markdown_to_docx
                today = datetime.now().strftime("%Y-%m-%d")
                files = []
                for num, output in self.stage_outputs.items():
                    # Save .md
                    fname = f"{today}_stage-{num:02d}.md"
                    fpath = os.path.join(directory, fname)
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(output)
                    files.append(fpath)
                    # Save .docx
                    try:
                        docx_path = os.path.join(directory, f"{today}_stage-{num:02d}.docx")
                        _markdown_to_docx(output, docx_path)
                        files.append(docx_path)
                    except Exception:
                        pass  # .md still saved

            md_count = sum(1 for f in files if f.endswith(".md"))
            docx_count = sum(1 for f in files if f.endswith(".docx"))
            if md_count > 0 and docx_count == 0:
                messagebox.showwarning("Saved (Markdown Only)",
                    f"Saved {md_count} .md file(s) to:\n{directory}\n\n"
                    "Word (.docx) files could not be created.\n"
                    "Install python-docx to enable Word export:\n"
                    "  pip install python-docx")
            else:
                messagebox.showinfo("Saved",
                    f"Saved {len(files)} file(s) to:\n{directory}\n\n"
                    f"{md_count} Markdown + {docx_count} Word document(s)")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    # -----------------------------------------------------------------------
    # Settings dialog
    # -----------------------------------------------------------------------
    def _open_settings(self):
        """Open the settings dialog for API key and model selection."""
        # Show cost/setup info popup the first time a user needs to enter an API key
        first_time = not self.config_data.get("api_key")
        if first_time and not self.config_data.get("_seen_api_info"):
            messagebox.showinfo("Before You Start",
                "This toolkit uses the Claude API from Anthropic to do its work.\n\n"
                "A few things to know:\n\n"
                "1. YOU NEED AN API KEY\n"
                "   Go to console.anthropic.com, create a free account,\n"
                "   and generate an API key. It starts with 'sk-ant-'.\n\n"
                "2. IT COSTS MONEY (but not much)\n"
                "   Every time the toolkit runs, it sends text to Claude\n"
                "   and Anthropic charges your account. A typical daily\n"
                "   run costs roughly $0.05-$0.25 depending on how many\n"
                "   sources you have. You can set a spending limit on\n"
                "   your Anthropic account to stay in control.\n\n"
                "3. CHOOSING A MODEL\n"
                "   Haiku is the default — fast, capable, and very affordable.\n"
                "   Sonnet is more powerful but costs more.\n"
                "   Opus is the most capable but costs significantly more.\n\n"
                "Once you have your API key, paste it in the next screen\n"
                "and you're ready to go.")
            self.config_data["_seen_api_info"] = True
            save_config(self.config_data)

        dialog = ctk.CTkToplevel(self)
        dialog.title("Settings")
        dialog.geometry("550x750")
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(fg_color=COLORS["bg_dark"])

        pad = {"padx": 28, "pady": (12, 2)}

        ctk.CTkLabel(dialog, text="Settings",
                      font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
                      text_color=COLORS["text"]).pack(pady=(24, 16))

        # API Key — M3 text field
        ctk.CTkLabel(dialog, text="Claude API Key:",
                      font=ctk.CTkFont(family="Segoe UI", size=14),
                      text_color=COLORS["text"]).pack(anchor="w", **pad)
        api_entry = ctk.CTkEntry(dialog, width=480, show="*",
                                  placeholder_text="sk-ant-...",
                                  height=44,
                                  corner_radius=RADIUS["small"],
                                  border_width=1,
                                  border_color=COLORS["outline"],
                                  fg_color=COLORS["output_bg"],
                                  font=ctk.CTkFont(family="Segoe UI", size=14))
        api_entry.pack(padx=28, pady=(0, 6))
        _add_context_menu(api_entry)
        if self.config_data.get("api_key"):
            api_entry.insert(0, self.config_data["api_key"])

        ctk.CTkLabel(dialog,
                      text="Each pipeline run costs ~$0.05-$0.25 on your Anthropic account",
                      font=ctk.CTkFont(family="Segoe UI", size=12),
                      text_color=COLORS["warning"]).pack(anchor="w", padx=28, pady=(0, 6))

        # Show/hide toggle — M3 checkbox
        show_var = ctk.BooleanVar(value=False)
        def toggle_show():
            api_entry.configure(show="" if show_var.get() else "*")
        ctk.CTkCheckBox(dialog, text="Show key", variable=show_var,
                         command=toggle_show,
                         font=ctk.CTkFont(family="Segoe UI", size=12),
                         fg_color=COLORS["accent"],
                         border_color=COLORS["outline"],
                         hover_color=COLORS["surface_2"],
                         corner_radius=4).pack(anchor="w", padx=28)

        # Model selection — M3 dropdown
        ctk.CTkLabel(dialog, text="Model:",
                      font=ctk.CTkFont(family="Segoe UI", size=14),
                      text_color=COLORS["text"]).pack(anchor="w", padx=28, pady=(16, 2))
        model_var = ctk.StringVar(value=self.config_data.get("model", "claude-haiku-4-5-20251001"))
        model_menu = ctk.CTkOptionMenu(
            dialog, variable=model_var,
            values=[
                "claude-haiku-4-5-20251001",
                "claude-sonnet-4-20250514",
                "claude-opus-4-20250514",
            ],
            width=480,
            height=40,
            corner_radius=RADIUS["small"],
            fg_color=COLORS["secondary_container"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            text_color=COLORS["on_secondary_container"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
            dropdown_fg_color=COLORS["bg_sidebar"],
            dropdown_hover_color=COLORS["surface_2"],
        )
        model_menu.pack(padx=28, pady=(0, 10))

        # Research model
        ctk.CTkLabel(dialog, text="Research Model (for prompts 1, 3, 9 — leave blank to use main model):",
                      font=ctk.CTkFont(family="Segoe UI", size=14),
                      text_color=COLORS["text"]).pack(anchor="w", padx=28, pady=(16, 2))
        research_model_var = ctk.StringVar(value=self.config_data.get("research_model", ""))
        research_model_menu = ctk.CTkOptionMenu(
            dialog, variable=research_model_var,
            values=[
                "Same as main model",
                "claude-haiku-4-5-20251001",
                "claude-sonnet-4-20250514",
                "claude-opus-4-20250514",
            ],
            width=480,
            height=40,
            corner_radius=RADIUS["small"],
            fg_color=COLORS["secondary_container"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            text_color=COLORS["on_secondary_container"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
            dropdown_fg_color=COLORS["bg_sidebar"],
            dropdown_hover_color=COLORS["surface_2"],
        )
        if not self.config_data.get("research_model"):
            research_model_var.set("Same as main model")
        research_model_menu.pack(padx=28, pady=(0, 10))

        ctk.CTkLabel(dialog,
                      text="Use a different model for research steps if you want (most people leave this as-is)",
                      font=ctk.CTkFont(family="Segoe UI", size=12),
                      text_color=COLORS["text_dim"]).pack(anchor="w", padx=28, pady=(0, 6))

        # Output folder
        ctk.CTkLabel(dialog, text="Output Folder (where your stories are saved):",
                      font=ctk.CTkFont(family="Segoe UI", size=14),
                      text_color=COLORS["text"]).pack(anchor="w", padx=28, pady=(16, 2))

        output_row = ctk.CTkFrame(dialog, fg_color="transparent")
        output_row.pack(fill="x", padx=28, pady=(0, 4))

        output_dir_var = ctk.StringVar(value=self.config_data.get("output_directory", ""))
        output_entry = ctk.CTkEntry(
            output_row, textvariable=output_dir_var,
            width=380, height=40,
            corner_radius=RADIUS["small"],
            border_width=1,
            border_color=COLORS["outline"],
            fg_color=COLORS["output_bg"],
            placeholder_text="Click Browse or leave blank to choose each time",
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        output_entry.pack(side="left", fill="x", expand=True)
        _add_context_menu(output_entry)

        def browse_output_folder():
            current = output_dir_var.get().strip()
            initial = current if current and os.path.isdir(current) else os.path.expanduser("~")
            chosen = filedialog.askdirectory(
                title="Choose output folder for saved stories",
                initialdir=initial,
                mustexist=True,
            )
            if chosen:
                output_dir_var.set(chosen)

        ctk.CTkButton(
            output_row, text="Browse", command=browse_output_folder,
            width=90, height=40,
            corner_radius=RADIUS["small"],
            fg_color=COLORS["secondary_container"],
            hover_color=COLORS["surface_2"],
            text_color=COLORS["on_secondary_container"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
        ).pack(side="left", padx=(8, 0))

        ctk.CTkLabel(dialog,
                      text="Leave blank to be asked each time you save",
                      font=ctk.CTkFont(family="Segoe UI", size=12),
                      text_color=COLORS["text_dim"]).pack(anchor="w", padx=28, pady=(0, 6))

        # Get key link
        ctk.CTkLabel(dialog,
                      text="Get an API key at console.anthropic.com",
                      font=ctk.CTkFont(family="Segoe UI", size=12),
                      text_color=COLORS["text_light"]).pack(padx=28, pady=(6, 0))

        # Save
        def save():
            key = api_entry.get().strip()
            if key and not key.startswith("sk-ant-"):
                messagebox.showwarning("Check Your API Key",
                    "Anthropic API keys start with 'sk-ant-'.\n\n"
                    "The value you entered doesn't look right. "
                    "Double-check and try again.",
                    parent=dialog)
                return
            self.config_data["api_key"] = key
            self.config_data["model"] = model_var.get()
            rm = research_model_var.get()
            self.config_data["research_model"] = "" if rm == "Same as main model" else rm
            self.config_data["output_directory"] = output_dir_var.get().strip()
            save_config(self.config_data)
            self.runner = None  # Reset client
            dialog.destroy()
            self.status_label.configure(text="Settings saved.")

        ctk.CTkButton(dialog, text="Save Settings", command=save,
                       fg_color=COLORS["accent"],
                       hover_color=COLORS["accent_hover"],
                       text_color=COLORS["on_primary"],
                       height=44, width=200,
                       corner_radius=RADIUS["full"],
                       font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold")).pack(pady=28)

    # -----------------------------------------------------------------------
    # City configuration dialog
    # -----------------------------------------------------------------------
    def _open_city_config(self):
        """Open the city configuration dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("City Configuration")
        dialog.geometry("750x850")
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(fg_color=COLORS["bg_dark"])

        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent",
                                         corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(scroll, text="City Configuration",
                      font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
                      text_color=COLORS["text"]).pack(pady=(12, 16))

        entries = {}

        def add_field(label, key, parent_key=None, placeholder=""):
            ctk.CTkLabel(scroll, text=label, font=ctk.CTkFont(family="Segoe UI", size=13),
                          text_color=COLORS["text_dim"]).pack(anchor="w", padx=16, pady=(10, 0))
            entry = ctk.CTkEntry(scroll, width=580, placeholder_text=placeholder,
                                  height=40,
                                  corner_radius=RADIUS["small"],
                                  border_width=1,
                                  border_color=COLORS["outline"],
                                  fg_color=COLORS["output_bg"],
                                  font=ctk.CTkFont(family="Segoe UI", size=13))
            entry.pack(padx=16, pady=(0, 2))
            _add_context_menu(entry)
            # Load current value
            if parent_key:
                val = self.config_data.get(parent_key, {}).get(key, "")
            else:
                val = self.config_data.get(key, "")
            if val:
                entry.insert(0, val)
            entries[(parent_key, key) if parent_key else (None, key)] = entry

        # Basic info — M3 title medium
        ctk.CTkLabel(scroll, text="Basic Info",
                      font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
                      text_color=COLORS["accent"]).pack(anchor="w", padx=16, pady=(6, 0))
        add_field("City Name:", "city_name", placeholder="e.g., Your City")
        add_field("State:", "state", placeholder="e.g., Your State")
        add_field("State Open Records Law:", "state_open_records_law", placeholder="e.g., CORA, FOIA, OPRA")
        add_field("City Clerk Contact:", "city_clerk_contact", placeholder="e.g., cityclerk@yourcity.gov")

        # Sources — M3 title medium
        ctk.CTkLabel(scroll, text="Primary Sources",
                      font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
                      text_color=COLORS["accent"]).pack(anchor="w", padx=16, pady=(18, 0))
        add_field("City Agenda Portal URL:", "city_agenda_portal_url", "sources",
                  placeholder="e.g., https://yourcity.primegov.com")
        add_field("City News Page URL:", "city_news_url", "sources",
                  placeholder="e.g., https://yourcity.gov/news")
        add_field("School District Name:", "school_district_name", "sources",
                  placeholder="e.g., Your School District")
        add_field("School District URL:", "school_district_url", "sources")
        add_field("Transit Agency Name:", "transit_agency_name", "sources",
                  placeholder="e.g., RTD")
        add_field("Transit Agency URL:", "transit_agency_url", "sources")
        add_field("County Name:", "county_name", "sources",
                  placeholder="e.g., Your County")
        add_field("County Government URL:", "county_gov_url", "sources")
        add_field("State Government URL:", "state_gov_url", "sources")
        add_field("Local Media Outlet Name:", "local_media_outlet", "sources",
                  placeholder="e.g., City Times")
        add_field("Local Media URL:", "local_media_url", "sources")

        # YouTube
        ctk.CTkLabel(scroll, text="YouTube",
                      font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
                      text_color=COLORS["accent"]).pack(anchor="w", padx=16, pady=(18, 0))
        add_field("City YouTube Channel URL:", "youtube_channel_url", "sources",
                  placeholder="e.g., https://www.youtube.com/@YourCity")

        # --- Additional Sources ---
        ctk.CTkLabel(scroll, text="Additional Sources",
                      font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
                      text_color=COLORS["accent"]).pack(anchor="w", padx=16, pady=(18, 0))
        ctk.CTkLabel(scroll, text="These are appended to research prompts (1, 3, 9) as extra context.",
                      font=ctk.CTkFont(family="Segoe UI", size=12),
                      text_color=COLORS["text_dim"]).pack(anchor="w", padx=16, pady=(2, 6))

        # Container for source rows
        sources_container = ctk.CTkFrame(scroll, fg_color="transparent")
        sources_container.pack(fill="x", padx=10, pady=(0, 5))

        # Header row — M3 surface container
        header = ctk.CTkFrame(sources_container, fg_color=COLORS["surface_2"],
                               corner_radius=RADIUS["small"])
        header.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(header, text="Name", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                      width=160, anchor="w", text_color=COLORS["text"]).grid(row=0, column=0, padx=(10, 4), pady=6)
        ctk.CTkLabel(header, text="URL", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                      width=200, anchor="w", text_color=COLORS["text"]).grid(row=0, column=1, padx=4, pady=6)
        ctk.CTkLabel(header, text="Type", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                      width=40, anchor="w", text_color=COLORS["text"]).grid(row=0, column=2, padx=4, pady=6)
        ctk.CTkLabel(header, text="Category", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                      width=100, anchor="w", text_color=COLORS["text"]).grid(row=0, column=3, padx=4, pady=6)

        # Mutable list of source row data (each row is a dict of widgets)
        source_rows = []

        def add_source_row(name="", url="", tier="B", category="General"):
            """Add one editable source row to the UI."""
            row_frame = ctk.CTkFrame(sources_container, fg_color="transparent")
            row_frame.pack(fill="x", pady=1)

            name_entry = ctk.CTkEntry(row_frame, width=160, placeholder_text="Source name",
                                       font=ctk.CTkFont(family="Segoe UI", size=11),
                                       height=34, corner_radius=RADIUS["small"],
                                       border_width=1, border_color=COLORS["border"])
            name_entry.grid(row=0, column=0, padx=(8, 2), pady=3)
            if name:
                name_entry.insert(0, name)

            url_entry = ctk.CTkEntry(row_frame, width=200, placeholder_text="https://...",
                                      font=ctk.CTkFont(family="Segoe UI", size=11),
                                      height=34, corner_radius=RADIUS["small"],
                                      border_width=1, border_color=COLORS["border"])
            url_entry.grid(row=0, column=1, padx=2, pady=3)
            if url:
                url_entry.insert(0, url)

            tier_entry = ctk.CTkOptionMenu(row_frame, width=120,
                                            values=list(TYPE_LABELS.values()),
                                            font=ctk.CTkFont(family="Segoe UI", size=11),
                                            height=34,
                                            corner_radius=RADIUS["small"],
                                            fg_color=COLORS["secondary_container"],
                                            button_color=COLORS["accent"],
                                            text_color=COLORS["on_secondary_container"])
            tier_entry.set(TYPE_LABELS.get(tier, "News"))
            tier_entry.grid(row=0, column=2, padx=2, pady=3)

            cat_entry = ctk.CTkEntry(row_frame, width=100, placeholder_text="Category",
                                      font=ctk.CTkFont(family="Segoe UI", size=11),
                                      height=34, corner_radius=RADIUS["small"],
                                      border_width=1, border_color=COLORS["border"])
            cat_entry.grid(row=0, column=3, padx=2, pady=3)
            if category:
                cat_entry.insert(0, category)

            def delete_row():
                row_data["deleted"] = True
                row_frame.destroy()

            del_btn = ctk.CTkButton(row_frame, text="X", width=30, height=30,
                                     fg_color=COLORS["error"], hover_color=COLORS["error_hover"],
                                     text_color="#FFFFFF",
                                     corner_radius=RADIUS["full"],
                                     font=ctk.CTkFont(family="Segoe UI", size=11), command=delete_row)
            del_btn.grid(row=0, column=4, padx=(4, 8), pady=3)

            row_data = {
                "frame": row_frame,
                "name": name_entry,
                "url": url_entry,
                "tier": tier_entry,
                "category": cat_entry,
                "deleted": False,
            }
            source_rows.append(row_data)

        # Populate existing additional sources
        for src in self.config_data.get("additional_sources", []):
            add_source_row(
                name=src.get("name", ""),
                url=src.get("url", ""),
                tier=src.get("tier", "B"),
                category=src.get("category", "General"),
            )

        # Add Source button — M3 tonal
        ctk.CTkButton(sources_container, text="+ Add Source",
                       fg_color=COLORS["secondary_container"],
                       hover_color=COLORS["surface_2"],
                       text_color=COLORS["on_secondary_container"],
                       height=36, width=140,
                       corner_radius=RADIUS["full"],
                       font=ctk.CTkFont(family="Segoe UI", size=12),
                       command=lambda: add_source_row()).pack(anchor="w", padx=8, pady=(8, 0))

        # Save
        def save():
            _log_debug("City Config save(): starting")
            for (parent_key, key), entry in entries.items():
                val = entry.get().strip()
                # Don't overwrite an auto-populated value with blank
                if not val:
                    if parent_key:
                        existing = self.config_data.get(parent_key, {}).get(key, "")
                    else:
                        existing = self.config_data.get(key, "")
                    if existing:
                        _log_debug(f"  save(): BLANK GUARD kept '{key}' = '{existing}'")
                        continue  # keep the existing value
                if parent_key:
                    if parent_key not in self.config_data:
                        self.config_data[parent_key] = {}
                    self.config_data[parent_key][key] = val
                else:
                    self.config_data[key] = val

            # Collect additional sources from the editable rows
            updated_sources = []
            for row in source_rows:
                if row["deleted"]:
                    continue
                src_name = row["name"].get().strip()
                src_url = row["url"].get().strip()
                src_tier_label = row["tier"].get()
                src_tier = TYPE_CODES.get(src_tier_label, "B")  # Convert label → A/B/C
                src_cat = row["category"].get().strip()
                if src_url:  # Only keep rows that have a URL
                    updated_sources.append({
                        "name": src_name,
                        "url": src_url,
                        "tier": src_tier,
                        "category": src_cat or "General",
                    })
            self.config_data["additional_sources"] = updated_sources

            save_config(self.config_data)
            _log_debug(f"City Config save(): complete. state='{self.config_data.get('state', '')}' "
                       f"records_law='{self.config_data.get('state_open_records_law', '')}' "
                       f"clerk='{self.config_data.get('city_clerk_contact', '')}' "
                       f"youtube='{self.config_data.get('sources', {}).get('youtube_channel_url', '')}'")
            city = self.config_data.get("city_name", "")
            state = self.config_data.get("state", "")
            self.city_label.configure(text=f"{city}, {state}" if city else "No city configured")
            dialog.destroy()
            self.status_label.configure(text="City configuration saved.")

        ctk.CTkButton(scroll, text="Save", command=save,
                       fg_color=COLORS["accent"],
                       hover_color=COLORS["accent_hover"],
                       text_color=COLORS["on_primary"],
                       height=44, width=200,
                       corner_radius=RADIUS["full"],
                       font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold")).pack(pady=24)

    # -----------------------------------------------------------------------
    # Source import
    # -----------------------------------------------------------------------
    def _import_sources(self):
        """Import additional sources from a text file."""
        filepath = filedialog.askopenfilename(
            title="Import Sources File",
            filetypes=[
                ("Text files", "*.txt"),
                ("CSV files", "*.csv"),
                ("All files", "*.*"),
            ]
        )
        if not filepath:
            return

        try:
            sources, metadata = import_sources_from_file(filepath)
            if not sources:
                messagebox.showwarning("No Sources Found",
                    "Could not parse any sources from that file.\n\n"
                    "Supported formats:\n"
                    "  - One URL per line\n"
                    "  - Name: URL (one per line)\n"
                    "  - Name, URL, Type, Category (CSV)")
                return

            _log_debug(f"_import_sources: file={filepath}, got {len(sources)} sources, metadata={metadata}")

            self.config_data["additional_sources"] = sources

            # Snapshot BEFORE auto-populate to detect what changed
            before = {
                "city_name": self.config_data.get("city_name", ""),
                "state": self.config_data.get("state", ""),
                "state_open_records_law": self.config_data.get("state_open_records_law", ""),
                "city_clerk_contact": self.config_data.get("city_clerk_contact", ""),
                "youtube_channel_url": self.config_data.get("sources", {}).get("youtube_channel_url", ""),
            }

            # Auto-fill City Configuration fields from imported sources
            auto_populate_config_from_sources(self.config_data, sources, metadata)

            # Snapshot AFTER auto-populate
            after = {
                "city_name": self.config_data.get("city_name", ""),
                "state": self.config_data.get("state", ""),
                "state_open_records_law": self.config_data.get("state_open_records_law", ""),
                "city_clerk_contact": self.config_data.get("city_clerk_contact", ""),
                "youtube_channel_url": self.config_data.get("sources", {}).get("youtube_channel_url", ""),
            }

            _log_debug(f"_import_sources: BEFORE auto-populate: {before}")
            _log_debug(f"_import_sources: AFTER  auto-populate: {after}")

            save_config(self.config_data)

            # Update city label in sidebar
            city = self.config_data.get("city_name", "")
            state = self.config_data.get("state", "")
            self.city_label.configure(text=f"{city}, {state}" if city else "No city configured")

            # Show summary including auto-populated fields — show ACTUAL config values,
            # not just what metadata contained, so user can see exactly what's stored
            summary = f"Imported {len(sources)} source(s).\n\n"

            # Show what was actually populated (from config, not just metadata)
            populated = []
            field_labels = [
                ("city_name", "City", None),
                ("state", "State", None),
                ("state_open_records_law", "Open Records Law", None),
                ("city_clerk_contact", "City Clerk", None),
                ("youtube_channel_url", "YouTube", "sources"),
            ]
            missing = []
            for key, label, parent in field_labels:
                if parent:
                    val = self.config_data.get(parent, {}).get(key, "")
                else:
                    val = self.config_data.get(key, "")
                if val:
                    changed = " (updated)" if before[key] != val else ""
                    populated.append(f"  {label}: {val}{changed}")
                else:
                    missing.append(f"  {label}: NOT SET")

            if populated:
                summary += "Populated settings:\n" + "\n".join(populated) + "\n\n"
            if missing:
                summary += "Missing settings (not found in file):\n" + "\n".join(missing) + "\n\n"

            summary += "Sources:\n"
            for s in sources[:10]:
                name = s.get("name", "Unnamed")
                url = s.get("url", "")
                tier = s.get("tier", "B")
                type_label = TYPE_LABELS.get(tier, "News")
                summary += f"  [{type_label}] {name}: {url[:60]}...\n" if len(url) > 60 else f"  [{type_label}] {name}: {url}\n"
            if len(sources) > 10:
                summary += f"\n  ... and {len(sources) - 10} more"

            summary += (
                "\n\nNote: If City Configuration is open, close and "
                "reopen it to see the updated values."
            )

            messagebox.showinfo("Sources Imported", summary)
            self.status_label.configure(text=f"Imported {len(sources)} source(s).")

            # If critical fields are still missing, open City Config so user can fill them in
            if missing:
                messagebox.showinfo("Complete Your Setup",
                    "Some settings couldn't be auto-detected from the file.\n\n"
                    "Opening City Configuration so you can fill in the remaining fields.")
                self._open_city_config()

        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    # -----------------------------------------------------------------------
    # Source template export
    # -----------------------------------------------------------------------
    def _export_source_template(self):
        """Export a template CSV that users can fill in with their city's sources."""
        filepath = filedialog.asksaveasfilename(
            title="Save Source Template",
            defaultextension=".csv",
            initialfile="my-city-sources.csv",
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not filepath:
            return

        # Pre-fill with any values already in config
        city = self.config_data.get("city_name", "")
        state = self.config_data.get("state", "")
        records_law = self.config_data.get("state_open_records_law", "")
        clerk = self.config_data.get("city_clerk_contact", "")

        template = f"""# ============================================================
# Civic Transparency Toolkit — Source List
# ============================================================
#
# HOW TO USE THIS FILE:
#
#   1. Fill in your city info below (replace the example values)
#   2. Add your sources — as many as you want
#   3. Save this file, then click "Import Sources" in the toolkit
#
# You can add sources THREE ways (mix and match):
#
#   EASY: Just paste URLs, one per line:
#     https://yourcity.gov/news
#     https://yourschooldistrict.org/category/news/
#
#   LABELED: Name followed by URL:
#     City News Page: https://yourcity.gov/news
#     School District News: https://yourschooldistrict.org/category/news/
#
#   DETAILED: Name, URL, Type, Category (comma-separated):
#     City News Page, https://yourcity.gov/news, Official Record, Government
#     Local Newspaper, https://localnews.com/, News, Journalism
#     (You can also use A/B/C instead of the full type names)
#
# Dump in as many URLs as you want. 5 or 50 — the toolkit
# searches them all. You can always edit them later in the app.
#
# ============================================================
# CITY INFO (auto-detected during import)
# ============================================================
#
# city: {city or 'YourCity'}
# state: {state or 'YourState'}
# state_open_records_law: {records_law or 'CORA, FOIA, OPRA, etc.'}
# city_clerk_contact: {clerk or 'cityclerk@yourcity.gov'}
#
# ============================================================
# SOURCE TYPES (the "Type" column, if you use detailed format)
# ============================================================
#
#   Official Record  (or A) = Government websites, agendas, meeting
#       videos, school district sites, transit agencies, .gov anything
#   News             (or B) = Newspapers, TV stations, news websites
#   Community        (or C) = Reddit, Nextdoor, Facebook groups, blogs
#
#   Not sure? Use News. The toolkit will search it either way.
#   If you just paste a URL with no type, it defaults to News.
#
# CATEGORIES (optional, helps organize in the app):
#   Government, Education, Journalism, Transit, Community, Legal, General
#
# TIP: Sources with "youtube" in the URL are also used for
#      transcript fetching — great for meeting recordings.
#
# ============================================================
# YOUR SOURCES (add as many as you need)
# ============================================================
#
# --- Official Records (checked daily) ---
{city or 'YourCity'} City Website, https://yourcity.gov/, Official Record, Government
{city or 'YourCity'} Agenda Portal, https://yourcity.primegov.com/, Official Record, Government
{city or 'YourCity'} News Page, https://yourcity.gov/news, Official Record, Government
{city or 'YourCity'} YouTube, https://www.youtube.com/@yourcitychannel, Official Record, Government
YourCounty County Government, https://yourcounty.gov/, Official Record, Government
Your School District, https://yourschooldistrict.org/, Official Record, Education
Your Transit Agency, https://yourtransit.org/, Official Record, Transit
#
# --- News Outlets ---
Your Local Newspaper, https://localnews.com/, News, Journalism
#
# --- Community Sources (optional — paste any URLs you want monitored) ---
# Your City Subreddit, https://reddit.com/r/yourcity, Community, Community
# Local Facebook Group, https://facebook.com/groups/yourcity, Community, Community
# Nextdoor, https://nextdoor.com/, Community, Community
#
# --- Paste additional URLs below this line ---
# (one per line, or use any format shown above)
#
"""

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(template)
            messagebox.showinfo("Template Saved",
                f"Template saved to:\n{filepath}\n\n"
                "Open it in any text editor, fill in your city's info and sources, "
                "then click 'Import Sources' to load it.")
            self.status_label.configure(text=f"Template saved to {os.path.basename(filepath)}")
        except IOError as e:
            messagebox.showerror("Save Error", f"Could not save template: {e}")

    # -----------------------------------------------------------------------
    # First run check
    # -----------------------------------------------------------------------
    def _check_first_run(self):
        """If no API key is set, show a welcome message."""
        if not self.config_data.get("api_key"):
            self.output_text.insert("1.0",
                "Welcome to the Civic Transparency Toolkit!\n\n"
                "This tool searches public government records, news sources,\n"
                "and community feeds for your city, then writes easy-to-read\n"
                "stories you can share with your neighbors.\n\n"
                "IMPORTANT: This tool uses the Claude AI service, which\n"
                "charges a small fee each time it runs (about $0.05-$0.25\n"
                "per daily run). You'll need an API key from Anthropic.\n\n"
                "Getting started takes about 5 minutes:\n\n"
                "  1. GET YOUR API KEY\n"
                "     Go to console.anthropic.com, create a free account,\n"
                "     and generate an API key. Then click 'Settings' in the\n"
                "     sidebar to paste it in.\n\n"
                "  2. SET UP YOUR CITY\n"
                "     Click 'City & Sources' to enter your city name,\n"
                "     state, and the websites you want monitored.\n\n"
                "  3. ADD MORE SOURCES (optional)\n"
                "     Click 'Export Template' to get a starter file, fill\n"
                "     in your city's websites, then click 'Import Sources'\n"
                "     to load them. You can add as many as you want.\n\n"
                "  4. RUN IT\n"
                "     Pick 'Find Today's News' and press 'Go'.\n"
                "     The toolkit will search your sources, find stories,\n"
                "     and write them up for you.\n\n"
                "What you can do:\n\n"
                "  Find Today's News — The main one. Finds stories, writes\n"
                "    them up, checks facts, and produces ready-to-share articles.\n\n"
                "  Dig Deeper — Looks for patterns and leads that might\n"
                "    be worth investigating.\n\n"
                "  Write a Story — Enter any topic and get a complete story.\n\n"
                "  Run a Single Step — Run any individual step by itself.\n"
            )
        else:
            self._on_lane_change()
