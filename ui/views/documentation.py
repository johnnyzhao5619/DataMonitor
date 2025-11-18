# -*- codeing = utf-8 -*-
# @Create: 2023-02-16 3:37 p.m.
# @Update: 2025-10-24 12:05 a.m.
# @Author: John Zhao
"""Documentation page providing license overview and styled user manuals."""
from __future__ import annotations

from pathlib import Path
import sys
from typing import Optional

from PySide6 import QtWidgets

import configuration

_MARKDOWN_STYLESHEET = """
body { font-family: "Segoe UI", "Microsoft YaHei", sans-serif; font-size: 13px; color: #2b2b2b; }
h1 { font-size: 22px; margin: 12px 0 8px; }
h2 { font-size: 18px; margin: 10px 0 6px; }
h3 { font-size: 16px; margin: 8px 0 4px; }
p { margin: 6px 0; line-height: 1.5; }
ul, ol { margin: 6px 0 6px 22px; }
code { font-family: "JetBrains Mono", monospace; background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
pre { background-color: #f4f4f4; padding: 8px; border-radius: 4px; overflow: auto; }
table { border-collapse: collapse; margin: 8px 0; }
th, td { border: 1px solid #d0d0d0; padding: 4px 8px; }
"""


class DocumentationPage(QtWidgets.QWidget):
    """Displays license summary and a language-aware user manual."""

    # Resolve resource paths at runtime so this works when frozen by PyInstaller
    @staticmethod
    def _project_root() -> Path:
        # Keep for backward-compat but prefer more robust lookup via
        # _find_resource when locating individual files.
        if getattr(sys, "frozen", False):
            return Path(getattr(sys, "_MEIPASS", Path.cwd()))
        return Path(__file__).resolve().parents[2]

    @classmethod
    def _find_resource(cls, *parts: str) -> Path:
        """Search common locations for a resource when running frozen.

        Checks sys._MEIPASS, the executable parent, current working
        directory, and common PyInstaller internal directories.
        Returns the first existing Path found or a best-effort Path.
        """
        name = Path(*parts)
        candidates: list[Path] = []
        if getattr(sys, "frozen", False):
            meipass = Path(getattr(sys, "_MEIPASS", ""))
            if meipass:
                candidates.append(meipass)
            exe_parent = Path(sys.executable).resolve().parent
            candidates.append(exe_parent)
            # Some PyInstaller one-folder layouts extract internals
            # into a sibling or child _internal directory — check common
            # patterns as well.
            candidates.append(exe_parent / "_internal")
            candidates.append(Path.cwd())
        else:
            candidates.append(Path(__file__).resolve().parents[2])

        # Try each candidate; return first match
        for base in candidates:
            candidate = base.joinpath(name)
            if candidate.exists():
                return candidate

        # As a last resort, try searching upward from cwd for the file
        cur = Path.cwd()
        for _ in range(4):
            candidate = cur.joinpath(name)
            if candidate.exists():
                return candidate
            cur = cur.parent

        # Not found — return a plausible path (first candidate joined)
        if candidates:
            return candidates[0].joinpath(name)
        return name

    @classmethod
    def _license_path(cls) -> Path:
        return cls._find_resource("LICENSE")

    @classmethod
    def _manual_zh_path(cls) -> Path:
        return cls._find_resource("docs", "manual_zh.md")

    @classmethod
    def _manual_en_path(cls) -> Path:
        return cls._find_resource("docs", "manual_en.md")

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("documentationPage")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self.licenseGroup = QtWidgets.QGroupBox(self)
        self.licenseGroup.setObjectName("licenseGroup")
        self.licenseGroup.setProperty("role", "card")
        license_layout = QtWidgets.QVBoxLayout(self.licenseGroup)
        license_layout.setContentsMargins(16, 16, 16, 16)
        license_layout.setSpacing(12)

        self.licenseSummaryLabel = QtWidgets.QLabel(self.licenseGroup)
        self.licenseSummaryLabel.setObjectName("licenseSummaryLabel")
        self.licenseSummaryLabel.setWordWrap(True)
        self.licenseSummaryLabel.setProperty("role", "hint")
        license_layout.addWidget(self.licenseSummaryLabel)

        self.licenseView = QtWidgets.QTextBrowser(self.licenseGroup)
        self.licenseView.setObjectName("licenseView")
        self.licenseView.setOpenExternalLinks(True)
        self.licenseView.setReadOnly(True)
        license_layout.addWidget(self.licenseView, 1)
        layout.addWidget(self.licenseGroup, 1)

        self.manualGroup = QtWidgets.QGroupBox(self)
        self.manualGroup.setObjectName("manualGroup")
        self.manualGroup.setProperty("role", "card")
        manual_layout = QtWidgets.QVBoxLayout(self.manualGroup)
        manual_layout.setContentsMargins(16, 16, 16, 16)
        manual_layout.setSpacing(12)

        self.manualSummaryLabel = QtWidgets.QLabel(self.manualGroup)
        self.manualSummaryLabel.setObjectName("manualSummaryLabel")
        self.manualSummaryLabel.setWordWrap(True)
        self.manualSummaryLabel.setProperty("role", "hint")
        manual_layout.addWidget(self.manualSummaryLabel)

        self.manualView = QtWidgets.QTextBrowser(self.manualGroup)
        self.manualView.setObjectName("manualView")
        self.manualView.setOpenExternalLinks(True)
        self.manualView.setReadOnly(True)
        # We'll inline the stylesheet into the generated HTML for
        # consistent rendering across Qt versions.
        manual_layout.addWidget(self.manualView, 1)
        layout.addWidget(self.manualGroup, 2)

        self.reload_content()
        self.retranslate_ui()

    def reload_content(self) -> None:
        self.licenseView.setPlainText(self._load_text(self._license_path()))
        manual_path = self._manual_path_for_language()
        manual_text = self._load_text(manual_path)
        if manual_path.suffix.lower() == ".md":
            # Convert Markdown -> HTML for more consistent rendering across
            # platforms/Qt versions. Use Python-Markdown if available.
            try:
                import markdown as _md

                html_body = _md.markdown(
                    manual_text,
                    extensions=["extra", "fenced_code", "tables"],
                )
                # Embed CSS into the HTML head to avoid relying on
                # Qt's document().setDefaultStyleSheet, which can vary
                # between Qt versions.
                css = _MARKDOWN_STYLESHEET
                full_html = ("<html><head><meta charset='utf-8'><style>" +
                             css + "</style></head>"
                             f"<body>{html_body}</body></html>")
                self.manualView.setHtml(full_html)
            except Exception:
                # Fallback: if markdown package not available or conversion
                # fails, let QTextBrowser attempt to render Markdown directly
                try:
                    self.manualView.setMarkdown(manual_text)
                except Exception:
                    self.manualView.setPlainText(manual_text)
        else:
            self.manualView.setPlainText(manual_text)

    def _manual_path_for_language(self) -> Path:
        language = configuration.get_language()
        if language == "zh_CN":
            return self._manual_zh_path()
        return self._manual_en_path()

    def _load_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return self.tr("File not found: {path}").format(path=path)
        except Exception as exc:
            return self.tr("Failed to load {path}: {error}").format(path=path,
                                                                    error=exc)

    def retranslate_ui(self) -> None:
        self.licenseGroup.setTitle(self.tr("License Overview"))
        self.licenseSummaryLabel.setText(
            self.
            tr("DataMonitor is released under the Apache License 2.0. The following section contains the full license text "
               "and summarizes the copyright and licensing terms that must be preserved in redistribution or commercial deployments."
               ))
        self.manualGroup.setTitle(self.tr("User Manual"))
        language = configuration.get_language()
        if language == "zh_CN":
            self.manualSummaryLabel.setText(
                self.tr("Displaying the Simplified Chinese user manual."))
        else:
            self.manualSummaryLabel.setText(
                self.tr("Displaying the English user manual."))
        self.reload_content()


__all__ = ["DocumentationPage"]
