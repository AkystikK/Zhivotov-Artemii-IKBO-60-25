import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from main import bfs, build_graph, read_config, read_test_repository


class GraphTests(unittest.TestCase):
    def load_case(self, name):
        path = PROJECT / f"tests/config_{name}.csv"
        return build_graph(read_config(path), path)

    def test_single_package(self):
        self.assertEqual(self.load_case("single"), {"A": []})

    def test_transitive_chain(self):
        graph = self.load_case("chain")

        self.assertEqual(graph, {"A": ["B"], "B": ["C"], "C": []})

    def test_shared_dependency(self):
        graph = self.load_case("shared")

        self.assertEqual(graph["B"], ["D"])
        self.assertEqual(graph["C"], ["D"])
        self.assertEqual(list(graph), ["A", "B", "C", "D"])

    def test_cycle_is_preserved_and_finishes(self):
        graph = self.load_case("cycle")

        self.assertEqual(graph, {"A": ["B"], "B": ["C"], "C": ["A"]})

    def test_self_cycle(self):
        graph = {}
        bfs(["A"], graph, {"A"}, {"test_mode": "true"}, {"A": ["A"]})

        self.assertEqual(graph, {"A": ["A"]})

    def test_breadth_first_order_and_unreachable_package(self):
        repository = {
            "A": ["B", "C"], "B": ["D"], "C": ["E"],
            "D": [], "E": [], "Z": [],
        }
        graph = {}

        bfs(["A"], graph, {"A"}, {"test_mode": "true"}, repository)

        self.assertEqual(list(graph), ["A", "B", "C", "D", "E"])
        self.assertNotIn("Z", graph)

    def test_real_graph_uses_each_dependency_version(self):
        config = {
            "package": "example:root", "version": "1",
            "repository": "https://r", "test_mode": "false",
        }
        responses = [["example:a:2", "example:b:3"],
                     ["example:b:3"], []]

        with patch("main.get_dependencies", side_effect=responses) as get:
            graph = build_graph(config, PROJECT / "config.csv")

        self.assertEqual(list(graph),
                         ["example:root:1", "example:a:2", "example:b:3"])
        self.assertEqual(get.call_count, 3)
        self.assertEqual(get.call_args_list[1].args,
                         ("example:a", "2", "https://r"))
        self.assertEqual(get.call_args_list[2].args,
                         ("example:b", "3", "https://r"))

    def test_missing_start_package(self):
        with self.assertRaisesRegex(ValueError, "not found"):
            bfs(["Z"], {}, {"Z"}, {"test_mode": "true"}, {"A": []})

    def test_invalid_test_repositories(self):
        cases = [[], {"a": []}, {"A1": []}, {"A": "B"},
                 {"A": ["B"]}, {"A": [1]}]

        for repository in cases:
            with self.subTest(repository=repository):
                text = io.StringIO(json.dumps(repository))

                with patch.object(Path, "open", return_value=text):
                    with self.assertRaises(ValueError):
                        read_test_repository(Path("repository.json"))

    def test_cycle_from_command_line(self):
        result = subprocess.run(
            [sys.executable, "-B", str(PROJECT / "src/main.py"),
             "--config", str(PROJECT / "tests/config_cycle.csv")],
            cwd=PROJECT / "src", text=True, capture_output=True, timeout=5,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("C -> A", result.stdout)
        self.assertEqual(result.stdout.count("A -> B"), 1)


if __name__ == "__main__":
    unittest.main()
