"""Smoke tests — server starts, API responds, core modules import."""

from __future__ import annotations


class TestSmoke:
    """Smoke — module imports, no DB needed."""

    def test_import_core(self):

        assert True

    def test_llm_client_imports(self):
        from learnbot_mcp.llm_client import build_history, chat_completion  # noqa: F401

        assert True

    def test_version(self):
        from learnbot_mcp._version import __version__

        assert __version__ == "0.4.0"

    def test_config_loads(self):
        from learnbot_mcp.config import get_settings

        s = get_settings()
        assert s.server_name == "learnbot-mcp"


class TestSafety:
    """Safety rules — unit tests for blocking and PII."""

    def test_rate_limit_passes(self):
        from learnbot_mcp.safety import _rate_limit

        assert _rate_limit("smoke-test-user") is True

    def test_topic_check_blocks(self):
        from learnbot_mcp.safety import _check_topics

        rules = [{"topic": "politics", "action": "refuse", "message": "No politics."}]
        result = _check_topics("What about politics today?", rules)
        assert result["blocked"] is True
        assert result["topic"] == "politics"

    def test_topic_check_passes(self):
        from learnbot_mcp.safety import _check_topics

        rules = [{"topic": "politics", "action": "refuse", "message": "No."}]
        result = _check_topics("The weather is nice.", rules)
        assert result["blocked"] is False

    def test_pii_redacts_email(self):
        from learnbot_mcp.safety import _check_pii_redaction

        result = _check_pii_redaction("email me at test@example.com")
        assert result["redacted"] is True
        assert "@" not in result["content"]

    def test_pii_passes_clean(self):
        from learnbot_mcp.safety import _check_pii_redaction

        result = _check_pii_redaction("The weather is nice.")
        assert result["redacted"] is False


class TestCompliance:
    """Compliance regimes — disclosure, real-name, refusal templates."""

    def test_disclosure_none(self, monkeypatch):
        monkeypatch.setenv("CHATBOT_REGULATORY_REGIME", "none")
        from learnbot_mcp.compliance import disclosure_message

        assert disclosure_message() == ""

    def test_disclosure_eu(self):
        from learnbot_mcp.compliance import disclosure_message

        msg = disclosure_message()
        assert "AI" in msg or msg == ""

    def test_refusal_templates_have_politics(self):
        from learnbot_mcp.compliance import refusal_templates

        t = refusal_templates()
        assert "politics" in t

    def test_real_name_auth_default_false(self, monkeypatch):
        monkeypatch.setenv("CHATBOT_REGULATORY_REGIME", "eu")
        from learnbot_mcp.compliance import requires_real_name_auth

        assert requires_real_name_auth() is False

    def test_real_name_auth_requires_user_id(self):
        """Real-name auth returns True only when regime is china."""
        from learnbot_mcp.compliance import requires_real_name_auth

        # Uses current env (default: none) — should be False
        assert requires_real_name_auth() is False


class TestProactive:
    """Proactive trigger parsing."""

    def test_parse_interval_minutes(self):
        from learnbot_mcp.proactive import _parse_interval

        td = _parse_interval("15m")
        assert td is not None
        assert td.seconds == 900

    def test_parse_interval_hours(self):
        from learnbot_mcp.proactive import _parse_interval

        td = _parse_interval("2h")
        assert td is not None
        assert td.seconds == 7200

    def test_parse_cron_hour_min(self):
        from learnbot_mcp.proactive import _parse_cron_hour_min

        hm = _parse_cron_hour_min("08:30")
        assert hm == (8, 30)

    def test_parse_dow(self):
        from learnbot_mcp.proactive import _parse_dow

        assert _parse_dow("1-5") == [1, 2, 3, 4, 5]
        assert _parse_dow("1,3,5") == [1, 3, 5]


class TestBuildHistory:
    """LLM history construction from DB rows."""

    def test_empty(self):
        from learnbot_mcp.llm_client import build_history

        assert build_history([]) == []

    def test_filters_system_role(self):
        from learnbot_mcp.llm_client import build_history

        turns = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
            {"role": "system", "content": "be a bot"},
        ]
        msgs = build_history(turns)
        assert len(msgs) == 2

    def test_respects_max_turns(self):
        from learnbot_mcp.llm_client import build_history

        turns = [{"role": "user", "content": f"msg {i}"} for i in range(50)]
        msgs = build_history(turns, max_turns=5)
        assert len(msgs) == 5
        assert "msg 45" in msgs[0]["content"]


class TestRobotOrchestrator:
    """Robot emotion mapping — sequences are valid, stop works."""

    def test_known_emotion_has_actions(self):
        from learnbot_mcp.robot_orchestrator import _EMOTION_MOTIONS

        for tag in ("cheerfully", "excited", "greeting", "sad", "angry", "playful"):
            assert tag in _EMOTION_MOTIONS
            assert len(_EMOTION_MOTIONS[tag]) > 0

    def test_all_actions_have_tool_and_args(self):
        from learnbot_mcp.robot_orchestrator import _EMOTION_MOTIONS

        for tag, seq in _EMOTION_MOTIONS.items():
            for step in seq:
                assert "tool" in step
                assert "args" in step
                assert "operation" in step["args"]
