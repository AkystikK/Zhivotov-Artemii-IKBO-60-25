from pathlib import Path
import subprocess
import sys
import unittest


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from main import read_config, validate_config


class ConfigTests(unittest.TestCase):
    def launch(self, config=None):
        command = [sys.executable, "-B", str(PROJECT / "src/main.py")]

        if config is not None:
            command += ["--config", str(config)]

        return subprocess.run(
            command, cwd=PROJECT / "src", capture_output=True,
            text=True, timeout=5,
        )

    def test_real_configuration(self):
        result = self.launch()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("package = junit:junit", result.stdout)
        self.assertIn("version = 4.13.2", result.stdout)
        self.assertIn("repository = https://", result.stdout)
        self.assertIn("test_mode = false", result.stdout)

    def test_local_configuration(self):
        result = self.launch(PROJECT / "tests/config_test.csv")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("package = A", result.stdout)
        self.assertIn("repository = repository.json", result.stdout)
        self.assertIn("test_mode = true", result.stdout)

    def test_errors_for_each_parameter(self):
        for name in ["package", "version", "repository", "mode"]:
            with self.subTest(name=name):
                config = PROJECT / f"tests/config_bad_{name}.csv"
                result = self.launch(config)

                self.assertEqual(result.returncode, 1)
                self.assertIn("Configuration error:", result.stdout)
                self.assertNotIn("Traceback", result.stderr)

    def test_missing_settings(self):
        for key in ["package", "version", "repository", "test_mode"]:
            with self.subTest(key=key):
                config = read_config(PROJECT / "config.csv")
                del config[key]

                with self.assertRaisesRegex(ValueError, key):
                    validate_config(config, PROJECT / "config.csv")

    def test_no_extra_name_or_version_rules(self):
        config = read_config(PROJECT / "config.csv")
        config["package"] = "example"
        config["version"] = "release example"

        validate_config(config, PROJECT / "config.csv")

    def test_missing_repository_file(self):
        path = PROJECT / "tests/config_test.csv"
        config = read_config(path)
        config["repository"] = "missing.json"

        with self.assertRaisesRegex(ValueError, "file not found"):
            validate_config(config, path)

    def test_missing_config_file(self):
        result = self.launch(PROJECT / "missing.csv")

        self.assertEqual(result.returncode, 1)
        self.assertIn("Configuration error:", result.stdout)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
