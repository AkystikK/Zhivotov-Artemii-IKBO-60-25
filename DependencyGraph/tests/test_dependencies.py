import contextlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.error import URLError
import xml.etree.ElementTree as ET


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from main import get_dependencies, main


POM = b"""<project xmlns="http://maven.apache.org/POM/4.0.0">
    <dependencies>
        <dependency>
            <groupId>example</groupId>
            <artifactId>first</artifactId>
        </dependency>
        <dependency>
            <groupId>example</groupId>
            <artifactId>second</artifactId>
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
    def test_direct_dependencies_and_requested_version(self):
        with patch("main.urlopen", return_value=io.BytesIO(POM)) as request:
            result = get_dependencies("org.example:demo", "2.5", "https://r/")

        self.assertEqual(result, ["example:first", "example:second"])
        request.assert_called_once_with(
            "https://r/org/example/demo/2.5/demo-2.5.pom", timeout=10
        )

    def test_no_namespace(self):
        pom = POM.replace(b' xmlns="http://maven.apache.org/POM/4.0.0"', b"")

        with patch("main.urlopen", return_value=io.BytesIO(pom)):
            result = get_dependencies("example:demo", "1", "https://r")

        self.assertEqual(result, ["example:first", "example:second"])

    def test_no_dependencies(self):
        with patch("main.urlopen", return_value=io.BytesIO(b"<project/>")):
            result = get_dependencies("example:demo", "1", "https://r")

        self.assertEqual(result, [])

    def test_invalid_xml(self):
        with patch("main.urlopen", return_value=io.BytesIO(b"<broken")):
            with self.assertRaises(ET.ParseError):
                get_dependencies("example:demo", "1", "https://r")

    def test_wrong_document(self):
        with patch("main.urlopen", return_value=io.BytesIO(b"<html/>")):
            with self.assertRaisesRegex(ValueError, "Maven POM"):
                get_dependencies("example:demo", "1", "https://r")

    def test_network_error_message(self):
        output = io.StringIO()

        with patch.object(sys, "argv", ["main.py"]):
            with patch("main.urlopen", side_effect=URLError("unavailable")):
                with contextlib.redirect_stdout(output):
                    result = main()

        self.assertEqual(result, 1)
        self.assertIn("Dependency loading error:", output.getvalue())

    def test_output(self):
        output = io.StringIO()

        with patch.object(sys, "argv", ["main.py"]):
            with patch("main.urlopen", return_value=io.BytesIO(POM)):
                with contextlib.redirect_stdout(output):
                    result = main()

        self.assertEqual(result, 0)
        self.assertIn("junit:junit:4.13.2", output.getvalue())
        self.assertIn("example:first", output.getvalue())
        self.assertIn("example:second", output.getvalue())


if __name__ == "__main__":
    unittest.main()
