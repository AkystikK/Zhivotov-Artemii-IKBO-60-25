"""Test dependency-first loading order and cycle detection."""

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "dependency_graph", PROJECT / "src/main.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
build_graph = MODULE.build_graph
loading_order = MODULE.loading_order
read_config = MODULE.read_config


class OrderTests(unittest.TestCase):
    """Test dependency-first ordering and invalid cycles."""

    def load_case(self, name):
        """Build the graph for a named local test configuration."""
        path = PROJECT / f"tests/config_{name}.csv"
        return build_graph(read_config(path), path)

    def test_single_package(self):
        """Handle a package with no dependencies."""
        self.assertEqual(loading_order(self.load_case("single")), ["A"])

    def test_chain(self):
        """Place each dependency before its dependent package."""
        self.assertEqual(loading_order(self.load_case("chain")),
                         ["C", "B", "A"])

    def test_shared_dependency(self):
        """Handle a dependency shared by several packages."""
        graph = self.load_case("shared")
        order = loading_order(graph)

        self.assertEqual(order, ["D", "B", "C", "A"])
        self.assertEqual(len(order), len(set(order)))

        for package, dependencies in graph.items():
            for dependency in dependencies:
                self.assertLess(order.index(dependency), order.index(package))

    def test_cycle(self):
        """Handle a graph containing a dependency cycle."""
        with self.assertRaisesRegex(ValueError, "cycle"):
            loading_order(self.load_case("cycle"))

    def test_self_cycle(self):
        """Handle a package that depends on itself."""
        with self.assertRaisesRegex(ValueError, "cycle"):
            loading_order({"A": ["A"]})

    def test_cycle_after_independent_package(self):
        """Reject a cycle even after processing independent nodes."""
        graph = {"A": ["B"], "B": ["A"], "C": []}

        with self.assertRaisesRegex(ValueError, "cycle"):
            loading_order(graph)

    def test_command_line(self):
        """Print the dependency-first order from the command line."""
        for name, code in [("shared", 0), ("cycle", 1)]:
            with self.subTest(name=name):
                result = subprocess.run(
                    [sys.executable, "-B", str(PROJECT / "src/main.py"),
                     "--config", str(PROJECT / f"tests/config_{name}.csv"),
                     "--order"], cwd=PROJECT / "src", text=True,
                    capture_output=True, timeout=5,
                )

                self.assertEqual(result.returncode, code, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

                if code == 0:
                    self.assertIn("D -> B -> C -> A", result.stdout)
                else:
                    self.assertIn("cycle", result.stdout)
                    self.assertNotIn("Loading order:", result.stdout)


if __name__ == "__main__":
    unittest.main()
