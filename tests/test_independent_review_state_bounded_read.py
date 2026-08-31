from __future__ import annotations

import io
import unittest

from runtime.control_plane import independent_review_state as review_state


class RecordingReader(io.BytesIO):
    def __init__(self, payload: bytes) -> None:
        super().__init__(payload)
        self.requested_sizes: list[int] = []

    def read(self, size: int = -1) -> bytes:
        self.requested_sizes.append(size)
        return super().read(size)


class RecordingPath:
    def __init__(self, reader: RecordingReader) -> None:
        self.reader = reader
        self.modes: list[str] = []

    def open(self, mode: str):
        self.modes.append(mode)
        self.reader.seek(0)
        return self.reader


class IndependentReviewBoundedReadTests(unittest.TestCase):
    def test_loader_reads_only_maximum_plus_one_before_rejecting_oversize(self) -> None:
        maximum = 64
        reader = RecordingReader(b"x" * 4096)
        path = RecordingPath(reader)

        with self.assertRaisesRegex(
            review_state.ReviewStateError,
            r"checkpoint exceeds the accepted encoded bound",
        ):
            review_state._load_json_object(
                path,
                "checkpoint",
                maximum_bytes=maximum,
            )

        self.assertEqual(["rb"], path.modes)
        self.assertEqual([maximum + 1], reader.requested_sizes)
        self.assertEqual(maximum + 1, reader.tell())

    def test_loader_still_accepts_valid_json_below_bound(self) -> None:
        payload = b'{"value": 1}'
        reader = RecordingReader(payload)
        path = RecordingPath(reader)

        value = review_state._load_json_object(
            path,
            "checkpoint",
            maximum_bytes=64,
        )

        self.assertEqual({"value": 1}, value)
        self.assertEqual([65], reader.requested_sizes)


if __name__ == "__main__":
    unittest.main()
