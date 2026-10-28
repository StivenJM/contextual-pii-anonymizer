"""Build a test copy of the browser extension with test-only values patched in.

The product sources are never modified. The copy differs from the delivered
extension in exactly five places, and every replacement reports its observed
count so a test can fail loudly if the upstream file changes shape.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXTENSION_SOURCE = PROJECT_ROOT / "browser-extension" / "extension"
BUILD_DIRECTORY = PROJECT_ROOT / "e2e" / ".build" / "extension"


class PatchError(RuntimeError):
    """Raised when a replacement does not match exactly once."""


@dataclass(frozen=True)
class Replacement:
    file: str
    what: str
    expected: int
    observed: int


@dataclass(frozen=True)
class BuildReport:
    destination: Path
    replacements: tuple[Replacement, ...]

    def is_complete(self) -> bool:
        return all(item.observed == item.expected for item in self.replacements)


def _replace_once(
    text: str, old: str, new: str, file: str, what: str
) -> tuple[str, Replacement]:
    observed = text.count(old)
    if observed != 1:
        raise PatchError(
            f"{file}: expected exactly one occurrence of {what}, found {observed}"
        )
    return text.replace(old, new), Replacement(
        file=file, what=what, expected=1, observed=observed
    )


def build_patched_extension(
    *,
    chat_origin: str,
    converter_url: str,
    middleware_url: str,
    token: str,
    destination: Path | None = None,
) -> BuildReport:
    target = destination or BUILD_DIRECTORY
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(EXTENSION_SOURCE, target)

    replacements: list[Replacement] = []

    manifest_path = target / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    match_pattern = f"{chat_origin}/*"
    if match_pattern not in manifest["host_permissions"]:
        manifest["host_permissions"].append(match_pattern)
    for url in (converter_url, middleware_url):
        parts = urlsplit(url)
        origin_pattern = f"{parts.scheme}://{parts.netloc}/*"
        if origin_pattern not in manifest["host_permissions"]:
            manifest["host_permissions"].append(origin_pattern)
    for entry in manifest["content_scripts"]:
        if match_pattern not in entry["matches"]:
            entry["matches"].append(match_pattern)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    replacements.append(
        Replacement("extension/manifest.json", "test origin in matches", 1, 1)
    )

    background_path = target / "background.js"
    background = background_path.read_text(encoding="utf-8")

    background, item = _replace_once(
        background,
        "const SECRET_TOKEN = 'mi-proyecto-middleware-2024-epn';",
        f"const SECRET_TOKEN = '{token}';",
        "background.js",
        "hardcoded conversion token",
    )
    replacements.append(item)

    background, item = _replace_once(
        background,
        "const SERVIDOR_CONVERSION = 'http://localhost:5000/convertir';",
        f"const SERVIDOR_CONVERSION = '{converter_url}';",
        "background.js",
        "conversion endpoint",
    )
    replacements.append(item)

    background, item = _replace_once(
        background,
        "  'http://127.0.0.1:8000/api/interactions/protect';",
        f"  '{middleware_url}';",
        "background.js",
        "protection endpoint",
    )
    replacements.append(item)

    background, item = _replace_once(
        background,
        "  'https://gemini.google.com/*'\n];",
        f"  'https://gemini.google.com/*',\n  '{chat_origin}/*'\n];",
        "background.js",
        "supported sites allowlist",
    )
    replacements.append(item)

    background_path.write_text(background, encoding="utf-8")

    return BuildReport(destination=target, replacements=tuple(replacements))
