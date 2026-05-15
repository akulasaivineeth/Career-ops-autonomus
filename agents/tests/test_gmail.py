"""Gmail helpers (mocked HTTP client). BUILD.md Task 0.5."""

from __future__ import annotations

from unittest.mock import MagicMock

from agents.tools import gmail as gmail_mod


def test_search_returns_messages() -> None:
    service = MagicMock()
    execute = MagicMock(
        return_value={"messages": [{"id": "a1"}, {"id": "a2"}]},
    )
    service.users.return_value.messages.return_value.list.return_value.execute = execute
    out = gmail_mod.search(service, "from:test newer_than:1d", max_results=10)
    assert [m["id"] for m in out] == ["a1", "a2"]
    service.users.return_value.messages.return_value.list.assert_called_once_with(
        userId="me",
        q="from:test newer_than:1d",
        maxResults=10,
    )


def test_get_body_text_plain() -> None:
    service = MagicMock()
    service.users().messages().get().execute.return_value = {
        "payload": {
            "mimeType": "text/plain",
            "body": {"data": "SGVsbG8=", "size": 5},
        },
    }
    text = gmail_mod.get_body_text(service, "mid1")
    assert text == "Hello"


def test_mark_read_modifies() -> None:
    service = MagicMock()
    gmail_mod.mark_read(service, "mid2")
    service.users().messages().modify.assert_called_once()


def test_get_verification_code_finds_digits(mocker) -> None:
    service = MagicMock()
    mocker.patch.object(gmail_mod, "search", return_value=[{"id": "m1"}])
    mocker.patch.object(gmail_mod.time, "sleep", autospec=True)
    service.users().messages().get().execute.return_value = {
        "payload": {
            "mimeType": "text/plain",
            "body": {"data": "WW91ciBjb2RlIGlzIDEyMzQ1Ng==", "size": 24},
        },
    }
    code = gmail_mod.get_verification_code(
        service,
        "example.com",
        poll_seconds=30,
        interval=1,
        newer_than="1d",
    )
    assert code == "123456"
