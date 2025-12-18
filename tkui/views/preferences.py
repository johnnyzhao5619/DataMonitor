"""Tkinter preferences view for timezone, language, and workspace management."""

from __future__ import annotations

import datetime as _dt
import threading
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Optional

from datamonitor.core import EventBus, Translator
from datamonitor.domain import settings, preferences
from monitoring import send_email
from tkui.theme import apply_text_theme


class PreferencesView(ttk.Frame):
    """Manage runtime preferences: timezone, language, workspace."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        translator: Translator,
        event_bus: EventBus,
        available_themes: Optional[list[str]] = None,
    ) -> None:
        super().__init__(master, padding=(12, 12, 12, 12))
        self._translator = translator
        self._event_bus = event_bus
        self._available_themes = available_themes or ["light"]
        self._label_texts: dict[str, ttk.Label] = {}
        self._checkbuttons: dict[str, ttk.Checkbutton] = {}

        self._build_ui()
        self.retranslate()
        self._load_initial()
        self._dirty = False

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)

        # Scrollable container
        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        vscroll = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vscroll.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.body = ttk.Frame(canvas)
        self.body.columnconfigure(0, weight=1)
        self.body_id = canvas.create_window((0, 0),
                                            window=self.body,
                                            anchor="nw")

        def _on_configure(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Keep body width in sync with canvas width
            canvas.itemconfig(self.body_id, width=canvas.winfo_width())

        def _on_mousewheel(event):
            delta = event.delta
            if delta == 0:
                return
            canvas.yview_scroll(int(-1 * (delta / 120)), "units")

        def _bind_wheel(_event=None):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_wheel(_event=None):
            canvas.unbind_all("<MouseWheel>")

        self.body.bind("<Configure>", _on_configure, add="+")
        canvas.bind("<Configure>", _on_configure, add="+")
        self.body.bind("<Enter>", _bind_wheel, add="+")
        self.body.bind("<Leave>", _unbind_wheel, add="+")

        # Timezone
        tz_card = ttk.LabelFrame(self.body, padding=12)
        tz_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        tz_card.columnconfigure(1, weight=1)
        self.tz_title = ttk.Label(tz_card, text="", style="CardTitle.TLabel")
        self.tz_title.grid(row=0, column=0, sticky="w", columnspan=2, pady=(0, 6))

        self.tz_value_label = ttk.Label(tz_card, text="")
        self.tz_value_label.grid(row=1, column=0, sticky="w")
        self.tz_spin = ttk.Spinbox(
            tz_card,
            from_=-24,
            to=24,
            increment=1,
            width=6,
            command=self._on_timezone_change,
        )
        self.tz_spin.grid(row=1, column=1, sticky="w")
        self.tz_spin.bind("<KeyRelease>", lambda _e: self._mark_dirty())
        self.tz_spin.bind("<<Increment>>", lambda _e: self._mark_dirty())
        self.tz_spin.bind("<<Decrement>>", lambda _e: self._mark_dirty())

        # Language
        lang_card = ttk.LabelFrame(self.body, padding=12)
        lang_card.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        lang_card.columnconfigure(1, weight=1)
        self.lang_title = ttk.Label(lang_card, text="", style="CardTitle.TLabel")
        self.lang_title.grid(row=0, column=0, sticky="w", columnspan=2, pady=(0, 6))

        self.lang_value_label = ttk.Label(lang_card, text="")
        self.lang_value_label.grid(row=1, column=0, sticky="w")
        self.lang_combo = ttk.Combobox(lang_card, state="readonly")
        self.lang_combo.grid(row=1, column=1, sticky="w")
        self.lang_combo.bind("<<ComboboxSelected>>",
                             lambda _e: (self._mark_dirty()))

        # Theme
        theme_card = ttk.LabelFrame(self.body, padding=12)
        theme_card.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        theme_card.columnconfigure(1, weight=1)
        self.theme_title = ttk.Label(theme_card, text="", style="CardTitle.TLabel")
        self.theme_title.grid(row=0, column=0, sticky="w", columnspan=2, pady=(0, 6))

        self.theme_value_label = ttk.Label(theme_card, text="")
        self.theme_value_label.grid(row=1, column=0, sticky="w")
        self.theme_combo = ttk.Combobox(theme_card, state="readonly")
        self.theme_combo.grid(row=1, column=1, sticky="w")
        self.theme_combo.bind("<<ComboboxSelected>>",
                              lambda _e: (self._mark_dirty()))

        # Workspace / paths
        ws_card = ttk.LabelFrame(self.body, padding=12)
        ws_card.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        ws_card.columnconfigure(1, weight=1)
        self.ws_title = ttk.Label(ws_card, text="", style="CardTitle.TLabel")
        self.ws_title.grid(row=0, column=0, sticky="w", columnspan=3, pady=(0, 6))

        self.ws_root_label = ttk.Label(ws_card, text="", style="CardTitle.TLabel")
        self.ws_root_label.grid(row=1, column=0, sticky="w", columnspan=3, pady=(6, 6))
        ws_root_row = ttk.Frame(ws_card)
        ws_root_row.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        ws_root_row.columnconfigure(0, weight=1)
        self.ws_root_entry = ttk.Entry(ws_root_row, state="readonly")
        self.ws_root_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.ws_root_browse = ttk.Button(ws_root_row,
                                         text="",
                                         command=self._pick_workspace_root)
        self.ws_root_browse.grid(row=0, column=1)

        self.config_dir_label = ttk.Label(ws_card,
                                          text="",
                                          style="CardTitle.TLabel")
        self.config_dir_label.grid(row=3, column=0, sticky="w", columnspan=3, pady=(0, 6))
        config_row = ttk.Frame(ws_card)
        config_row.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        config_row.columnconfigure(0, weight=1)
        self.config_dir_entry = ttk.Entry(config_row, state="readonly")
        self.config_dir_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.log_dir_label = ttk.Label(ws_card,
                                       text="",
                                       style="CardTitle.TLabel")
        self.log_dir_label.grid(row=5, column=0, sticky="w", columnspan=3, pady=(0, 6))
        log_row = ttk.Frame(ws_card)
        log_row.grid(row=6, column=0, columnspan=3, sticky="ew")
        log_row.columnconfigure(0, weight=1)
        self.log_dir_entry = ttk.Entry(log_row, state="readonly")
        self.log_dir_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.log_dir_browse = ttk.Button(log_row,
                                         text="",
                                         command=self._pick_log_dir)
        self.log_dir_browse.grid(row=0, column=1)

        # Logging & Mail
        lm_card = ttk.LabelFrame(self.body, padding=12)
        lm_card.grid(row=4, column=0, sticky="ew")
        lm_card.columnconfigure(1, weight=1)
        self.lm_title = ttk.Label(lm_card, text="", style="CardTitle.TLabel")
        self.lm_title.grid(row=0, column=0, sticky="w", columnspan=3, pady=(0, 6))

        # Logging settings
        self.log_title = ttk.Label(lm_card, text="", style="CardTitle.TLabel")
        self.log_title.grid(row=1, column=0, sticky="w", columnspan=3, pady=(4, 4))

        self._label_texts["Level"] = ttk.Label(lm_card, text="")
        self._label_texts["Level"].grid(row=2, column=0, sticky="w")
        self.log_level = ttk.Combobox(lm_card,
                                      state="readonly",
                                      values=["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level.grid(row=2, column=1, sticky="ew", pady=2)

        self._label_texts["Format"] = ttk.Label(lm_card, text="")
        self._label_texts["Format"].grid(row=3, column=0, sticky="w")
        self.log_format = ttk.Entry(lm_card)
        self.log_format.grid(row=3, column=1, sticky="ew", pady=2)

        self._label_texts["Date format"] = ttk.Label(lm_card, text="")
        self._label_texts["Date format"].grid(row=4, column=0, sticky="w")
        self.log_datefmt = ttk.Entry(lm_card)
        self.log_datefmt.grid(row=4, column=1, sticky="ew", pady=2)

        self._label_texts["Filename"] = ttk.Label(lm_card, text="")
        self._label_texts["Filename"].grid(row=5, column=0, sticky="w")
        self.log_filename = ttk.Entry(lm_card)
        self.log_filename.grid(row=5, column=1, sticky="ew", pady=2)

        self._label_texts["Log template"] = ttk.Label(lm_card, text="")
        self._label_texts["Log template"].grid(row=6, column=0, sticky="nw", pady=(4, 0))
        self.log_template = tk.Text(lm_card,
                                    height=4,
                                    width=50,
                                    relief="flat",
                                    borderwidth=0,
                                    highlightthickness=0)
        self.log_template.grid(row=6, column=1, sticky="ew", pady=2)

        self._label_texts["CSV header"] = ttk.Label(lm_card, text="")
        self._label_texts["CSV header"].grid(row=7, column=0, sticky="w")
        self.csv_header = ttk.Entry(lm_card)
        self.csv_header.grid(row=7, column=1, sticky="ew", pady=2)

        # Mail settings
        self.mail_title = ttk.Label(lm_card, text="", style="CardTitle.TLabel")
        self.mail_title.grid(row=8, column=0, sticky="w", columnspan=3, pady=(8, 4))

        def add_mail_row(key: str, var_row: list[int]):
            r = var_row[0]
            lbl = ttk.Label(lm_card, text="")
            lbl.grid(row=r, column=0, sticky="w")
            self._label_texts[key] = lbl
            entry = ttk.Entry(lm_card)
            entry.grid(row=r, column=1, sticky="ew", pady=2)
            var_row[0] += 1
            return entry

        mail_row = [9]
        self.mail_server = add_mail_row("SMTP server", mail_row)
        self.mail_port = add_mail_row("SMTP port", mail_row)
        self.mail_username = add_mail_row("Username", mail_row)
        self.mail_password = ttk.Entry(lm_card, show="*")
        self.mail_password.grid(row=mail_row[0], column=1, sticky="ew", pady=2)
        pwd_label = ttk.Label(lm_card, text="")
        pwd_label.grid(row=mail_row[0], column=0, sticky="w")
        self._label_texts["Password"] = pwd_label
        mail_row[0] += 1
        self.mail_from = add_mail_row("From", mail_row)
        self.mail_to = add_mail_row("To", mail_row)
        self.mail_to_hint = ttk.Label(
            lm_card,
            style="Small.TLabel",
        )
        self.mail_to_hint.grid(row=mail_row[0], column=1, sticky="w")
        mail_row[0] += 1

        opts_row = mail_row[0]
        self.use_ssl = tk.BooleanVar()
        self.use_starttls = tk.BooleanVar()
        ssl_btn = ttk.Checkbutton(lm_card, text="", variable=self.use_ssl)
        ssl_btn.grid(row=opts_row, column=0, sticky="w", pady=2)
        starttls_btn = ttk.Checkbutton(lm_card,
                                       text="",
                                       variable=self.use_starttls)
        starttls_btn.grid(row=opts_row, column=1, sticky="w", pady=2)
        self._checkbuttons["Use SSL"] = ssl_btn
        self._checkbuttons["Use STARTTLS"] = starttls_btn
        mail_row[0] = opts_row + 1

        self._label_texts["Alert subject"] = ttk.Label(lm_card, text="")
        self._label_texts["Alert subject"].grid(row=mail_row[0],
                                                column=0,
                                                sticky="w")
        self.alert_subject = ttk.Entry(lm_card)
        self.alert_subject.grid(row=mail_row[0], column=1, sticky="ew", pady=2)
        mail_row[0] += 1

        self._label_texts["Alert body"] = ttk.Label(lm_card, text="")
        self._label_texts["Alert body"].grid(row=mail_row[0],
                                             column=0,
                                             sticky="nw")
        self.alert_body = tk.Text(lm_card,
                                  height=3,
                                  width=50,
                                  relief="flat",
                                  borderwidth=0,
                                  highlightthickness=0)
        self.alert_body.grid(row=mail_row[0], column=1, sticky="ew", pady=2)
        mail_row[0] += 1

        self._label_texts["Recovery subject"] = ttk.Label(lm_card, text="")
        self._label_texts["Recovery subject"].grid(row=mail_row[0],
                                                   column=0,
                                                   sticky="w")
        self.recovery_subject = ttk.Entry(lm_card)
        self.recovery_subject.grid(row=mail_row[0],
                                   column=1,
                                   sticky="ew",
                                   pady=2)
        mail_row[0] += 1

        self._label_texts["Recovery body"] = ttk.Label(lm_card, text="")
        self._label_texts["Recovery body"].grid(row=mail_row[0],
                                                column=0,
                                                sticky="nw")
        self.recovery_body = tk.Text(lm_card,
                                     height=3,
                                     width=50,
                                     relief="flat",
                                     borderwidth=0,
                                     highlightthickness=0)
        self.recovery_body.grid(row=mail_row[0],
                                column=1,
                                sticky="ew",
                                pady=2)
        mail_row[0] += 1

        self.test_mail_button = ttk.Button(
            lm_card,
            text="",
            command=self._send_test_email,
        )
        self.test_mail_button.grid(row=mail_row[0],
                                   column=1,
                                   sticky="e",
                                   pady=(6, 0))

        actions = ttk.Frame(self.body)
        actions.grid(row=5, column=0, sticky="e", pady=(8, 0))
        self.apply_button = ttk.Button(actions,
                                       text="",
                                       command=self._apply_changes)
        self.apply_button.pack(side="right", padx=(6, 0))
        self.save_button = ttk.Button(actions,
                                      text="",
                                      command=self._save_and_reload)
        self.save_button.pack(side="right")

    # ------------------------------------------------------------------
    def retranslate(self) -> None:
        t = self._translator.translate
        self.tz_title.config(text=t("Preferences", "Time Zone"))
        self.tz_value_label.config(text=t("Preferences", "Offset (hours)"))

        self.lang_title.config(text=t("Preferences", "Language"))
        self.lang_value_label.config(text=t("Preferences", "Current"))

        self.theme_title.config(text=t("Preferences", "Theme"))
        self.theme_value_label.config(text=t("Preferences", "Current"))

        self.ws_title.config(text=t("Preferences", "Configuration Workspace"))
        self.ws_root_label.config(text=t("Preferences", "Workspace root"))
        self.ws_root_browse.config(text=t("Preferences", "Browse"))
        self.config_dir_label.config(text=t("Preferences", "Config directory"))
        self.log_dir_label.config(text=t("Preferences", "Log directory"))
        self.log_dir_browse.config(text=t("Preferences", "Browse"))
        self.lm_title.config(text=t("Preferences", "Logging & Mail"))
        self.log_title.config(text=t("Preferences", "Logging"))
        self.mail_title.config(text=t("Preferences", "Mail"))
        self.apply_button.config(text=t("Preferences", "Apply"))
        self.save_button.config(text=t("Preferences", "Save and Reload"))
        for key, widget in self._label_texts.items():
            widget.config(text=t("Preferences", key))
        for key, widget in self._checkbuttons.items():
            widget.config(text=t("Preferences", key))
        self.mail_to_hint.config(
            text=t("Preferences",
                   "Comma-separated; leave empty to use per-monitor email."))
        self.test_mail_button.config(text=t("Preferences", "Send test email"))

    # ------------------------------------------------------------------
    def _load_initial(self) -> None:
        self.tz_spin.delete(0, tk.END)
        self.tz_spin.insert(0, str(preferences.get_timezone()))

        languages = list(settings.available_languages())
        self.lang_combo["values"] = languages
        current_lang = settings.get_language()
        self.lang_combo.set(current_lang)
        self.lang_value_label.config(
            text=self._translator.translate("Preferences", "Current") +
            f": {current_lang}")

        self.theme_combo["values"] = self._available_themes
        current_theme = self._available_themes[0] if self._available_themes else ""
        self.theme_combo.set(current_theme)
        self.theme_value_label.config(
            text=self._translator.translate("Preferences", "Current") +
            f": {current_theme}")

        self._load_paths()
        self._load_logging_settings()
        self._load_mail_settings()
        self._load_templates()

    # ------------------------------------------------------------------
    def _on_timezone_change(self) -> None:
        try:
            offset = int(self.tz_spin.get())
        except Exception:
            return
        preferences.set_timezone(str(offset))
        self._event_bus.emit("timezoneChanged", offset)
        self._event_bus.emit(
            "statusMessage",
            self._translator.translate("Preferences", "Timezone updated"),
            3000,
        )

    def _on_language_change(self) -> None:
        language = self.lang_combo.get().strip()
        if not language:
            return
        settings.set_language(language)
        self._event_bus.emit("languageChanged", language)
        self._event_bus.emit(
            "statusMessage",
            self._translator.translate("Preferences",
                                       "Language updated to {lang}").format(
                                           lang=language),
            3000,
        )

    # ------------------------------------------------------------------
    def _load_paths(self) -> None:
        """Load active workspace root, config dir, and log dir into the UI."""
        active = settings.active_configuration_workspace()
        root_path = active.get("path", "") if isinstance(active, dict) else ""

        config_dir = settings.get_config_directory()
        log_settings = settings.get_logging_settings()
        log_dir = log_settings.file_path.parent

        self._set_entry(self.ws_root_entry, root_path)
        self._set_entry(self.config_dir_entry, str(config_dir))
        self._set_entry(self.log_dir_entry, str(log_dir))

    def _pick_workspace_root(self) -> None:
        path = filedialog.askdirectory(
            title=self._translator.translate("Preferences",
                                             "Select workspace root"))
        if not path:
            return
        self._set_entry(self.ws_root_entry, path)
        self._mark_dirty()

    def _pick_log_dir(self) -> None:
        path = filedialog.askdirectory(
            title=self._translator.translate("Preferences",
                                             "Select log directory"))
        if not path:
            return
        self._set_entry(self.log_dir_entry, path)
        self._mark_dirty()

    def _set_entry(self, entry: ttk.Entry, value: str) -> None:
        entry.configure(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, value)
        entry.configure(state="readonly")

    def _fill_entry(self, entry: ttk.Entry, value: str) -> None:
        entry.configure(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, value)

    def _on_theme_change(self) -> None:
        theme = self.theme_combo.get().strip()
        if not theme:
            return
        self._event_bus.emit("themeChanged", theme)

    def _apply_changes(self) -> None:
        """Apply pending changes (timezone/language/workspace activation)."""
        self._on_timezone_change()
        self._on_language_change()
        self._on_theme_change()
        try:
            self._apply_paths()
            self._apply_logging_settings()
            self._apply_mail_settings()
            self._apply_templates()
        except ValueError as exc:
            self._event_bus.emit(
                "statusMessage",
                self._translator.translate(
                    "Preferences",
                    "Failed to apply preferences: {error}").format(
                        error=exc),
                4000,
            )
            return
        self._event_bus.emit(
            "statusMessage",
            self._translator.translate("Preferences", "Preferences applied"),
            3000,
        )
        self._dirty = False
        # Refresh displayed preferences with persisted values.
        self._load_initial()

    def _save_and_reload(self) -> None:
        """Apply changes and reload workspaces to reflect on-disk state."""
        self._apply_changes()
        self._load_paths()

    def _mark_dirty(self) -> None:
        self._dirty = True

    def _apply_paths(self) -> None:
        """Persist workspace root and log directory selections."""
        root_value = self.ws_root_entry.get().strip()
        log_dir_value = self.log_dir_entry.get().strip()

        if root_value:
            settings.add_configuration_workspace(root_value, activate=True)
            settings.ensure_initial_configuration()

        if log_dir_value:
            log_prefs = settings.get_logging_settings()
            settings.set_logging_preferences(
                level=log_prefs.level_name,
                max_size=log_prefs.max_bytes,
                backup_count=log_prefs.backup_count,
                console=log_prefs.console,
                directory=log_dir_value,
                filename=log_prefs.file_path.name,
                fmt=log_prefs.fmt,
                datefmt=log_prefs.datefmt,
            )

        # Inform the app so dependent views (e.g., Configuration) can reload.
        self._event_bus.emit("workspaceChanged", root_value or None)

    # ------------------------------------------------------------------
    # Logging & Mail helpers
    def _apply_logging_settings(self) -> None:
        log_settings = settings.get_logging_settings()
        log_dir = self.log_dir_entry.get().strip() or log_settings.file_path.parent
        settings.set_logging_preferences(
            level=self.log_level.get() or log_settings.level_name,
            max_size=log_settings.max_bytes,
            backup_count=log_settings.backup_count,
            console=log_settings.console,
            directory=log_dir,
            filename=self.log_filename.get().strip() or log_settings.file_path.name,
            fmt=self.log_format.get().strip() or log_settings.fmt,
            datefmt=self.log_datefmt.get().strip() or log_settings.datefmt,
        )

    def _apply_mail_settings(self) -> None:
        values = {
            "smtp_server": self.mail_server.get().strip(),
            "smtp_port": self.mail_port.get().strip(),
            "username": self.mail_username.get().strip(),
            "password": self.mail_password.get().strip(),
            "from_addr": self.mail_from.get().strip(),
            "to_addrs": self.mail_to.get().strip(),
            "use_ssl": self.use_ssl.get(),
            "use_starttls": self.use_starttls.get(),
            "subject": "",
        }
        settings.set_mail_settings(values)

    def _send_test_email(self) -> None:
        """Validate current mail settings and send a simple test email."""

        def _send() -> None:
            try:
                self._apply_mail_settings()
            except ValueError as exc:
                self._event_bus.emit(
                    "statusMessage",
                    self._translator.translate(
                        "Preferences",
                        "Mail settings invalid: {error}").format(error=exc),
                    4000,
                )
                return

            mail_settings = settings.get_mail_settings()
            recipients = mail_settings.get("to_addrs", "").strip()
            if not recipients:
                self._event_bus.emit(
                    "statusMessage",
                    self._translator.translate(
                        "Preferences",
                        "Test mail failed: recipients are empty"),
                    4000,
                )
                return

            subject = "DataMonitor test email"
            timestamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            body = f"Test email sent at {timestamp}\nThis is a connectivity check."
            try:
                send_email.send_email(subject, body, recipients)
            except Exception as exc:
                self._event_bus.emit(
                    "statusMessage",
                    self._translator.translate(
                        "Preferences",
                        "Test mail failed: {error}").format(error=exc),
                    5000,
                )
                return

            self._event_bus.emit(
                "statusMessage",
                self._translator.translate("Preferences", "Test mail sent"),
                3000,
            )

        self._event_bus.emit(
            "statusMessage",
            self._translator.translate("Preferences", "Sending test email..."),
            2000,
        )
        threading.Thread(target=_send, daemon=True).start()

    def _apply_templates(self) -> None:
        # Log templates
        settings.set_template_values(
            "log", {
                "record_entry": self._get_text(self.log_template),
                "csv_header": self.csv_header.get().strip(),
            })
        # Mail templates
        settings.set_template_values(
            "mail", {
                "alert_subject": self.alert_subject.get().strip(),
                "alert_body": self._get_text(self.alert_body),
                "recovery_subject": self.recovery_subject.get().strip(),
                "recovery_body": self._get_text(self.recovery_body),
            })

    def _load_logging_settings(self) -> None:
        log_settings = settings.get_logging_settings()
        self.log_level.set(log_settings.level_name)
        self._fill_entry(self.log_format, log_settings.fmt)
        self._fill_entry(self.log_datefmt, log_settings.datefmt or "")
        self._fill_entry(self.log_filename, log_settings.file_path.name)
        apply_text_theme(self.log_template)
        log_templates = settings.get_template_values("log")
        self._set_text(self.log_template, log_templates.get("record_entry", ""))
        self._fill_entry(self.csv_header, log_templates.get("csv_header", ""))

    def _load_mail_settings(self) -> None:
        mail_settings = settings.get_mail_settings()
        self._fill_entry(self.mail_server, mail_settings.get("smtp_server", ""))
        self._fill_entry(self.mail_port, mail_settings.get("smtp_port", ""))
        self._fill_entry(self.mail_username, mail_settings.get("username", ""))
        self._fill_entry(self.mail_password, mail_settings.get("password", ""))
        self._fill_entry(self.mail_from, mail_settings.get("from_addr", ""))
        self._fill_entry(self.mail_to, mail_settings.get("to_addrs", ""))
        self.use_ssl.set(bool(mail_settings.get("use_ssl", False)))
        self.use_starttls.set(bool(mail_settings.get("use_starttls", False)))

    def _load_templates(self) -> None:
        mail_templates = settings.get_template_values("mail")
        self._fill_entry(self.alert_subject,
                         mail_templates.get("alert_subject", ""))
        apply_text_theme(self.alert_body)
        self._set_text(self.alert_body, mail_templates.get("alert_body", ""))
        self._fill_entry(self.recovery_subject,
                         mail_templates.get("recovery_subject", ""))
        apply_text_theme(self.recovery_body)
        self._set_text(self.recovery_body,
                       mail_templates.get("recovery_body", ""))

    def _set_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        if value:
            widget.insert("1.0", value)
        widget.configure(state="normal")

    def _get_text(self, widget: tk.Text) -> str:
        return widget.get("1.0", tk.END).rstrip("\n")
