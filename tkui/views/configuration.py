"""Tkinter configuration view for monitor definitions."""

from __future__ import annotations

import json
import tkinter as tk
from dataclasses import asdict
from tkinter import ttk
from typing import Dict, List, Optional

from datamonitor.core import EventBus, Translator
from datamonitor.domain import settings
from tkui.theme import apply_text_theme


class ConfigurationView(ttk.Frame):
    """List and edit monitors using shared configuration helpers."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        translator: Translator,
        event_bus: EventBus,
    ) -> None:
        super().__init__(master, padding=(8, 8, 8, 8))
        self._translator = translator
        self._event_bus = event_bus
        self._monitors: List[Dict[str, object]] = []
        self._current_index: int | None = None
        self._style = ttk.Style(self)
        self._build_ui()
        self.retranslate()
        self.reload()
        self._workspace_subscription = self._event_bus.subscribe(
            "workspaceChanged", self._on_workspace_changed
        )
        self.bind("<Destroy>", self._on_destroy, add="+")

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Monitor list
        list_card = ttk.LabelFrame(self, padding=8)
        list_card.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        list_card.rowconfigure(1, weight=1)

        self.list_label = ttk.Label(list_card, text="")
        self.list_label.grid(row=0, column=0, sticky="w")

        self.monitor_list = tk.Listbox(
            list_card,
            height=12,
            relief="flat",
            borderwidth=1,
            highlightthickness=0,
            exportselection=False,
        )
        self.monitor_list.grid(row=1, column=0, sticky="ns", pady=(4, 6))
        self.monitor_list.bind("<<ListboxSelect>>", self._on_select)
        self._apply_list_theme(self.monitor_list)

        btns = ttk.Frame(list_card)
        btns.grid(row=2, column=0, pady=(0, 4), sticky="ew")
        self.add_button = ttk.Button(btns, text="", command=self._add_monitor)
        self.add_button.pack(side="left", padx=(0, 4))
        self.remove_button = ttk.Button(btns,
                                        text="",
                                        command=self._remove_monitor)
        self.remove_button.pack(side="left")

        # Form
        form_card = ttk.LabelFrame(self, padding=12)
        form_card.grid(row=0, column=1, sticky="nsew")
        form_card.columnconfigure(1, weight=1)

        self._label_widgets: List[ttk.Label] = []

        def add_row(label: str, widget):
            row = form_card.grid_size()[1]
            lbl = ttk.Label(form_card, text=label)
            lbl.grid(row=row,
                     column=0,
                     sticky="w",
                     pady=2,
                     padx=(0, 6))
            self._label_widgets.append(lbl)
            widget.grid(row=row, column=1, sticky="ew", pady=2)

        self.name_var = tk.StringVar()
        self.url_var = tk.StringVar()
        self.type_var = tk.StringVar()
        self.interval_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.language_var = tk.StringVar()
        self.payload_text = tk.Text(
            form_card,
            height=4,
            width=40,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
        )
        self.headers_text = tk.Text(
            form_card,
            height=4,
            width=40,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
        )
        apply_text_theme(self.payload_text)
        apply_text_theme(self.headers_text)

        add_row("Name", ttk.Entry(form_card, textvariable=self.name_var))
        add_row("URL", ttk.Entry(form_card, textvariable=self.url_var))
        type_box = ttk.Combobox(
            form_card,
            textvariable=self.type_var,
            values=sorted(settings.supported_monitor_types()),
            state="readonly",
        )
        add_row("Type", type_box)
        add_row("Interval (s)", ttk.Entry(form_card, textvariable=self.interval_var))
        add_row("Email", ttk.Entry(form_card, textvariable=self.email_var))
        self.email_hint = ttk.Label(
            form_card,
            style="Small.TLabel",
        )
        self.email_hint.grid(row=form_card.grid_size()[1],
                             column=1,
                             sticky="w",
                             pady=(0, 4))
        add_row("Language", ttk.Entry(form_card, textvariable=self.language_var))

        add_row("Payload (JSON)", self.payload_text)
        add_row("Headers (JSON)", self.headers_text)

        actions = ttk.Frame(form_card)
        actions.grid(row=form_card.grid_size()[1], column=0, columnspan=2, pady=(8, 0), sticky="e")
        self.save_button = ttk.Button(actions, text="", command=self._save_all)
        self.save_button.pack(side="right")

    # ------------------------------------------------------------------
    def retranslate(self) -> None:
        t = self._translator.translate
        self.list_label.config(text=t("Configuration", "Monitors"))
        self.add_button.config(text=t("Configuration", "Add"))
        self.remove_button.config(text=t("Configuration", "Remove"))
        self.save_button.config(text=t("Configuration", "Save"))
        label_keys = (
            "Name",
            "URL",
            "Type",
            "Interval (s)",
            "Email",
            "Language",
            "Payload (JSON)",
            "Headers (JSON)",
        )
        for widget, key in zip(self._label_widgets, label_keys):
            widget.config(text=t("Configuration", key))
        self.email_hint.config(
            text=t(
                "Configuration",
                "Optional; comma-separated. Empty uses global recipients.",
            ))

    # ------------------------------------------------------------------
    def reload(self) -> None:
        self._monitors = [
            self._normalise_monitor_dict(asdict(item))
            for item in settings.read_monitor_list()
        ]
        self._refresh_list()
        if self._monitors:
            self._select_index(0)
        else:
            self._clear_form()

    def _refresh_list(self) -> None:
        self.monitor_list.delete(0, tk.END)
        for monitor in self._monitors:
            label = f"{monitor.get('name','')} [{monitor.get('type','')}]"
            self.monitor_list.insert(tk.END, label)

    def _on_select(self, _event=None) -> None:
        selection = self.monitor_list.curselection()
        if not selection:
            return
        index = selection[0]
        self._current_index = index
        self._load_into_form(index)

    def _load_into_form(self, index: int) -> None:
        monitor = self._monitors[index]
        self.name_var.set(monitor.get("name", ""))
        self.url_var.set(monitor.get("url", ""))
        self.type_var.set(monitor.get("monitor_type", monitor.get("type", "")))
        self.interval_var.set(str(monitor.get("interval", "")))
        self.email_var.set(monitor.get("email", ""))
        self.language_var.set(monitor.get("language", ""))
        self._set_text(self.payload_text, monitor.get("payload"))
        self._set_text(self.headers_text, monitor.get("headers"))

    def _set_text(self, widget: tk.Text, value) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        if value:
            widget.insert("1.0", json.dumps(value, indent=2, ensure_ascii=False))
        widget.configure(state="normal")

    def _on_workspace_changed(self, *_args, **_kwargs) -> None:
        self.reload()

    def _on_destroy(self, _event=None) -> None:
        if hasattr(self, "_workspace_subscription") and callable(
                self._workspace_subscription):
            try:
                self._workspace_subscription()
            except Exception:
                pass

    # ------------------------------------------------------------------
    def _add_monitor(self) -> None:
        new = {
            "name": self._translator.translate("Configuration", "New Monitor"),
            "url": "",
            "type": "GET",
            "interval": 60,
            "email": "",
        }
        self._monitors.append(new)
        self._refresh_list()
        self._select_index(len(self._monitors) - 1)

    def _remove_monitor(self) -> None:
        selection = self.monitor_list.curselection()
        if not selection:
            return
        index = selection[0]
        self._monitors.pop(index)
        self._refresh_list()
        if self._monitors:
            new_index = min(index, len(self._monitors) - 1)
            self._select_index(new_index)
        else:
            self._clear_form()
            self._current_index = None

    def _clear_form(self) -> None:
        for var in (
                self.name_var,
                self.url_var,
                self.type_var,
                self.interval_var,
                self.email_var,
                self.language_var,
        ):
            var.set("")
        for widget in (self.payload_text, self.headers_text):
            widget.delete("1.0", tk.END)

    def _save_all(self) -> None:
        selection = self.monitor_list.curselection()
        try:
            target_index: int | None = None
            if selection:
                target_index = selection[0]
            elif self._current_index is not None:
                target_index = self._current_index
            elif self._monitors:
                target_index = 0
            if target_index is not None:
                self._sync_form_to_model(target_index)
        except Exception as exc:
            self._event_bus.emit(
                "statusMessage",
                self._translator.translate("Configuration",
                                           "Invalid monitor data: {error}").
                format(error=exc),
                5000,
            )
            return
        try:
            settings.write_monitor_list(self._monitors)
        except Exception as exc:
            self._event_bus.emit(
                "statusMessage",
                self._translator.translate("Configuration",
                                           "Failed to save monitors: {error}").
                format(error=exc),
                5000,
            )
            return

        self._event_bus.emit(
            "statusMessage",
            self._translator.translate("Configuration", "Monitors saved"),
            3000,
        )
        self.reload()

    def _sync_form_to_model(self, index: int) -> None:
        if index >= len(self._monitors):
            return
        t = self._translator.translate
        payload = self._parse_json(self.payload_text.get("1.0", tk.END))
        headers = self._parse_json(self.headers_text.get("1.0", tk.END))
        name = self.name_var.get().strip()
        url = self.url_var.get().strip()
        monitor_type = (self.type_var.get().strip() or "GET").upper()
        interval_val = self.interval_var.get().strip()
        email = self.email_var.get().strip()
        language = self.language_var.get().strip()

        if not name:
            raise ValueError(t("Configuration", "Name is required"))
        if not url:
            raise ValueError(t("Configuration", "URL is required"))
        try:
            interval = int(interval_val) if interval_val else 60
        except ValueError as exc:
            raise ValueError(
                t("Configuration",
                  "Interval must be an integer")) from exc
        if interval <= 0:
            raise ValueError(
                t("Configuration",
                  "Interval must be greater than 0"))

        self._monitors[index] = {
            "name": name,
            "url": url,
            "type": monitor_type,
            "interval": interval,
            "email": email,
            "language": language,
            "payload": payload,
            "headers": headers,
        }

    def _parse_json(self, text: str):
        cleaned = text.strip()
        if not cleaned:
            return None
        try:
            value = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(
                self._translator.translate("Configuration",
                                           "Invalid JSON: {error}").format(
                                               error=exc)) from exc
        if not isinstance(value, dict):
            raise ValueError(
                self._translator.translate("Configuration",
                                           "JSON must be an object"))
        return value

    def _apply_list_theme(self, widget: tk.Listbox) -> None:
        bg = (self._style.lookup("TFrame", "background")
              or self._style.lookup("TLabelframe", "background")
              or widget.cget("background"))
        fg = self._style.lookup("TLabel", "foreground") or widget.cget("foreground")
        sel_bg = self._style.lookup("TButton", "background") or bg
        sel_fg = self._style.lookup("TButton", "foreground") or fg
        widget.configure(
            bg=bg,
            fg=fg,
            selectbackground=sel_bg,
            selectforeground=sel_fg,
            highlightthickness=0,
            borderwidth=0,
        )

    def _normalise_monitor_dict(self, data: dict) -> dict:
        """Ensure monitor dictionaries use the keys expected by write_monitor_list."""
        normalized = dict(data)
        # prefer type key
        if "monitor_type" in normalized and "type" not in normalized:
            normalized["type"] = normalized.get("monitor_type")
        # coerce optional fields to strings where appropriate
        for key in ("email", "language"):
            val = normalized.get(key)
            if val is None:
                normalized[key] = ""
            else:
                normalized[key] = str(val).strip()
        # ensure interval is int-compatible
        if "interval" in normalized:
            try:
                normalized["interval"] = int(normalized["interval"])
            except Exception:
                normalized["interval"] = 0
        return normalized

    def _select_index(self, index: int) -> None:
        if not self._monitors:
            return
        index = max(0, min(index, len(self._monitors) - 1))
        self.monitor_list.selection_clear(0, tk.END)
        self.monitor_list.selection_set(index)
        self.monitor_list.activate(index)
        self._current_index = index
        self._load_into_form(index)
