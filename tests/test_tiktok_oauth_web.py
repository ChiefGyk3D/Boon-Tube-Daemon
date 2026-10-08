#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tests for HTML escaping in the TikTok OAuth callback page."""

import importlib.util
import io
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "tiktok_oauth_web",
    Path(__file__).parent.parent / "scripts" / "tiktok_oauth_web.py",
)
tiktok_oauth_web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tiktok_oauth_web)

PAYLOAD = "<script>alert(1)</script>"


def test_build_error_html_escapes_payload():
    page = tiktok_oauth_web.build_error_html(PAYLOAD)
    assert "&lt;script&gt;" in page
    assert "<script>" not in page


def test_build_error_html_escapes_quotes():
    page = tiktok_oauth_web.build_error_html('"onload="x')
    assert '"onload' not in page


def test_handler_escapes_error_description():
    handler = tiktok_oauth_web.CallbackHandler.__new__(tiktok_oauth_web.CallbackHandler)
    handler.path = "/callback?error=access_denied&error_description=" + PAYLOAD
    handler.headers = {}
    handler.wfile = io.BytesIO()
    handler.send_response = lambda *a, **k: None
    handler.send_header = lambda *a, **k: None
    handler.end_headers = lambda: None
    handler.do_GET()
    body = handler.wfile.getvalue().decode()
    assert "&lt;script&gt;" in body
    assert "<script>" not in body
