"""主题管理与主题定义模块。"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, fields, is_dataclass, replace
from pathlib import Path
from textwrap import dedent
from typing import Callable, Iterable, Mapping, Optional

from PySide6 import QtGui, QtWidgets

import configuration

try:  # pragma: no cover - 可选依赖
    import yaml  # type: ignore
except Exception:  # pragma: no cover - 可选依赖
    yaml = None

LOGGER = logging.getLogger(__name__)


PaletteFactory = Callable[["ThemeTokens"], QtGui.QPalette]
StylesheetBuilder = Callable[["ThemeTokens"], str]


@dataclass(frozen=True)
class ThemeSpacing:
    """描述样式表中使用到的间距令牌。"""

    button_vertical: int = 8
    button_horizontal: int = 18
    navigation_vertical: int = 10
    navigation_horizontal: int = 14
    control_padding: int = 6
    text_padding: int = 8
    groupbox_title_offset: int = 12
    groupbox_title_padding: int = 4
    tab_padding_vertical: int = 6
    tab_padding_horizontal: int = 12
    tab_gap: int = 4
    card_title_spacing: int = 8


@dataclass(frozen=True)
class ThemeRadii:
    """描述控件圆角的令牌。"""

    button: int = 6
    navigation: int = 8
    card: int = 10
    input: int = 6
    tab: int = 6


@dataclass(frozen=True)
class ThemePaletteColors:
    """用于构建 Qt 调色板的颜色集合。"""

    window: str
    window_text: str
    base: str
    alternate_base: str
    tooltip_base: str
    tooltip_text: str
    text: str
    button: str
    button_text: str
    bright_text: str
    highlight: str
    highlighted_text: str
    link: str
    link_visited: str
    placeholder_text: str


@dataclass(frozen=True)
class ThemeSurfaceColors:
    """描述样式表使用到的界面颜色。"""

    window_bg: str
    window_text: str
    heading_text: str
    accent: str
    accent_text: str
    accent_hover: str
    accent_pressed: str
    accent_disabled_bg: str
    accent_disabled_text: str
    navigation_panel_bg: str
    navigation_border: str
    navigation_button_bg: str
    navigation_text: str
    navigation_hover_bg: str
    navigation_hover_text: str
    navigation_checked_bg: str
    navigation_checked_text: str
    card_bg: str
    card_border: str
    card_title: str
    hint_text: str
    error_text: str
    input_bg: str
    input_border: str
    input_text: str
    input_placeholder: str
    popup_bg: str
    popup_border: str
    status_bg: str
    status_border: str
    status_text: str
    tab_bg: str
    tab_border: str
    tab_text: str
    tab_selected_bg: str
    tab_selected_text: str
    tooltip_bg: str
    tooltip_text: str
    tooltip_border: str
    splitter: str
    scrollarea_bg: str
    selection_bg: str
    selection_text: str
    list_selection_bg: str
    list_selection_text: str
    groupbox_title: str


@dataclass(frozen=True)
class ThemeTokens:
    """聚合主题所需的令牌。"""

    palette: ThemePaletteColors
    colors: ThemeSurfaceColors
    spacing: ThemeSpacing = ThemeSpacing()
    radii: ThemeRadii = ThemeRadii()
    font_family: str = '"Segoe UI", "Microsoft YaHei", sans-serif'

    def to_stylesheet_mapping(self) -> dict[str, str]:
        """转换为样式表模板可用的映射。"""

        spacing = self.spacing
        radii = self.radii
        colors = self.colors
        return {
            "font_family": self.font_family,
            "window_bg": colors.window_bg,
            "window_text": colors.window_text,
            "heading_text": colors.heading_text,
            "accent": colors.accent,
            "accent_text": colors.accent_text,
            "accent_hover": colors.accent_hover,
            "accent_pressed": colors.accent_pressed,
            "accent_disabled_bg": colors.accent_disabled_bg,
            "accent_disabled_text": colors.accent_disabled_text,
            "navigation_panel_bg": colors.navigation_panel_bg,
            "navigation_border": colors.navigation_border,
            "navigation_button_bg": colors.navigation_button_bg,
            "navigation_text": colors.navigation_text,
            "navigation_hover_bg": colors.navigation_hover_bg,
            "navigation_hover_text": colors.navigation_hover_text,
            "navigation_checked_bg": colors.navigation_checked_bg,
            "navigation_checked_text": colors.navigation_checked_text,
            "card_bg": colors.card_bg,
            "card_border": colors.card_border,
            "card_title": colors.card_title,
            "hint_text": colors.hint_text,
            "error_text": colors.error_text,
            "input_bg": colors.input_bg,
            "input_border": colors.input_border,
            "input_text": colors.input_text,
            "selection_bg": colors.selection_bg,
            "selection_text": colors.selection_text,
            "popup_bg": colors.popup_bg,
            "popup_border": colors.popup_border,
            "status_bg": colors.status_bg,
            "status_border": colors.status_border,
            "status_text": colors.status_text,
            "tab_bg": colors.tab_bg,
            "tab_border": colors.tab_border,
            "tab_text": colors.tab_text,
            "tab_selected_bg": colors.tab_selected_bg,
            "tab_selected_text": colors.tab_selected_text,
            "tooltip_bg": colors.tooltip_bg,
            "tooltip_text": colors.tooltip_text,
            "tooltip_border": colors.tooltip_border,
            "splitter": colors.splitter,
            "scrollarea_bg": colors.scrollarea_bg,
            "list_selection_bg": colors.list_selection_bg,
            "list_selection_text": colors.list_selection_text,
            "groupbox_title": colors.groupbox_title,
            "spacing_button_vertical": f"{spacing.button_vertical}px",
            "spacing_button_horizontal": f"{spacing.button_horizontal}px",
            "spacing_navigation_vertical": f"{spacing.navigation_vertical}px",
            "spacing_navigation_horizontal": f"{spacing.navigation_horizontal}px",
            "spacing_control_padding": f"{spacing.control_padding}px",
            "spacing_text_padding": f"{spacing.text_padding}px",
            "spacing_groupbox_title_offset": f"{spacing.groupbox_title_offset}px",
            "spacing_groupbox_title_padding": f"{spacing.groupbox_title_padding}px",
            "spacing_tab_padding_vertical": f"{spacing.tab_padding_vertical}px",
            "spacing_tab_padding_horizontal": f"{spacing.tab_padding_horizontal}px",
            "spacing_tab_gap": f"{spacing.tab_gap}px",
            "spacing_card_title_spacing": f"{spacing.card_title_spacing}px",
            "radius_button": f"{radii.button}px",
            "radius_navigation": f"{radii.navigation}px",
            "radius_card": f"{radii.card}px",
            "radius_input": f"{radii.input}px",
            "radius_tab": f"{radii.tab}px",
        }


@dataclass(frozen=True)
class ThemeMetadata:
    """描述主题的附加信息。"""

    display_name: str
    descriptions: Mapping[str, str]
    is_high_contrast: bool = False

    def description_for(self, language: str) -> str:
        if not self.descriptions:
            return ""
        if language in self.descriptions:
            return self.descriptions[language]
        default_language = configuration.DEFAULT_LANGUAGE
        if default_language in self.descriptions:
            return self.descriptions[default_language]
        if "*" in self.descriptions:
            return self.descriptions["*"]
        return next(iter(self.descriptions.values()))


@dataclass(frozen=True)
class ThemeDefinition:
    """封装单个主题的调色板与样式表定义。"""

    name: str
    palette_factory: PaletteFactory
    tokens: ThemeTokens
    stylesheet_builder: StylesheetBuilder
    metadata: ThemeMetadata = ThemeMetadata(display_name="", descriptions={})

    def create_palette(self) -> QtGui.QPalette:
        """构造调色板副本，避免外部修改共享状态。"""

        palette = self.palette_factory(self.tokens)
        return QtGui.QPalette(palette)

    def build_stylesheet(self) -> str:
        return self.stylesheet_builder(self.tokens)


class ThemeManager:
    """负责注册与切换主题的管理器。"""

    THEME_CONFIG_DIRNAME = "themes"

    def __init__(self, app: Optional[QtWidgets.QApplication] = None) -> None:
        self._app = app or QtWidgets.QApplication.instance()
        if self._app is None:
            raise RuntimeError("ThemeManager 需要有效的 QApplication 实例")

        self._themes: "dict[str, ThemeDefinition]" = {}
        self._order: list[str] = []
        self._current: Optional[str] = None

    def register(self, theme: ThemeDefinition) -> None:
        """注册单个主题，如果名称重复则覆盖旧值。"""

        if theme.name in self._themes:
            self._themes[theme.name] = theme
            return

        self._themes[theme.name] = theme
        self._order.append(theme.name)

    def register_many(self, themes: Iterable[ThemeDefinition]) -> None:
        """按顺序批量注册主题，并加载配置目录中的扩展定义。"""

        for theme in themes:
            self.register(theme)

        for theme in self._load_configured_themes():
            self.register(theme)

    def available_themes(self) -> list[str]:
        return [name for name in self._order if name in self._themes]

    def get_theme(self, name: str) -> ThemeDefinition:
        return self._themes[name]

    def current_theme_name(self) -> Optional[str]:
        return self._current

    def current_theme(self) -> Optional[ThemeDefinition]:
        if self._current is None:
            return None
        return self._themes.get(self._current)

    def apply_theme(self, name: str) -> ThemeDefinition:
        """应用指定名称的主题，同时刷新已存在的控件。"""

        if name not in self._themes:
            raise KeyError(f"未注册主题: {name}")

        theme = self._themes[name]
        palette = theme.create_palette()
        stylesheet = theme.build_stylesheet()

        self._app.setPalette(palette)
        self._app.setStyleSheet(stylesheet)
        self._current = name
        self._app.setProperty("currentTheme", name)

        style = self._app.style()
        style.unpolish(self._app)
        style.polish(self._app)

        for widget in self._app.allWidgets():
            widget.setPalette(palette)
            style.unpolish(widget)
            style.polish(widget)
            self.refresh_widget(widget)

        return theme

    # -- 配置主题加载 --------------------------------------------------
    def _load_configured_themes(self) -> list[ThemeDefinition]:
        config_dir = configuration.get_config_directory()
        theme_dir = config_dir / self.THEME_CONFIG_DIRNAME
        if not theme_dir.is_dir():
            return []

        definitions: list[ThemeDefinition] = []
        for path in sorted(theme_dir.iterdir()):
            if path.suffix.lower() not in {".json", ".yaml", ".yml"}:
                continue
            try:
                payload = _read_theme_payload(path)
            except Exception as exc:  # pragma: no cover - 防御性日志
                LOGGER.warning("主题文件 %s 解析失败: %s", path, exc)
                continue
            definition = self._build_theme_from_payload(payload, path)
            if definition is not None:
                definitions.append(definition)
        return definitions

    def _build_theme_from_payload(
        self, payload: Mapping[str, object], path: Path
    ) -> Optional[ThemeDefinition]:
        if not isinstance(payload, Mapping):
            LOGGER.warning("主题文件 %s 格式无效，预期为映射", path)
            return None

        raw_name = payload.get("name")
        name = str(raw_name).strip() if raw_name is not None else ""
        if not name:
            LOGGER.warning("主题文件 %s 缺少名称", path)
            return None

        base_tokens = self._resolve_base_tokens(payload.get("extends"))

        tokens_payload = payload.get("tokens")
        try:
            tokens = _merge_tokens(base_tokens, tokens_payload)
        except Exception as exc:  # pragma: no cover - 防御性日志
            LOGGER.warning("主题 %s 令牌合并失败: %s", path, exc)
            return None

        display_name = str(payload.get("display_name") or name)
        descriptions = _normalise_descriptions(payload.get("descriptions"))
        high_contrast = _coerce_bool(payload.get("high_contrast"))

        metadata = ThemeMetadata(
            display_name=display_name,
            descriptions=descriptions,
            is_high_contrast=high_contrast,
        )

        return ThemeDefinition(
            name=name,
            palette_factory=_create_palette,
            tokens=tokens,
            stylesheet_builder=_build_stylesheet,
            metadata=metadata,
        )

    def _resolve_base_tokens(self, extends_value: object) -> ThemeTokens:
        if isinstance(extends_value, str) and extends_value.strip():
            key = extends_value.strip()
            base = self._themes.get(key)
            if base is not None:
                return base.tokens
            LOGGER.warning("找不到继承基准主题 %s，使用默认主题", key)
        if "workspace_light" in self._themes:
            return self._themes["workspace_light"].tokens
        if self._themes:
            first_key = self._order[0]
            return self._themes[first_key].tokens
        return workspace_light.tokens

    # -- 工具方法 -----------------------------------------------------
    @staticmethod
    def refresh_widget(widget: QtWidgets.QWidget) -> None:
        """刷新控件绘制，兼容视图类在 PySide6 中 update() 签名变更。"""

        update_method = getattr(widget, "update", None)
        if callable(update_method):
            try:
                update_method()
                return
            except TypeError:
                pass

        try:
            QtWidgets.QWidget.update(widget)
            return
        except Exception:
            pass

        viewport_getter = getattr(widget, "viewport", None)
        if callable(viewport_getter):
            viewport = viewport_getter()
            if viewport is not None:
                viewport.update()


def _coerce_bool(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return False


def _normalise_descriptions(raw: object) -> dict[str, str]:
    if isinstance(raw, Mapping):
        result: dict[str, str] = {}
        for key, value in raw.items():
            if value is None:
                continue
            text = str(value).strip()
            if not text:
                continue
            result[str(key)] = text
        return result
    if isinstance(raw, str):
        text = raw.strip()
        return {"*": text} if text else {}
    return {}


def _read_theme_payload(path: Path) -> Mapping[str, object]:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(text)
    else:
        if yaml is None:
            raise RuntimeError("需要 PyYAML 才能解析 YAML 主题文件")
        payload = yaml.safe_load(text)
    if not isinstance(payload, Mapping):
        raise ValueError("主题文件未解析为映射")
    return payload


def _merge_tokens(base: ThemeTokens, payload: object) -> ThemeTokens:
    if not isinstance(payload, Mapping):
        return base

    palette = _merge_dataclass(base.palette, payload.get("palette"))
    colors = _merge_dataclass(base.colors, payload.get("colors"))
    spacing = _merge_dataclass(base.spacing, payload.get("spacing"))
    radii = _merge_dataclass(base.radii, payload.get("radii"))
    font_family = base.font_family
    if "font_family" in payload:
        value = payload.get("font_family")
        if value is not None:
            font_family = str(value)
    return ThemeTokens(
        palette=palette,
        colors=colors,
        spacing=spacing,
        radii=radii,
        font_family=font_family,
    )


def _merge_dataclass(instance: object, payload: object):
    if not is_dataclass(instance):
        return instance
    if not isinstance(payload, Mapping):
        return instance
    kwargs = {}
    for field in fields(instance):
        value = getattr(instance, field.name)
        if field.name not in payload:
            kwargs[field.name] = value
            continue
        override = payload[field.name]
        if is_dataclass(value):
            kwargs[field.name] = _merge_dataclass(value, override)
            continue
        kwargs[field.name] = _coerce_field(field.type, override, value)
    return replace(instance, **kwargs)


def _coerce_field(field_type: object, override: object, default_value: object) -> object:
    if isinstance(default_value, bool) or field_type is bool:
        return _coerce_bool(override)
    if isinstance(default_value, int) or field_type is int:
        return int(override)
    if override is None:
        return default_value
    return str(override)


def _create_palette(tokens: ThemeTokens) -> QtGui.QPalette:
    colors = tokens.palette
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(colors.window))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(colors.window_text))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(colors.base))
    palette.setColor(
        QtGui.QPalette.AlternateBase, QtGui.QColor(colors.alternate_base)
    )
    palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(colors.tooltip_base))
    palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(colors.tooltip_text))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor(colors.text))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(colors.button))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(colors.button_text))
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(colors.highlight))
    palette.setColor(
        QtGui.QPalette.HighlightedText, QtGui.QColor(colors.highlighted_text)
    )
    palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor(colors.bright_text))
    palette.setColor(QtGui.QPalette.Link, QtGui.QColor(colors.link))
    palette.setColor(QtGui.QPalette.LinkVisited, QtGui.QColor(colors.link_visited))
    palette.setColor(
        QtGui.QPalette.PlaceholderText, QtGui.QColor(colors.placeholder_text)
    )
    return palette


_BASE_STYLESHEET_TEMPLATE = dedent(
    """
    QMainWindow {{
        background-color: {window_bg};
    }}
    QWidget {{
        font-family: {font_family};
        color: {window_text};
    }}
    QPushButton {{
        background-color: {accent};
        color: {accent_text};
        border: none;
        border-radius: {radius_button};
        padding: {spacing_button_vertical} {spacing_button_horizontal};
    }}
    QPushButton:hover {{
        background-color: {accent_hover};
    }}
    QPushButton:pressed {{
        background-color: {accent_pressed};
    }}
    QPushButton:disabled {{
        background-color: {accent_disabled_bg};
        color: {accent_disabled_text};
    }}
    QPushButton[category="navigation"] {{
        background-color: {navigation_button_bg};
        color: {navigation_text};
        border-radius: {radius_navigation};
        font-weight: 600;
        text-align: left;
        padding: {spacing_navigation_vertical} {spacing_navigation_horizontal};
    }}
    QPushButton[category="navigation"]:hover {{
        background-color: {navigation_hover_bg};
        color: {navigation_hover_text};
    }}
    QPushButton[category="navigation"]:checked {{
        background-color: {navigation_checked_bg};
        color: {navigation_checked_text};
    }}
    QFrame#navigationBar {{
        background-color: {navigation_panel_bg};
        border-right: 1px solid {navigation_border};
    }}
    QFrame[role="card"], QWidget[role="card"] {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: {radius_card};
    }}
    QFrame[role="card"] QLabel[role="cardTitle"], QWidget[role="card"] QLabel[role="cardTitle"] {{
        font-size: 14px;
        font-weight: 600;
        margin-bottom: {spacing_card_title_spacing};
        color: {card_title};
    }}
    QLabel[role="heading"] {{
        font-size: 18px;
        font-weight: 600;
        color: {heading_text};
    }}
    QLabel[role="hint"] {{
        color: {hint_text};
    }}
    QLabel[role="error"] {{
        color: {error_text};
    }}
    QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTextBrowser, QListWidget {{
        background: {input_bg};
        border: 1px solid {input_border};
        border-radius: {radius_input};
        padding: {spacing_control_padding};
        color: {input_text};
        selection-background-color: {selection_bg};
        selection-color: {selection_text};
    }}
    QPlainTextEdit, QTextBrowser {{
        padding: {spacing_text_padding};
    }}
    QComboBox::drop-down {{
        border: none;
    }}
    QComboBox QAbstractItemView {{
        background: {popup_bg};
        border: 1px solid {popup_border};
        selection-background-color: {selection_bg};
        selection-color: {selection_text};
        color: {input_text};
    }}
    QStatusBar {{
        background: {status_bg};
        border-top: 1px solid {status_border};
        color: {status_text};
    }}
    QTabWidget::pane {{
        border: 1px solid {tab_border};
        border-radius: {radius_tab};
    }}
    QTabBar::tab {{
        background: {tab_bg};
        border: 1px solid {tab_border};
        border-bottom: none;
        padding: {spacing_tab_padding_vertical} {spacing_tab_padding_horizontal};
        margin-right: {spacing_tab_gap};
        border-top-left-radius: {radius_tab};
        border-top-right-radius: {radius_tab};
        color: {tab_text};
    }}
    QTabBar::tab:selected {{
        background: {tab_selected_bg};
        color: {tab_selected_text};
    }}
    QScrollArea {{
        background: {scrollarea_bg};
        border: none;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: {spacing_groupbox_title_offset};
        padding: 0 {spacing_groupbox_title_padding};
        color: {groupbox_title};
    }}
    QSplitter::handle {{
        background-color: {splitter};
    }}
    QToolTip {{
        color: {tooltip_text};
        background-color: {tooltip_bg};
        border: 1px solid {tooltip_border};
    }}
    QListWidget::item:selected {{
        background-color: {list_selection_bg};
        color: {list_selection_text};
    }}
    """
)


def _build_stylesheet(tokens: ThemeTokens) -> str:
    return _BASE_STYLESHEET_TEMPLATE.format_map(tokens.to_stylesheet_mapping())


# --- 内置主题定义 -------------------------------------------------------
_light_tokens = ThemeTokens(
    palette=ThemePaletteColors(
        window="#F3F2F1",
        window_text="#201F1E",
        base="#FFFFFF",
        alternate_base="#F7F6F3",
        tooltip_base="#FFFFFF",
        tooltip_text="#201F1E",
        text="#201F1E",
        button="#FFFFFF",
        button_text="#201F1E",
        bright_text="#C50F1F",
        highlight="#6264A7",
        highlighted_text="#FFFFFF",
        link="#605E5C",
        link_visited="#414043",
        placeholder_text="#605E5C",
    ),
    colors=ThemeSurfaceColors(
        window_bg="#F3F2F1",
        window_text="#201F1E",
        heading_text="#201F1E",
        accent="#6264A7",
        accent_text="#FFFFFF",
        accent_hover="#4C4D89",
        accent_pressed="#33344A",
        accent_disabled_bg="#E1DFDD",
        accent_disabled_text="#A19F9D",
        navigation_panel_bg="#F3F2F1",
        navigation_border="#E1DFDD",
        navigation_button_bg="transparent",
        navigation_text="#201F1E",
        navigation_hover_bg="#E1DFDD",
        navigation_hover_text="#201F1E",
        navigation_checked_bg="#C8C6C4",
        navigation_checked_text="#201F1E",
        card_bg="#FFFFFF",
        card_border="#E1DFDD",
        card_title="#201F1E",
        hint_text="#605E5C",
        error_text="#C50F1F",
        input_bg="#FFFFFF",
        input_border="#C8C6C4",
        input_text="#201F1E",
        input_placeholder="#605E5C",
        popup_bg="#FFFFFF",
        popup_border="#C8C6C4",
        status_bg="#E1DFDD",
        status_border="#C8C6C4",
        status_text="#201F1E",
        tab_bg="#E9E9F0",
        tab_border="#C8C6C4",
        tab_text="#201F1E",
        tab_selected_bg="#FFFFFF",
        tab_selected_text="#201F1E",
        tooltip_bg="#FFFFFF",
        tooltip_text="#201F1E",
        tooltip_border="#C8C6C4",
        splitter="#E1DFDD",
        scrollarea_bg="transparent",
        selection_bg="#6264A7",
        selection_text="#FFFFFF",
        list_selection_bg="#6264A7",
        list_selection_text="#FFFFFF",
        groupbox_title="#201F1E",
    ),
)

workspace_light = ThemeDefinition(
    name="workspace_light",
    palette_factory=_create_palette,
    tokens=_light_tokens,
    stylesheet_builder=_build_stylesheet,
    metadata=ThemeMetadata(
        display_name="Workspace Light",
        descriptions={
            "zh_CN": "柔和的浅色主题，适合大多数场景",
            "en_US": "Balanced light theme for everyday use",
        },
    ),
)

_dark_tokens = ThemeTokens(
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
        navigation_button_bg="transparent",
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

workspace_dark = ThemeDefinition(
    name="workspace_dark",
    palette_factory=_create_palette,
    tokens=_dark_tokens,
    stylesheet_builder=_build_stylesheet,
    metadata=ThemeMetadata(
        display_name="Workspace Dark",
        descriptions={
            "zh_CN": "深色主题，适合弱光环境",
            "en_US": "Dark theme designed for low-light work",
        },
    ),
)

BUILTIN_THEMES: tuple[ThemeDefinition, ...] = (
    workspace_light,
    workspace_dark,
)


__all__ = [
    "ThemeDefinition",
    "ThemeManager",
    "ThemeTokens",
    "ThemeMetadata",
    "workspace_light",
    "workspace_dark",
    "BUILTIN_THEMES",
]
