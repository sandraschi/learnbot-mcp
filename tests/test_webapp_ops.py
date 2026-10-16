"""webapp_ops surface — UI map, diagnose handler, REST route registration."""

from __future__ import annotations

import json
from pathlib import Path


class TestUiMap:
    def test_map_has_14_routes(self):
        from learnbot_mcp.webapp_ops import load_ui_map

        ui_map = load_ui_map()
        assert len(ui_map["routes"]) == 14
        assert "demo_60s" in ui_map["tour_presets"]

    def test_tour_unknown_route_fails_with_known_paths(self):
        import asyncio

        from learnbot_mcp.webapp_ops import op_tour_page

        receipt = asyncio.run(op_tour_page(route="/nope"))
        assert receipt["success"] is False
        assert "14 known paths" in receipt["error"]


class TestDiagnoseRoute:
    def test_route_registered(self):
        from learnbot_mcp.api import build_app

        paths = [r.path for r in build_app().routes if hasattr(r, "path")]
        assert "/api/webapp/diagnose" in paths

    def test_handler_returns_shape(self):
        import asyncio

        from learnbot_mcp.api import api_webapp_diagnose

        snapshot = (
            Path(__file__).resolve().parents[1]
            / "demos"
            / "webapp-ops-pilot"
            / "last-diagnosis.json"
        )
        backup = snapshot.read_text(encoding="utf-8") if snapshot.is_file() else None
        try:
            resp = asyncio.run(api_webapp_diagnose(None))
            body = json.loads(resp.body.decode("utf-8"))
            assert body["operation"] == "diagnose_webapp"
            assert body["of"] == 14
            assert body["ok"] == 14
            assert len(body["pages"]) == 14
        finally:
            if backup is not None:
                snapshot.write_text(backup, encoding="utf-8")
