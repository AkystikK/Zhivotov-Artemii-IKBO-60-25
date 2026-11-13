"""Test direct dependency parsing and repository errors."""

import contextlib
import importlib.util
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError
from xml.etree import ElementTree


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "dependency_graph", PROJECT / "src/main.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
get_dependencies = MODULE.get_dependencies
main = MODULE.main


POM = b"""<project xmlns="http://maven.apache.org/POM/4.0.0">
    <properties>
        <library.version>1.0</library.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>example</groupId>
            <artifactId>first</artifactId>
            <version>${library.version}</version>
        </dependency>
        <dependency>
            <groupId>example</groupId>
            <artifactId>second</artifactId>
            <version>${project.version}</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>example</groupId>
                <artifactId>not-a-direct-dependency</artifactId>
            </dependency>
        </dependencies>
    </dependencyManagement>
</project>"""


class DependencyTests(unittest.TestCase):
    """Test direct dependencies read from Maven POM files."""

    def test_direct_dependencies_and_requested_version(self):
        """Read direct dependencies and request the chosen version."""
        with patch.object(
            MODULE, "urlopen", return_value=io.BytesIO(POM)
        ) as request:
            result = get_dependencies("org.example:demo", "2.5", "https://r/")

        self.assertEqual(result, ["example:first:1.0", "example:second:2.5"])
        request.assert_called_once_with(
            "https://r/org/example/demo/2.5/demo-2.5.pom", timeout=10
        )

    def test_no_namespace(self):
        """Read a POM without an XML namespace."""
        pom = POM.replace(b' xmlns="http://maven.apache.org/POM/4.0.0"', b"")

        with patch.object(MODULE, "urlopen", return_value=io.BytesIO(pom)):
            result = get_dependencies("example:demo", "1", "https://r")

        self.assertEqual(result, ["example:first:1.0", "example:second:1"])

    def test_no_dependencies(self):
        """Accept a POM without dependencies."""
        with patch.object(
            MODULE, "urlopen", return_value=io.BytesIO(b"<project/>")
        ):
            result = get_dependencies("example:demo", "1", "https://r")

        self.assertEqual(result, [])

    def test_invalid_xml(self):
        """Reject malformed XML."""
        with patch.object(
            MODULE, "urlopen", return_value=io.BytesIO(b"<broken")
        ):
            with self.assertRaises(ElementTree.ParseError):
                get_dependencies("example:demo", "1", "https://r")

    def test_wrong_document(self):
        """Reject an XML document that is not a Maven POM."""
        with patch.object(
            MODULE, "urlopen", return_value=io.BytesIO(b"<html/>")
        ):
            with self.assertRaisesRegex(ValueError, "Maven POM"):
                get_dependencies("example:demo", "1", "https://r")

    def test_network_error_message(self):
        """Report a repository connection failure."""
        output = io.StringIO()

        with patch.object(sys, "argv", ["main.py"]):
            with patch.object(
                MODULE, "urlopen", side_effect=URLError("unavailable")
            ):
                with contextlib.redirect_stdout(output):
                    result = main()

        self.assertEqual(result, 1)
        self.assertIn("Dependency loading error:", output.getvalue())

    def test_output(self):
        """Print the graph obtained from the dependency reader."""
        output = io.StringIO()

        with patch.object(sys, "argv", ["main.py"]):
            with patch.object(MODULE, "get_dependencies", side_effect=[
                    ["example:first:1", "example:second:1"], [], []]):
                with contextlib.redirect_stdout(output):
                    result = main()

        self.assertEqual(result, 0)
        self.assertIn("junit:junit:4.13.2 ->", output.getvalue())
        self.assertIn("example:first", output.getvalue())
        self.assertIn("example:second", output.getvalue())


if __name__ == "__main__":
    unittest.main()
