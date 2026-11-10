import json
import re
from pathlib import Path


def test_content_script_is_declared_in_main_world() -> None:
    extension = Path(__file__).resolve().parents[2] / "browser-extension" / "extension"
    manifest = json.loads((extension / "manifest.json").read_text(encoding="utf-8"))
    entries = [entry for entry in manifest["content_scripts"] if "content.js" in entry["js"]]

    assert len(entries) == 1
    assert entries[0]["world"] == "MAIN"
    assert entries[0]["run_at"] == "document_start"
    assert "bridge.js" not in entries[0]["js"]
    assert entries[0]["matches"] == manifest["content_scripts"][0]["matches"]
    background = (extension / "background.js").read_text(encoding="utf-8")
    assert re.search(r"\.registerContentScripts\s*\(", background) is None
    assert "scripting" not in manifest["permissions"]
    assert "content-main" not in background
