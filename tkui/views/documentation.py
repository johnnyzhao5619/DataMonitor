"""Tkinter documentation view that displays local manual content."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Optional
import re

from datamonitor.core import Translator


class DocumentationView(ttk.Frame):
    """Render documentation markdown as plain text inside a scrollable view."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        translator: Translator,
        docs_root: Optional[Path] = None,
    ) -> None:
        super().__init__(master, padding=(8, 8, 8, 8))
        self._translator = translator
        self._docs_root = docs_root or Path(__file__).resolve().parents[2] / "docs"

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.title_label = ttk.Label(self, style="CardTitle.TLabel")
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.text = tk.Text(self, wrap="word", state="disabled")
        self.text.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns")

        self.retranslate()
        self.reload()

    def retranslate(self) -> None:
        self.title_label.config(
            text=self._translator.translate("Documentation", "Documentation")
        )
        self.reload()

    def reload(self) -> None:
        """Load documentation based on current language."""

        language = self._current_language()
        # Choose file by language; default to English manual.
        if language == "zh_CN":
            filename = "manual_zh.md"
        else:
            filename = "manual_en.md"

        path = self._docs_root / filename
        content = self._read_file(path)
        if not content:
            content = f"Missing documentation file: {path}"

        rendered = self._render_markdown(content)
        self.text.configure(state="normal")
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", rendered)
        self.text.configure(state="disabled")

    def _read_file(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""

    def _current_language(self) -> str:
        # Translator stores default language; if unavailable, fall back to configuration default.
        return getattr(self._translator, "default_language", "en_US")

    def _render_markdown(self, text: str) -> str:
        """Minimal markdown-to-plain-text rendering for headings/lists/links."""
        lines = []
        for raw in text.splitlines():
            line = raw.rstrip()
            line = re.sub(r"^#{1,6}\s*", "", line)
            line = re.sub(r"^\s*[-*]\s+", "- ", line)
            line = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", line)
            line = line.replace("**", "").replace("__", "")
            line = line.replace("*", "").replace("_", "").replace("`", "")
            lines.append(line)
        return "\n".join(lines)
