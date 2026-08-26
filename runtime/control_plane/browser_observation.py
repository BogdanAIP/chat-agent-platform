from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from .verification import ObservationRef, ObservationSnapshot


BROWSER_PAGE_CAPABILITY = "browser.page"
MAX_BROWSER_SNAPSHOT_CHARS = 1_000_000
MAX_BROWSER_CONTROLS = 512
MAX_BROWSER_TEXT_CHARS = 4096
MAX_BROWSER_ID_CHARS = 512

_ALLOWED_TOP_LEVEL = {
    "url",
    "title",
    "document_id",
    "snapshot_text",
    "controls",
    "settled",
    "complete",
    "ambiguous",
}
_ALLOWED_CONTROL_FIELDS = {
    "control_id",
    "role",
    "name",
    "enabled",
    "checked",
    "selected",
    "visible",
    "value",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_bool(value: Any, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{name} must be bool")
    return value


def _bounded_text(
    value: Any,
    *,
    name: str,
    max_chars: int = MAX_BROWSER_TEXT_CHARS,
    allow_none: bool = False,
    allow_empty: bool = True,
) -> str | None:
    if value is None and allow_none:
        return None
    if type(value) is not str:
        raise TypeError(f"{name} must be a string")
    if not allow_empty and not value:
        raise ValueError(f"{name} must be non-empty")
    if len(value) > max_chars:
        raise ValueError(f"{name} exceeds {max_chars} characters")
    return value


def canonicalize_browser_url(value: Any) -> tuple[str, str]:
    raw = _bounded_text(
        value,
        name="browser url",
        max_chars=4096,
        allow_empty=False,
    )
    assert raw is not None
    if raw != raw.strip() or any(ord(char) < 32 for char in raw):
        raise ValueError("browser url contains surrounding whitespace or control characters")

    # The isolated Playwright session starts at this one browser-internal state.
    # It is admissible only as observation evidence, never as a web_open target.
    if raw.lower() == "about:blank":
        return "about:blank", "about:"

    try:
        parsed = urlsplit(raw)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("browser url is invalid") from exc

    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise ValueError("browser url must use http or https, except observed about:blank")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("browser url must not contain credentials")
    if not parsed.hostname:
        raise ValueError("browser url requires a hostname")

    try:
        hostname = parsed.hostname.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValueError("browser hostname is invalid") from exc

    rendered_host = f"[{hostname}]" if ":" in hostname else hostname
    default_port = 443 if scheme == "https" else 80
    netloc = rendered_host if port in {None, default_port} else f"{rendered_host}:{port}"
    path = parsed.path or "/"
    canonical = urlunsplit((scheme, netloc, path, parsed.query, parsed.fragment))
    origin = f"{scheme}://{netloc}"
    return canonical, origin


def _normalize_control(raw: Any) -> tuple[str, dict[str, Any]]:
    if type(raw) is not dict:
        raise TypeError("browser control must be a plain dict")
    extra = set(raw) - _ALLOWED_CONTROL_FIELDS
    if extra:
        raise ValueError(f"browser control contains unsupported fields: {sorted(extra)}")
    if "control_id" not in raw or "role" not in raw:
        raise ValueError("browser control requires control_id and role")

    control_id = _bounded_text(
        raw["control_id"],
        name="browser control_id",
        max_chars=MAX_BROWSER_ID_CHARS,
        allow_empty=False,
    )
    role = _bounded_text(
        raw["role"],
        name="browser control role",
        max_chars=256,
        allow_empty=False,
    )
    assert control_id is not None and role is not None

    normalized: dict[str, Any] = {
        "role": role,
        "name": _bounded_text(
            raw.get("name"),
            name="browser control name",
            allow_none=True,
        ),
        "enabled": None,
        "checked": None,
        "selected": None,
        "visible": None,
        "value": _bounded_text(
            raw.get("value"),
            name="browser control value",
            allow_none=True,
        ),
    }
    for field in ("enabled", "checked", "selected", "visible"):
        value = raw.get(field)
        normalized[field] = None if value is None else _require_bool(value, name=f"browser control {field}")
    return control_id, normalized


def normalize_browser_observation(raw: Any) -> tuple[dict[str, Any], bool, bool]:
    """Normalize one bounded browser observation into verifier-safe plain state.

    The adapter intentionally accepts data only. It cannot call a browser, run
    JavaScript, select a backend or authorize an action. A higher capability
    adapter must collect current browser evidence and explicitly declare whether
    that collection is complete/ambiguous.
    """

    if type(raw) is not dict:
        raise TypeError("browser observation must be a plain dict")
    extra = set(raw) - _ALLOWED_TOP_LEVEL
    if extra:
        raise ValueError(f"browser observation contains unsupported fields: {sorted(extra)}")
    required = {"url", "title", "snapshot_text", "controls", "settled", "complete", "ambiguous"}
    missing = required - set(raw)
    if missing:
        raise ValueError(f"browser observation is missing required fields: {sorted(missing)}")

    complete = _require_bool(raw["complete"], name="browser observation complete")
    declared_ambiguous = _require_bool(raw["ambiguous"], name="browser observation ambiguous")
    canonical_url, origin = canonicalize_browser_url(raw["url"])
    title = _bounded_text(raw["title"], name="browser title", allow_none=True)
    document_id = _bounded_text(
        raw.get("document_id"),
        name="browser document_id",
        max_chars=MAX_BROWSER_ID_CHARS,
        allow_none=True,
    )
    snapshot_text = _bounded_text(
        raw["snapshot_text"],
        name="browser snapshot_text",
        max_chars=MAX_BROWSER_SNAPSHOT_CHARS,
        allow_none=True,
    )

    settled_value = raw["settled"]
    if settled_value is None:
        settled = None
    else:
        settled = _require_bool(settled_value, name="browser settled")

    if complete and snapshot_text is None:
        raise ValueError("complete browser observation requires snapshot_text")
    if complete and settled is None:
        raise ValueError("complete browser observation requires settled state")

    raw_controls = raw["controls"]
    if type(raw_controls) is not list:
        raise TypeError("browser controls must be a plain list")
    if len(raw_controls) > MAX_BROWSER_CONTROLS:
        raise ValueError(f"browser controls exceed {MAX_BROWSER_CONTROLS} items")

    controls: dict[str, dict[str, Any]] = {}
    collisions: set[str] = set()
    for raw_control in raw_controls:
        control_id, control = _normalize_control(raw_control)
        if control_id in collisions:
            continue
        if control_id in controls:
            controls.pop(control_id, None)
            collisions.add(control_id)
            continue
        controls[control_id] = control

    controls = {key: controls[key] for key in sorted(controls)}
    collision_list = sorted(collisions)
    snapshot_sha256 = (
        hashlib.sha256(snapshot_text.encode("utf-8")).hexdigest()
        if snapshot_text is not None
        else None
    )
    state = {
        "url": canonical_url,
        "origin": origin,
        "document": {
            "id": document_id,
            "title": title,
            "snapshot_sha256": snapshot_sha256,
        },
        "settled": settled,
        "controls": controls,
        "control_collisions": collision_list,
        "control_count": len(raw_controls),
        "verified_control_count": len(controls),
    }
    state["page_state_sha256"] = hashlib.sha256(
        json.dumps(
            state,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return state, complete, declared_ambiguous or bool(collisions)


class BrowserObservationStream:
    """One monotonic observation stream for one bound browser page/session subject."""

    def __init__(
        self,
        *,
        subject: str,
        stream_id: str | None = None,
    ) -> None:
        normalized_subject = _bounded_text(
            subject,
            name="browser observation subject",
            max_chars=MAX_BROWSER_ID_CHARS,
            allow_empty=False,
        )
        assert normalized_subject is not None
        self._subject = normalized_subject
        self._stream_id = stream_id or secrets.token_hex(16)
        _bounded_text(
            self._stream_id,
            name="browser observation stream_id",
            max_chars=MAX_BROWSER_ID_CHARS,
            allow_empty=False,
        )
        self._sequence = 0

    @property
    def subject(self) -> str:
        return self._subject

    @property
    def stream_id(self) -> str:
        return self._stream_id

    def observe(self, raw: dict[str, Any]) -> ObservationSnapshot:
        state, complete, ambiguous = normalize_browser_observation(raw)
        self._sequence += 1
        fingerprint_payload = {
            "state": state,
            "complete": complete,
            "ambiguous": ambiguous,
        }
        fingerprint = hashlib.sha256(
            json.dumps(
                fingerprint_payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return ObservationSnapshot(
            ref=ObservationRef(
                capability=BROWSER_PAGE_CAPABILITY,
                subject=self._subject,
                stream_id=self._stream_id,
                sequence=self._sequence,
                fingerprint=fingerprint,
                observed_at=_utc_now(),
            ),
            state=state,
            complete=complete,
            ambiguous=ambiguous,
        )
