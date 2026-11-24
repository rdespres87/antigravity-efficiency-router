#!/usr/bin/env python3
"""Unit tests for local LM Studio dual-model detection and Maker directives."""

import json
import os
import sys
import unittest
import urllib.error
from typing import Any
from unittest.mock import MagicMock, patch

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import router  # noqa: E402


def _make_response(payload: dict[str, Any], status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    resp.read.return_value = json.dumps(payload).encode("utf-8")
    return resp


class TestLocalLmStatus(unittest.TestCase):
    def test_v0_models_filters_unloaded_and_embeddings(self) -> None:
        v0_payload = {
            "data": [
                {"id": "qwen3.8-27b-splash", "type": "vlm", "state": "loaded"},
                {"id": "qwen/qwen3.6-35b-a3b", "type": "vlm", "state": "loaded"},
                {"id": "qwen/qwen3.8-27b", "type": "vlm", "state": "not-loaded"},
                {"id": "text-embedding-nomic", "type": "embeddings", "state": "loaded"},
            ]
        }

        def fake_urlopen(req: Any, timeout: float = 0.15) -> MagicMock:
            self.assertIn("/api/v0/models", req.full_url)
            return _make_response(v0_payload)

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            self.assertEqual(router._check_local_lm_status(), " | local=dual(splash+35b)")

    def test_v0_models_single_loaded_ignores_unloaded_splash(self) -> None:
        v0_payload = {
            "data": [
                {"id": "qwen3.8-27b-splash", "type": "vlm", "state": "not-loaded"},
                {"id": "qwen/qwen3.6-35b-a3b", "type": "vlm", "state": "loaded"},
            ]
        }

        with patch("urllib.request.urlopen", return_value=_make_response(v0_payload)):
            self.assertEqual(router._check_local_lm_status(), " | local=qwen3.6-35b-a3")

    def test_v0_models_none_loaded(self) -> None:
        v0_payload = {
            "data": [
                {"id": "qwen3.8-27b-splash", "type": "vlm", "state": "not-loaded"},
            ]
        }

        with patch("urllib.request.urlopen", return_value=_make_response(v0_payload)):
            self.assertEqual(router._check_local_lm_status(), " | ⚠️ local=NO_MODEL")

    def test_fallback_to_v1_models_when_v0_fails(self) -> None:
        v1_payload = {
            "data": [
                {"id": "qwen3.8-27b-splash"},
                {"id": "qwen/qwen3.6-35b-a3b"},
                {"id": "text-embedding-nomic"},
            ]
        }

        def fake_urlopen(req: Any, timeout: float = 0.15) -> MagicMock:
            if "/api/v0/models" in req.full_url:
                raise urllib.error.URLError("v0 not supported")
            return _make_response(v1_payload)

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            self.assertEqual(router._check_local_lm_status(), " | local=dual(splash+35b)")

    def test_v0_models_ignores_entries_without_id(self) -> None:
        v0_payload = {
            "data": [
                {"state": "loaded", "type": "vlm"},
                {"id": "qwen3.8-27b-splash", "type": "vlm", "state": "loaded"},
            ]
        }

        with patch("urllib.request.urlopen", return_value=_make_response(v0_payload)):
            self.assertEqual(router._check_local_lm_status(), " | local=qwen3.8-27b-sp")

    def test_offline_when_both_endpoints_fail(self) -> None:
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            self.assertEqual(router._check_local_lm_status(), " | ⚠️ local=OFFLINE")


class TestBuildLocalDirective(unittest.TestCase):
    def test_none_hint_does_not_crash(self) -> None:
        self.assertEqual(
            router._build_local_directive(" | local=dual(splash+35b)", "GREEN", None),  # type: ignore[arg-type]
            "",
        )
    def test_red_quota_with_splash_forces_maker(self) -> None:
        directive = router._build_local_directive(" | local=dual(splash+35b)", "RED", "T0")
        self.assertIn("[LOCAL-FIRST MAKER]", directive)
        self.assertIn("MUST offload", directive)
        self.assertIn('role="maker"', directive)

    def test_yellow_quota_with_splash_suggests_maker(self) -> None:
        directive = router._build_local_directive(" | local=dual(splash+35b)", "YELLOW", "T3")
        self.assertIn("[LOCAL-FIRST MAKER]", directive)
        self.assertNotIn("MUST offload", directive)
        self.assertIn('role="maker"', directive)

    def test_green_quota_t1_t2_with_splash_suggests_maker(self) -> None:
        for hint in ("T1", "T2"):
            directive = router._build_local_directive(" | local=dual(splash+35b)", "GREEN", hint)
            self.assertIn("[LOCAL-FIRST MAKER]", directive)

    def test_green_quota_t0_t3_stays_silent(self) -> None:
        for hint in ("T0", "T3"):
            self.assertEqual(
                router._build_local_directive(" | local=dual(splash+35b)", "GREEN", hint),
                "",
            )

    def test_no_directive_when_splash_absent(self) -> None:
        self.assertEqual(
            router._build_local_directive(" | local=qwen3.6-35b-a3", "RED", "T2"),
            "",
        )
        self.assertEqual(
            router._build_local_directive(" | ⚠️ local=OFFLINE", "RED", "T2"),
            "",
        )


if __name__ == "__main__":
    unittest.main()
