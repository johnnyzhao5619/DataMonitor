"""Basic ttk theme mapping using shared theme tokens."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from datamonitor.core.theme_tokens import (
    ThemePaletteColors,
    ThemeSurfaceColors,
    ThemeTokens,
)


def _light_tokens() -> ThemeTokens:
    return ThemeTokens(
        palette=ThemePaletteColors(
            window="#FFFFFF",
            window_text="#201F1E",
            base="#F5F5F5",
            alternate_base="#F0F0F0",
            tooltip_base="#FFFFFF",
            tooltip_text="#201F1E",
            text="#201F1E",
            button="#FFFFFF",
            button_text="#201F1E",
            bright_text="#C42B1C",
            highlight="#6264A7",
            highlighted_text="#FFFFFF",
            link="#005FB8",
            link_visited="#6B69D6",
            placeholder_text="#605E5C",
        ),
        colors=ThemeSurfaceColors(
            window_bg="#F8F8F8",
            window_text="#201F1E",
            heading_text="#11100F",
            accent="#4F52B2",
            accent_text="#FFFFFF",
            accent_hover="#5F62C3",
            accent_pressed="#3D3F92",
            accent_disabled_bg="#E1DFDD",
            accent_disabled_text="#8A8886",
            navigation_panel_bg="#F3F2F1",
            navigation_border="#E1DFDD",
            navigation_button_bg="#F3F2F1",
            navigation_text="#201F1E",
            navigation_hover_bg="#E1DFDD",
            navigation_hover_text="#11100F",
            navigation_checked_bg="#D0D0E8",
            navigation_checked_text="#11100F",
            card_bg="#FFFFFF",
            card_border="#E1DFDD",
            card_title="#201F1E",
            hint_text="#605E5C",
            error_text="#A4262C",
            input_bg="#FFFFFF",
            input_border="#E1DFDD",
            input_text="#201F1E",
            input_placeholder="#605E5C",
            popup_bg="#FFFFFF",
            popup_border="#E1DFDD",
            status_bg="#FFFFFF",
            status_border="#E1DFDD",
            status_text="#201F1E",
            tab_bg="#FFFFFF",
            tab_border="#E1DFDD",
            tab_text="#201F1E",
            tab_selected_bg="#F3F2F1",
            tab_selected_text="#11100F",
            tooltip_bg="#FFFFFF",
            tooltip_text="#201F1E",
            tooltip_border="#E1DFDD",
            splitter="#E1DFDD",
            scrollarea_bg="transparent",
            selection_bg="#6264A7",
            selection_text="#FFFFFF",
            list_selection_bg="#6264A7",
            list_selection_text="#FFFFFF",
            groupbox_title="#201F1E",
        ),
    )


def _dark_tokens() -> ThemeTokens:
    return ThemeTokens(
        palette=ThemePaletteColors(
            window="#1F1F24",
            window_text="#F3F2F1",
            base="#1F1F24",
            alternate_base="#2D2C30",
            tooltip_base="#2D2C30",
            tooltip_text="#F3F2F1",
            text="#F3F2F1",
            button="#2D2C30",
            button_text="#F3F2F1",
            bright_text="#F1707B",
            highlight="#8B8CC7",
            highlighted_text="#1F1F24",
            link="#C8C6C4",
            link_visited="#A19F9D",
            placeholder_text="#A19F9D",
        ),
        colors=ThemeSurfaceColors(
            window_bg="#1F1F24",
            window_text="#F3F2F1",
            heading_text="#FFFFFF",
            accent="#464775",
            accent_text="#FFFFFF",
            accent_hover="#5B5C94",
            accent_pressed="#32315A",
            accent_disabled_bg="#2D2C3A",
            accent_disabled_text="#8A8886",
            navigation_panel_bg="#252526",
            navigation_border="#3B3A39",
            navigation_button_bg="#252526",
            navigation_text="#F3F2F1",
            navigation_hover_bg="#3B3A39",
            navigation_hover_text="#FFFFFF",
            navigation_checked_bg="#3F3F46",
            navigation_checked_text="#FFFFFF",
            card_bg="#2D2C30",
            card_border="#3B3A39",
            card_title="#F3F2F1",
            hint_text="#C8C6C4",
            error_text="#F1707B",
            input_bg="#1F1F24",
            input_border="#3B3A39",
            input_text="#F3F2F1",
            input_placeholder="#A19F9D",
            popup_bg="#2D2C30",
            popup_border="#3B3A39",
            status_bg="#2D2C30",
            status_border="#3B3A39",
            status_text="#F3F2F1",
            tab_bg="#302F3A",
            tab_border="#3B3A39",
            tab_text="#C8C6C4",
            tab_selected_bg="#1F1F24",
            tab_selected_text="#FFFFFF",
            tooltip_bg="#2D2C30",
            tooltip_text="#F3F2F1",
            tooltip_border="#3B3A39",
            splitter="#3B3A39",
            scrollarea_bg="transparent",
            selection_bg="#8B8CC7",
            selection_text="#1F1F24",
            list_selection_bg="#8B8CC7",
            list_selection_text="#1F1F24",
            groupbox_title="#F3F2F1",
        ),
    )


def apply_theme(root: tk.Misc, style: ttk.Style, tokens: ThemeTokens) -> None:
    """Apply a minimal theme mapping to ttk styles."""

    colors = tokens.colors
    palette = tokens.palette
    font_family = tokens.font_family.strip('"')

    # Use a themable engine so custom colors take effect (native themes ignore many options)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    root.configure(bg=colors.window_bg)
    # Apply defaults to classic Tk widgets used in the app
    # Apply defaults to classic Tk widgets used in the app
    root.option_add("*Text.background", colors.input_bg)
    root.option_add("*Text*background", colors.input_bg)
    root.option_add("*Text.foreground", colors.input_text)
    root.option_add("*Text*foreground", colors.input_text)
    root.option_add("*Text.insertBackground", colors.input_text)
    root.option_add("*Text.selectBackground", colors.selection_bg)
    root.option_add("*Text.selectForeground", colors.selection_text)
    root.option_add("*Listbox.background", colors.input_bg)
    root.option_add("*Listbox*background", colors.input_bg)
    root.option_add("*Listbox.foreground", colors.input_text)
    root.option_add("*Listbox*foreground", colors.input_text)
    root.option_add("*Listbox.selectBackground", colors.list_selection_bg)
    root.option_add("*Listbox.selectForeground", colors.list_selection_text)
    root.option_add("*Label.background", colors.card_bg)
    root.option_add("*Label.foreground", colors.window_text)
    root.option_add("*Frame.background", colors.window_bg)
    root.option_add("*Labelframe.background", colors.card_bg)
    root.option_add("*Labelframe.foreground", colors.window_text)

    style.configure(
        ".",
        background=colors.window_bg,
        foreground=colors.window_text,
        font=(font_family, 10),
    )
    style.configure(
        "TFrame",
        background=colors.window_bg,
    )
    style.configure(
        "TLabel",
        background=colors.card_bg,
        foreground=colors.window_text,
    )
    style.configure(
        "Nav.TFrame",
        background=colors.navigation_panel_bg,
        bordercolor=colors.navigation_border,
        relief="solid",
        borderwidth=1,
    )
    style.configure(
        "CardTitle.TLabel",
        background=colors.card_bg,
        foreground=colors.card_title,
        font=(font_family, 12, "bold"),
    )
    style.configure(
        "TLabelframe",
        background=colors.card_bg,
        foreground=colors.window_text,
        bordercolor=colors.card_border,
        relief="solid",
        borderwidth=1,
    )
    style.configure(
        "TLabelframe.Label",
        background=colors.card_bg,
        foreground=colors.card_title,
    )
    style.configure(
        "TButton",
        background=colors.accent,
        foreground=colors.accent_text,
        padding=6,
        borderwidth=1,
        relief="solid",
    )
    style.map(
        "TButton",
        background=[
            ("active", colors.accent_hover),
            ("pressed", colors.accent_pressed),
            ("disabled", colors.accent_disabled_bg),
        ],
        foreground=[
            ("disabled", colors.accent_disabled_text or colors.window_text),
            ("!disabled", colors.accent_text),
        ],
        bordercolor=[
            ("disabled", colors.accent_disabled_bg),
            ("pressed", colors.accent_pressed),
            ("!disabled", colors.accent),
        ],
        relief=[("pressed", "sunken"), ("disabled", "solid")],
    )
    style.configure(
        "Nav.TButton",
        background=colors.navigation_button_bg,
        foreground=colors.navigation_text or colors.window_text,
        padding=(12, 10),
        anchor="w",
        borderwidth=1,
        relief="solid",
    )
    style.map(
        "Nav.TButton",
        background=[
            ("active", colors.navigation_hover_bg),
            ("pressed", colors.navigation_checked_bg),
            ("selected", colors.navigation_checked_bg),
            ("disabled", colors.navigation_panel_bg),
        ],
        foreground=[
            ("active", colors.navigation_hover_text),
            ("selected", colors.navigation_checked_text),
            ("disabled", colors.navigation_text or colors.window_text),
        ],
        relief=[("pressed", "sunken"), ("selected", "flat")],
    )
    style.configure(
        "NavHeading.TLabel",
        background=colors.navigation_panel_bg,
        foreground=colors.navigation_text or colors.window_text or "#11100F",
        font=(font_family, 12, "bold"),
        anchor="center",
    )
    style.configure(
        "TEntry",
        fieldbackground=colors.input_bg,
        foreground=colors.input_text,
        bordercolor=colors.input_border,
        insertcolor=colors.input_text,
    )
    style.map(
        "TEntry",
        fieldbackground=[("disabled", colors.accent_disabled_bg)],
        foreground=[("disabled", colors.accent_disabled_text or colors.input_text)],
        bordercolor=[("disabled", colors.accent_disabled_bg)],
    )
    style.configure(
        "TSpinbox",
        fieldbackground=colors.input_bg,
        foreground=colors.input_text,
        bordercolor=colors.input_border,
        insertcolor=colors.input_text,
        arrowcolor=colors.input_text,
    )
    style.map(
        "TSpinbox",
        fieldbackground=[("disabled", colors.accent_disabled_bg)],
        foreground=[("disabled", colors.accent_disabled_text or colors.input_text)],
        arrowcolor=[
            ("disabled", colors.accent_disabled_text or colors.input_text),
            ("!disabled", colors.input_text),
        ],
        bordercolor=[("disabled", colors.accent_disabled_bg)],
    )
    style.configure(
        "TCombobox",
        fieldbackground=colors.input_bg,
        foreground=colors.input_text,
        selectbackground=colors.selection_bg,
        selectforeground=colors.selection_text,
        background=colors.input_bg,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", colors.input_bg)],
        foreground=[("disabled", colors.accent_disabled_text or colors.input_text)],
        background=[("disabled", colors.accent_disabled_bg)],
        arrowcolor=[
            ("disabled", colors.accent_disabled_text or colors.input_text),
            ("!disabled", colors.input_text),
        ],
    )
    style.configure(
        "TNotebook",
        background=colors.tab_bg,
        tabmargins=2,
    )
    style.configure(
        "TNotebook.Tab",
        background=colors.tab_bg,
        foreground=colors.tab_text,
        padding=(10, 6),
        bordercolor=colors.tab_border,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", colors.tab_selected_bg)],
        foreground=[("selected", colors.tab_selected_text)],
    )


def apply_text_theme(widget: tk.Text) -> None:
    """Apply entry-style colors to a Tk text widget to match the active ttk theme."""

    style = ttk.Style(widget)
    bg = style.lookup("TEntry", "fieldbackground") or widget.cget("background")
    fg = style.lookup("TEntry", "foreground") or widget.cget("foreground")
    widget.configure(bg=bg, fg=fg, insertbackground=fg)


THEMES: dict[str, ThemeTokens] = {
    "light": _light_tokens(),
    "dark": _dark_tokens(),
}

DEFAULT_THEME = THEMES["light"]
