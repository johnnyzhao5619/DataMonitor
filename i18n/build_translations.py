# -*- codeing = utf-8 -*-
# @Create: 2023-02-16 3:37 p.m.
# @Update: 2025-10-24 11:53 p.m.
# @Author: John Zhao
"""Generate JsonTranslator-friendly translation files from the shared catalog."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_catalog(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - static analysis aid
        raise SystemExit(
            f"Failed to parse translation catalog: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("catalog.json must be an object structure")
    return payload


def build_translations(catalog: dict[str, Any], root: Path) -> None:
    languages = catalog.get("languages")
    contexts = catalog.get("contexts")

    if not isinstance(languages, list) or not languages:
        raise SystemExit("catalog.json is missing a languages definition")
    if not isinstance(contexts, list) or not contexts:
        raise SystemExit("catalog.json is missing a contexts definition")

    for language in languages:
        if not isinstance(language, str) or not language:
            raise SystemExit("languages contains an invalid language code")

    for language in languages:
        messages: dict[str, dict[str, str]] = {}
        for context in contexts:
            context_name = context.get("name")
            if not isinstance(context_name, str) or not context_name:
                raise SystemExit("context entry is missing a name")
            entries = context.get("messages")
            if not isinstance(entries, list):
                raise SystemExit(
                    f"context {context_name} is missing a messages array")
            context_messages: dict[str, str] = {}
            for message in entries:
                if not isinstance(message, dict):
                    raise SystemExit(
                        f"context {context_name} contains an invalid message structure"
                    )
                source = message.get("source")
                translations = message.get("translations")
                if not isinstance(source, str):
                    raise SystemExit(
                        f"context {context_name} contains an invalid source value"
                    )
                if not isinstance(translations, dict):
                    raise SystemExit(
                        f"context {context_name} entry {source!r} is missing translations"
                    )
                if language not in translations:
                    raise SystemExit(
                        f"context {context_name} entry {source!r} lacks a {language} translation"
                    )
                target = translations[language]
                if not isinstance(target, str) or target == "":
                    raise SystemExit(
                        f"context {context_name} entry {source!r} has no translation text for {language}"
                    )
                context_messages[source] = target
            messages[context_name] = context_messages

        payload = {
            "language": language,
            "messages": messages,
        }
        output_path = root / f"{language}.qm.json"
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print(f"Generated {output_path.relative_to(root)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help=
        "Directory containing catalog.json (defaults to this script's directory)",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    catalog_path = root / "catalog.json"
    if not catalog_path.is_file():
        raise SystemExit(f"catalog.json not found: {catalog_path}")

    catalog = load_catalog(catalog_path)
    build_translations(catalog, root)


if __name__ == "__main__":
    main()
