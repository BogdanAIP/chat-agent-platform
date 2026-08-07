from __future__ import annotations

import hashlib
import json
import mimetypes
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .errors import ValidationError
from .contracts import validate_contract


DATA_CLASSES = {"public", "project", "private", "sensitive"}


@dataclass
class Artifact:
    artifact_id: str
    type: str
    path: str
    mime: str
    size_bytes: int
    sha256: str
    created_by: str
    created_at: str
    status: str
    data_class: str
    metadata: dict
    external_policy: dict


class ArtifactStore:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.root / "manifest.json"

    def import_file(
        self, source: Path, *, created_by: str, data_class: str = "project"
    ) -> Artifact:
        source = source.resolve()
        if not source.is_file():
            raise ValidationError(f"Artifact source is not a file: {source}")
        if data_class not in DATA_CLASSES:
            raise ValidationError(f"Unknown data class: {data_class}")

        artifact_id = f"art_{uuid4().hex}"
        destination = (self.root / artifact_id / source.name).resolve()
        if self.root not in destination.parents:
            raise ValidationError("Resolved artifact path escapes Artifact Store")
        destination.parent.mkdir(parents=True, exist_ok=False)
        shutil.copy2(source, destination)
        digest = _sha256(destination)
        mime = mimetypes.guess_type(destination.name)[0] or "application/octet-stream"
        artifact = Artifact(
            artifact_id=artifact_id,
            type=_artifact_type(mime),
            path=str(destination),
            mime=mime,
            size_bytes=destination.stat().st_size,
            sha256=digest,
            created_by=created_by,
            created_at=datetime.now(UTC).isoformat(),
            status="ready",
            data_class=data_class,
            metadata={},
            external_policy={"staging_allowed": False, "allowed_executors": []},
        )
        validate_contract(asdict(artifact), "artifact-v1.schema.json")
        self._append(artifact)
        return artifact

    def update_metadata(self, artifact: Artifact, metadata: dict) -> Artifact:
        if _sha256(Path(artifact.path)) != artifact.sha256:
            raise ValidationError(f"Artifact hash changed after import: {artifact.artifact_id}")
        artifact.metadata.update(metadata)
        validate_contract(asdict(artifact), "artifact-v1.schema.json")
        entries = self._read_manifest()
        entries[artifact.artifact_id] = asdict(artifact)
        self._write_manifest(entries)
        return artifact

    def _append(self, artifact: Artifact) -> None:
        entries = self._read_manifest()
        entries[artifact.artifact_id] = asdict(artifact)
        self._write_manifest(entries)

    def _read_manifest(self) -> dict:
        if not self.manifest_path.exists():
            return {}
        try:
            value = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValidationError("Artifact manifest is corrupt") from exc
        return value

    def _write_manifest(self, entries: dict) -> None:
        temporary = self.manifest_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.manifest_path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _artifact_type(mime: str) -> str:
    return mime.split("/", 1)[0] if "/" in mime else "binary"
