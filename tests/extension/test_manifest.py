import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_manifest_uses_mv3_minimal_sensitive_permissions():
    manifest = json.loads((ROOT / "extension" / "manifest.json").read_text())

    assert manifest["manifest_version"] == 3
    assert "storage" in manifest["permissions"]
    assert "activeTab" in manifest["permissions"]
    assert "tabs" not in manifest["permissions"]
    assert "history" not in manifest["permissions"]
    assert "cookies" not in manifest["permissions"]
    assert "object-src 'none'" in manifest["content_security_policy"]["extension_pages"]
    assert manifest["action"]["default_popup"] == "src/popup/popup.html"


def test_extension_loads_privacy_before_injector():
    manifest = json.loads((ROOT / "extension" / "manifest.json").read_text())
    scripts = manifest["content_scripts"][0]["js"]

    assert scripts.index("src/utils/hash.js") < scripts.index("src/content/injector.js")
    assert scripts.index("src/heuristics/localScorer.js") < scripts.index("src/content/injector.js")
