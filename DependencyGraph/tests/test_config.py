"""Test CSV settings and configuration errors."""

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
read_config = MODULE.read_config
validate_config = MODULE.validate_config


class ConfigTests(unittest.TestCase):
    """Test reading and validating program settings."""

    def launch(self, config=None):
        """Run the program with an optional CSV configuration."""
        command = [sys.executable, "-B", str(PROJECT / "src/main.py")]

        if config is not None:
            command += ["--config", str(config)]

        return subprocess.run(
            command, cwd=PROJECT / "src", capture_output=True,
            text=True, timeout=5,
        )

    def test_real_configuration(self):
        """Read and validate the supplied Maven configuration."""
        path = PROJECT / "config.csv"
        config = read_config(path)

        validate_config(config, path)

        self.assertEqual(config["package"], "junit:junit")
        self.assertEqual(config["version"], "4.13.2")
        self.assertEqual(config["test_mode"], "false")

    def test_local_configuration(self):
        """Load the graph from a local test repository."""
        result = self.launch(PROJECT / "tests/config_test.csv")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Dependency graph:", result.stdout)
        self.assertIn("A -> B, C", result.stdout)

    def test_errors_for_each_parameter(self):
        """Report invalid values for each configuration field."""
        for name in ["package", "version", "repository", "mode"]:
            with self.subTest(name=name):
                config = PROJECT / f"tests/config_bad_{name}.csv"
                result = self.launch(config)

                self.assertEqual(result.returncode, 1)
                self.assertIn("Configuration error:", result.stdout)
                self.assertNotIn("Traceback", result.stderr)

    def test_missing_settings(self):
        """Reject each missing required setting."""
        for key in ["package", "version", "repository", "test_mode"]:
            with self.subTest(key=key):
                config = read_config(PROJECT / "config.csv")
                del config[key]

                with self.assertRaisesRegex(ValueError, key):
                    validate_config(config, PROJECT / "config.csv")

    def test_no_extra_name_or_version_rules(self):
        """Avoid imposing extra package or version restrictions."""
        config = read_config(PROJECT / "config.csv")
        config["package"] = "example"
        config["version"] = "release example"

        validate_config(config, PROJECT / "config.csv")

    def test_missing_repository_file(self):
        """Reject a missing local repository file."""
        path = PROJECT / "tests/config_test.csv"
        config = read_config(path)
        config["repository"] = "missing.json"

        with self.assertRaisesRegex(ValueError, "file not found"):
            validate_config(config, path)

    def test_missing_config_file(self):
        """Report a missing CSV configuration file."""
        result = self.launch(PROJECT / "missing.csv")

        self.assertEqual(result.returncode, 1)
        self.assertIn("Configuration error:", result.stdout)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
