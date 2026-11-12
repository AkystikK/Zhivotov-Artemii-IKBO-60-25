from pathlib import Path
import subprocess
import sys
import unittest


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from main import build_graph, loading_order, read_config


class OrderTests(unittest.TestCase):
    def load_case(self, name):
        path = PROJECT / f"tests/config_{name}.csv"
        return build_graph(read_config(path), path)

    def test_single_package(self):
        self.assertEqual(loading_order(self.load_case("single")), ["A"])

    def test_chain(self):
        self.assertEqual(loading_order(self.load_case("chain")),
                         ["C", "B", "A"])

    def test_shared_dependency(self):
        graph = self.load_case("shared")
        order = loading_order(graph)

        self.assertEqual(order, ["D", "B", "C", "A"])
        self.assertEqual(len(order), len(set(order)))

        for package, dependencies in graph.items():
            for dependency in dependencies:
                self.assertLess(order.index(dependency), order.index(package))

    def test_cycle(self):
        with self.assertRaisesRegex(ValueError, "cycle"):
            loading_order(self.load_case("cycle"))

    def test_self_cycle(self):
        with self.assertRaisesRegex(ValueError, "cycle"):
            loading_order({"A": ["A"]})

    def test_cycle_after_independent_package(self):
        graph = {"A": ["B"], "B": ["A"], "C": []}

        with self.assertRaisesRegex(ValueError, "cycle"):
            loading_order(graph)

    def test_command_line(self):
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
