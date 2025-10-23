"""从统一 catalog 生成 JsonTranslator 可读取的翻译文件。"""
from __future__ import annotations


import argparse
import json
from pathlib import Path
from typing import Any


def load_catalog(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - 静态分析
        raise SystemExit(f"无法解析翻译 catalog: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("catalog.json 必须为对象结构")
    return payload


def build_translations(catalog: dict[str, Any], root: Path) -> None:
    languages = catalog.get("languages")
    contexts = catalog.get("contexts")

    if not isinstance(languages, list) or not languages:
        raise SystemExit("catalog.json 缺少 languages 定义")
    if not isinstance(contexts, list) or not contexts:
        raise SystemExit("catalog.json 缺少 contexts 定义")

    for language in languages:
        if not isinstance(language, str) or not language:
            raise SystemExit("languages 中包含无效的语言代码")

    for language in languages:
        messages: dict[str, dict[str, str]] = {}
        for context in contexts:
            context_name = context.get("name")
            if not isinstance(context_name, str) or not context_name:
                raise SystemExit("context 缺少名称")
            entries = context.get("messages")
            if not isinstance(entries, list):
                raise SystemExit(f"context {context_name} 缺少 messages 数组")
            context_messages: dict[str, str] = {}
            for message in entries:
                if not isinstance(message, dict):
                    raise SystemExit(f"context {context_name} 存在无效消息结构")
                source = message.get("source")
                translations = message.get("translations")
                if not isinstance(source, str):
                    raise SystemExit(f"context {context_name} 包含无效 source")
                if not isinstance(translations, dict):
                    raise SystemExit(
                        f"context {context_name} 的 {source!r} 缺少 translations"
                    )
                if language not in translations:
                    raise SystemExit(
                        f"context {context_name} 的 {source!r} 缺少 {language} 翻译"
                    )
                target = translations[language]
                if not isinstance(target, str) or target == "":
                    raise SystemExit(
                        f"context {context_name} 的 {source!r} 在 {language} 中未翻译"
                    )
                context_messages[source] = target
            messages[context_name] = context_messages

        payload = {
            "language": language,
            "messages": messages,
        }
        output_path = root / f"{language}.qm.json"
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"生成 {output_path.relative_to(root)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="catalog.json 所在目录，默认当前脚本所在目录",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    catalog_path = root / "catalog.json"
    if not catalog_path.is_file():
        raise SystemExit(f"未找到 catalog.json: {catalog_path}")

    catalog = load_catalog(catalog_path)
    build_translations(catalog, root)


if __name__ == "__main__":
    main()
