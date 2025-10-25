# -*- codeing = utf-8 -*-
# @Create: 2023-02-16 3:37 p.m.
# @Update: 2025-10-24 12:05 a.m.
# @Author: John Zhao
"""Documentation page providing license overview and styled user manuals."""
from __future__ import annotations

from pathlib import Path
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

    _LICENSE_PATH = Path(__file__).resolve().parents[2] / "LICENSE"
    _MANUAL_ZH_PATH = Path(
        __file__).resolve().parents[2] / "docs" / "manual_zh.md"
    _MANUAL_EN_PATH = Path(
        __file__).resolve().parents[2] / "docs" / "manual_en.md"

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
        self.manualView.document().setDefaultStyleSheet(_MARKDOWN_STYLESHEET)
        manual_layout.addWidget(self.manualView, 1)
        layout.addWidget(self.manualGroup, 2)

        self.reload_content()
        self.retranslate_ui()

    def reload_content(self) -> None:
        self.licenseView.setPlainText(self._load_text(self._LICENSE_PATH))
        manual_path = self._manual_path_for_language()
        manual_text = self._load_text(manual_path)
        if manual_path.suffix.lower() == ".md":
            self.manualView.setMarkdown(manual_text)
        else:
            self.manualView.setPlainText(manual_text)

    def _manual_path_for_language(self) -> Path:
        language = configuration.get_language()
        if language == "zh_CN":
            return self._MANUAL_ZH_PATH
        return self._MANUAL_EN_PATH

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
