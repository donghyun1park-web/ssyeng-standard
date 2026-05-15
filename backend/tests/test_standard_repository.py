import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.standard_repository import StandardRepository


def write_items(path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "id": "std-1",
                    "category": "mechanical",
                    "section": "pipe",
                    "title": "Pipe support",
                    "summary": "Support spacing",
                    "body": "Use the approved support spacing.",
                    "keywords": ["pipe"],
                    "checklist": [],
                }
            ]
        ),
        encoding="utf-8",
    )


class StandardRepositoryLoadingTest(unittest.TestCase):
    def setUp(self) -> None:
        if hasattr(StandardRepository, "_shared_cache"):
            StandardRepository._shared_cache.clear()

    def test_constructor_defers_loading_until_items_are_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_path = Path(tmp) / "standard_items.json"
            rag_path = Path(tmp) / "rag_index.json"
            write_items(data_path)

            with (
                patch.object(StandardRepository, "_load_items", side_effect=AssertionError("loaded eagerly")),
                patch.object(StandardRepository, "_load_rag_items", side_effect=AssertionError("loaded eagerly")),
            ):
                StandardRepository(data_path=data_path, rag_index_path=rag_path)

    def test_instances_share_loaded_items_when_sources_are_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_path = Path(tmp) / "standard_items.json"
            rag_path = Path(tmp) / "rag_index.json"
            write_items(data_path)

            calls = 0
            original_load_items = StandardRepository._load_items

            def counting_load_items(repo: StandardRepository):
                nonlocal calls
                calls += 1
                return original_load_items(repo)

            with patch.object(StandardRepository, "_load_items", counting_load_items):
                first = StandardRepository(data_path=data_path, rag_index_path=rag_path)
                second = StandardRepository(data_path=data_path, rag_index_path=rag_path)

                self.assertEqual(first.list_items(), second.list_items())

            self.assertEqual(calls, 1)

    def test_force_reload_bypasses_shared_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_path = Path(tmp) / "standard_items.json"
            rag_path = Path(tmp) / "rag_index.json"
            write_items(data_path)

            calls = 0
            original_load_items = StandardRepository._load_items

            def counting_load_items(repo: StandardRepository):
                nonlocal calls
                calls += 1
                return original_load_items(repo)

            with patch.object(StandardRepository, "_load_items", counting_load_items):
                first = StandardRepository(data_path=data_path, rag_index_path=rag_path)
                first.list_items()

                second = StandardRepository(data_path=data_path, rag_index_path=rag_path)
                second.reload_if_changed(force=True)

            self.assertEqual(calls, 2)


if __name__ == "__main__":
    unittest.main()
