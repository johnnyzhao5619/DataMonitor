"""Tkinter dashboard view showing clocks and live log feed."""

from __future__ import annotations

import datetime as _dt
import tkinter as tk
from tkinter import ttk
from typing import Optional

from datamonitor.core import EventBus, Translator
from datamonitor.core.monitoring import MonitoringOrchestrator
from tkui.theme import apply_text_theme


class DashboardView(ttk.Frame):
    """Dashboard displaying local/UTC time and a live log feed."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        translator: Translator,
        event_bus: EventBus,
        orchestrator: MonitoringOrchestrator,
        timezone_offset_hours: int = 0,
    ) -> None:
        super().__init__(master, padding=(8, 8, 8, 8))
        self._translator = translator
        self._event_bus = event_bus
        self._orchestrator = orchestrator
        self._timezone_offset_hours = timezone_offset_hours
        self._log_subscription: Optional[callable] = None
        self._status_subscription: Optional[callable] = None
        self._tz_subscription: Optional[callable] = None
        self._monitoring_subscription: Optional[callable] = None
        self._tick_after_id: Optional[str] = None

        self._build_ui()
        self.retranslate()
        self._wire_events()
        self._schedule_tick()

        self.bind("<Destroy>", self._on_destroy, add="+")

    def _build_ui(self) -> None:
        cards = ttk.Frame(self)
        cards.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        cards.columnconfigure(0, weight=1)
        cards.columnconfigure(1, weight=1)

        self.local_group = ttk.LabelFrame(cards, padding=12)
        self.local_group.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.local_time_label = ttk.Label(self.local_group,
                                          font=("Segoe UI", 18, "bold"))
        self.local_time_label.pack(anchor="center")

        self.utc_group = ttk.LabelFrame(cards, padding=12)
        self.utc_group.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.utc_time_label = ttk.Label(self.utc_group,
                                        font=("Segoe UI", 18, "bold"))
        self.utc_time_label.pack(anchor="center")

        controls = ttk.Frame(self)
        controls.grid(row=1, column=0, sticky="w", pady=(0, 6))
        self.start_button = ttk.Button(controls,
                                       text="Start",
                                       command=self._start_monitoring)
        self.start_button.pack(side="left", padx=(0, 6))
        self.stop_button = ttk.Button(controls,
                                      text="Stop",
                                      command=self._stop_monitoring,
                                      state="disabled")
        self.stop_button.pack(side="left")

        log_card = ttk.LabelFrame(self, padding=12)
        log_card.grid(row=2, column=0, sticky="nsew")
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        self.log_title = ttk.Label(log_card, style="CardTitle.TLabel")
        self.log_title.pack(anchor="w", pady=(0, 6))

        self.log_widget = tk.Text(
            log_card,
            wrap="word",
            height=16,
            state="disabled",
            font=("Consolas", 10),
            relief="flat",
        )
        apply_text_theme(self.log_widget)
        self.log_widget.pack(fill="both", expand=True)

        self._log_scrollbar = ttk.Scrollbar(
            log_card, orient="vertical", command=self._on_log_scroll
        )
        self._log_scrollbar_visible = False
        self.log_widget.configure(yscrollcommand=self._on_log_yscroll)
        self.log_widget.bind("<Configure>",
                             lambda _e: self._update_scrollbar_visibility(),
                             add="+")

    def retranslate(self) -> None:
        t = self._translator.translate
        self.local_group.config(text=t("Dashboard", "Local Time"))
        self.utc_group.config(text=t("Dashboard", "UTC Time"))
        self.log_title.config(text=t("Dashboard", "Live Feed"))
        self.start_button.config(text=t("Dashboard", "Start Monitoring"))
        self.stop_button.config(text=t("Dashboard", "Stop Monitoring"))

    # ------------------------------------------------------------------
    def _wire_events(self) -> None:
        self._log_subscription = self._event_bus.subscribe(
            "logMessage", self.append_log)
        self._status_subscription = self._event_bus.subscribe(
            "statusMessage", self._handle_status)
        self._tz_subscription = self._event_bus.subscribe(
            "timezoneChanged", self._handle_timezone_changed)
        self._monitoring_subscription = self._event_bus.subscribe(
            "monitoringToggled", self._handle_monitoring_toggled)

    def _schedule_tick(self) -> None:
        self._update_clocks()
        self._tick_after_id = self.after(1000, self._schedule_tick)

    def _update_clocks(self) -> None:
        now_utc = _dt.datetime.now(_dt.timezone.utc)
        local = now_utc + _dt.timedelta(hours=self._timezone_offset_hours)
        fmt = "%Y-%m-%d %H:%M:%S"
        self.local_time_label.config(text=local.strftime(fmt))
        self.utc_time_label.config(text=now_utc.strftime(fmt))

    # ------------------------------------------------------------------
    def append_log(self, message: str) -> None:
        if not message:
            return
        self.log_widget.configure(state="normal")
        self.log_widget.insert("end", message + "\n")
        self.log_widget.see("end")
        self.log_widget.configure(state="disabled")
        self._update_scrollbar_visibility()

    def _handle_status(self, message: str, *_args, **_kwargs) -> None:
        # Status messages are appended to the feed to retain history.
        self.append_log(message)

    def _handle_timezone_changed(self, offset_minutes: int) -> None:
        try:
            self._timezone_offset_hours = int(offset_minutes)
        except Exception:
            return
        self._update_clocks()

    def _handle_monitoring_toggled(self, active: bool) -> None:
        self.start_button.state(("disabled", ) if active else ("!disabled", ))
        self.stop_button.state(("!disabled", ) if active else ("disabled", ))

    def _start_monitoring(self) -> None:
        try:
            self._orchestrator.start()
        except Exception as exc:
            self.append_log(f"Failed to start monitoring: {exc}")

    def _stop_monitoring(self) -> None:
        try:
            self._orchestrator.stop()
        except Exception as exc:
            self.append_log(f"Failed to stop monitoring: {exc}")

    # ------------------------------------------------------------------
    def _on_destroy(self, _event=None) -> None:
        if self._tick_after_id:
            try:
                self.after_cancel(self._tick_after_id)
            except Exception:
                pass
            self._tick_after_id = None

        for unsubscribe in (self._log_subscription, self._status_subscription,
                            self._tz_subscription, self._monitoring_subscription):
            if callable(unsubscribe):
                try:
                    unsubscribe()
                except Exception:
                    pass

    def _on_log_scroll(self, *args) -> None:
        self.log_widget.yview(*args)
        self._update_scrollbar_visibility()

    def _on_log_yscroll(self, first: str, last: str) -> None:
        # Drive the ttk scrollbar and toggle visibility based on content height.
        self._log_scrollbar.set(first, last)
        self._update_scrollbar_visibility(first, last)

    def _update_scrollbar_visibility(
        self, first: Optional[str] = None, last: Optional[str] = None
    ) -> None:
        if first is None or last is None:
            first, last = self.log_widget.yview()
        needs_scrollbar = float(last) - float(first) < 1.0
        if needs_scrollbar and not self._log_scrollbar_visible:
            self._log_scrollbar.pack(side="right", fill="y")
            self._log_scrollbar_visible = True
        elif not needs_scrollbar and self._log_scrollbar_visible:
            self._log_scrollbar.pack_forget()
            self._log_scrollbar_visible = False
