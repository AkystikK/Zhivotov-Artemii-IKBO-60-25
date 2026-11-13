"""Test PlantUML output and output-mode selection."""

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
to_plantuml = MODULE.to_plantuml


class PlantumlTests(unittest.TestCase):
    """Test diagram components, arrows, and command-line output."""

    def test_isolated_node(self):
        """Declare a PlantUML component without edges."""
        result = to_plantuml({"A": []})

        self.assertEqual(result,
                         '@startuml\ncomponent "A" as P0\n@enduml')

    def test_shared_dependency(self):
        """Handle a dependency shared by several packages."""
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        result = to_plantuml(graph)

        self.assertEqual(result.count('component "D"'), 1)
        self.assertIn("P0 --> P1", result)
        self.assertIn("P0 --> P2", result)
        self.assertIn("P1 --> P3", result)
        self.assertIn("P2 --> P3", result)

    def test_cycle(self):
        """Handle a graph containing a dependency cycle."""
        result = to_plantuml({"A": ["B"], "B": ["A"]})

        self.assertIn("P0 --> P1", result)
        self.assertIn("P1 --> P0", result)

    def test_maven_name_is_a_quoted_label(self):
        """Quote Maven coordinates in a component label."""
        result = to_plantuml({"org.example:library:1.2": []})

        self.assertIn('component "org.example:library:1.2" as P0', result)

    def test_command_line_outputs_only_plantuml(self):
        """Print PlantUML without an extra graph heading."""
        result = subprocess.run(
            [sys.executable, "-B", str(PROJECT / "src/main.py"),
             "--config", str(PROJECT / "tests/config_cycle.csv"),
             "--plantuml"], cwd=PROJECT / "src", text=True,
            capture_output=True, timeout=5,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("@startuml\n"))
        self.assertTrue(result.stdout.rstrip().endswith("@enduml"))
        self.assertIn("P2 --> P0", result.stdout)
        self.assertNotIn("Dependency graph:", result.stdout)

    def test_incompatible_modes(self):
        """Reject simultaneous order and PlantUML options."""
        result = subprocess.run(
            [sys.executable, "-B", str(PROJECT / "src/main.py"),
             "--order", "--plantuml"], text=True,
            capture_output=True, timeout=5,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("not allowed", result.stderr)


if __name__ == "__main__":
    unittest.main()
