from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from .errors import ToolUnavailable, ValidationError


SUMMARY_PATTERN = re.compile(
    r"Integrated loudness:\s*I:\s*(?P<lufs>-?(?:inf|\d+(?:\.\d+)?))\s*LUFS"
    r".*?Loudness range:\s*LRA:\s*(?P<lra>\d+(?:\.\d+)?)\s*LU"
    r".*?True peak:\s*Peak:\s*(?P<peak>-?(?:inf|\d+(?:\.\d+)?))\s*dBFS",
    re.IGNORECASE | re.DOTALL,
)


def inspect_media(path: Path) -> dict:
    ffprobe = shutil.which("ffprobe")
    ffmpeg = shutil.which("ffmpeg")
    if not ffprobe or not ffmpeg:
        raise ToolUnavailable("ffprobe and ffmpeg must both be available on PATH")

    probe = _run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "format=duration:stream=codec_name,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ]
    )
    try:
        raw = json.loads(probe.stdout)
        stream = raw["streams"][0]
        duration = float(raw["format"]["duration"])
        sample_rate = int(stream["sample_rate"])
        channels = int(stream["channels"])
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValidationError("ffprobe did not return a valid primary audio stream") from exc

    loudness = _run(
        [
            ffmpeg,
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-filter_complex",
            "ebur128=peak=true:framelog=verbose",
            "-f",
            "null",
            "-",
        ]
    )
    match = SUMMARY_PATTERN.search(loudness.stderr)
    if not match:
        raise ValidationError("FFmpeg EBU R128 summary could not be parsed")
    integrated = match.group("lufs").lower()
    integrated_lufs = None if integrated == "-inf" else float(integrated)

    result = {
        "duration_seconds": duration,
        "sample_rate_hz": sample_rate,
        "channels": channels,
        "codec": stream.get("codec_name", "unknown"),
        "integrated_lufs": integrated_lufs,
        "integrated_lufs_status": "below_measurement_floor" if integrated_lufs is None else "measured",
        "loudness_range_lu": float(match.group("lra")),
        "true_peak_dbtp": None if match.group("peak").lower() == "-inf" else float(match.group("peak")),
        "true_peak_status": (
            "below_measurement_floor" if match.group("peak").lower() == "-inf" else "measured"
        ),
    }
    _validate_result(result)
    return result


def tool_versions() -> dict:
    versions = {}
    for name in ("ffmpeg", "ffprobe"):
        executable = shutil.which(name)
        if not executable:
            versions[name] = {"available": False, "version": None, "path": None}
            continue
        completed = _run([executable, "-version"])
        versions[name] = {
            "available": True,
            "version": completed.stdout.splitlines()[0],
            "path": executable,
        }
    return versions


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if completed.returncode != 0:
        detail = completed.stderr.strip().splitlines()[-1] if completed.stderr.strip() else "unknown error"
        raise ValidationError(f"Media command failed: {detail}")
    return completed


def _validate_result(result: dict) -> None:
    if result["duration_seconds"] <= 0:
        raise ValidationError("Media duration must be positive")
    if result["sample_rate_hz"] <= 0:
        raise ValidationError("Sample rate must be positive")
    if result["channels"] <= 0:
        raise ValidationError("Channel count must be positive")
