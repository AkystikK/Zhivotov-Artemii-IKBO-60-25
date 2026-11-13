"""Test recursive breadth-first dependency graph construction."""

import importlib.util
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "dependency_graph", PROJECT / "src/main.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
bfs = MODULE.bfs
build_graph = MODULE.build_graph
read_config = MODULE.read_config
read_test_repository = MODULE.read_test_repository


class GraphTests(unittest.TestCase):
    """Test graph traversal, dependency versions, and cycles."""

    def load_case(self, name):
        """Build the graph for a named local test configuration."""
        path = PROJECT / f"tests/config_{name}.csv"
        return build_graph(read_config(path), path)

    def test_single_package(self):
        """Handle a package with no dependencies."""
        self.assertEqual(self.load_case("single"), {"A": []})

    def test_transitive_chain(self):
        """Collect every dependency in a chain."""
        graph = self.load_case("chain")

        self.assertEqual(graph, {"A": ["B"], "B": ["C"], "C": []})

    def test_shared_dependency(self):
        """Handle a dependency shared by several packages."""
        graph = self.load_case("shared")

        self.assertEqual(graph["B"], ["D"])
        self.assertEqual(graph["C"], ["D"])
        self.assertEqual(list(graph), ["A", "B", "C", "D"])

    def test_cycle_is_preserved_and_finishes(self):
        """Keep cyclic edges without repeating the traversal."""
        graph = self.load_case("cycle")

        self.assertEqual(graph, {"A": ["B"], "B": ["C"], "C": ["A"]})

    def test_self_cycle(self):
        """Handle a package that depends on itself."""
        graph = {}
        bfs(["A"], graph, {"A"}, {"test_mode": "true"}, {"A": ["A"]})

        self.assertEqual(graph, {"A": ["A"]})

    def test_breadth_first_order_and_unreachable_package(self):
        """Visit breadth-first and omit unreachable packages."""
        repository = {
            "A": ["B", "C"], "B": ["D"], "C": ["E"],
            "D": [], "E": [], "Z": [],
        }
        graph = {}

        bfs(["A"], graph, {"A"}, {"test_mode": "true"}, repository)

        self.assertEqual(list(graph), ["A", "B", "C", "D", "E"])
        self.assertNotIn("Z", graph)

    def test_real_graph_uses_each_dependency_version(self):
        """Request the declared version of each dependency."""
        config = {
            "package": "example:root", "version": "1",
            "repository": "https://r", "test_mode": "false",
        }
        responses = [["example:a:2", "example:b:3"],
                     ["example:b:3"], []]

        with patch.object(
            MODULE, "get_dependencies", side_effect=responses
        ) as get:
            graph = build_graph(config, PROJECT / "config.csv")

        self.assertEqual(list(graph),
                         ["example:root:1", "example:a:2", "example:b:3"])
        self.assertEqual(get.call_count, 3)
        self.assertEqual(get.call_args_list[1].args,
                         ("example:a", "2", "https://r"))
        self.assertEqual(get.call_args_list[2].args,
                         ("example:b", "3", "https://r"))

    def test_missing_start_package(self):
        """Reject a starting package absent from the repository."""
        with self.assertRaisesRegex(ValueError, "not found"):
            bfs(["Z"], {}, {"Z"}, {"test_mode": "true"}, {"A": []})

    def test_invalid_test_repositories(self):
        """Reject malformed local repository data."""
        cases = [[], {"a": []}, {"A1": []}, {"A": "B"},
                 {"A": ["B"]}, {"A": [1]}]

        for repository in cases:
            with self.subTest(repository=repository):
                text = io.StringIO(json.dumps(repository))

                with patch.object(Path, "open", return_value=text):
                    with self.assertRaises(ValueError):
                        read_test_repository(Path("repository.json"))

    def test_cycle_from_command_line(self):
        """Print a cyclic graph and finish successfully."""
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
