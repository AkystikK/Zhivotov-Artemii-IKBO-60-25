"""Test filesystem loading, command handling, and emulator startup."""

import base64
import contextlib
import hashlib
import importlib.util
import io
import os
import subprocess
import sys
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "Emulator" / "src"
SPEC = importlib.util.spec_from_file_location("emulator", SRC / "main.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
load_vfs = MODULE.load_vfs
run_command = MODULE.run_command


def memory_archive(entries):
    """Build an in-memory ZIP archive from name/data pairs."""
    buffer = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(buffer, "w") as archive:
            for name, data in entries:
                archive.writestr(name, data)
    buffer.seek(0)
    return buffer


class VfsTests(unittest.TestCase):
    """Test in-memory ZIP loading and command status codes."""

    def test_empty_archive_has_root(self):
        """Check that an empty archive creates the root directory."""
        vfs = load_vfs(memory_archive([]))
        self.assertEqual(vfs, {"/": {"type": "directory"}})

    def test_binary_data_survives_base64(self):
        """Check that Base64 preserves all byte values."""
        data = bytes(range(256))
        vfs = load_vfs(memory_archive([("binary.bin", data)]))
        node = vfs["/binary.bin"]
        self.assertEqual(node["type"], "file")
        self.assertEqual(node["size"], 256)
        self.assertEqual(base64.b64decode(node["content"]), data)

    def test_empty_file_is_not_directory(self):
        """Distinguish an empty file from a directory."""
        vfs = load_vfs(memory_archive([("empty.txt", b"")]))
        self.assertEqual(vfs["/empty.txt"]["type"], "file")
        self.assertEqual(vfs["/empty.txt"]["content"], "")
        self.assertEqual(vfs["/empty.txt"]["size"], 0)

    def test_implicit_parents_and_empty_directory(self):
        """Check implicit parents and explicit empty directories."""
        entries = [("a/b/c/note.txt", b"text"), ("a/b/empty/", b"")]
        vfs = load_vfs(memory_archive(entries))
        for name in ["/", "/a", "/a/b", "/a/b/c", "/a/b/empty"]:
            self.assertEqual(vfs[name]["type"], "directory")
        self.assertEqual(vfs["/a/b/c/note.txt"]["size"], 4)

    def test_explicit_parents_after_files(self):
        """Accept directory entries listed after their files."""
        entries = [("a/note.txt", b"text"), ("a/", b"")]
        self.assertIn("/a/note.txt", load_vfs(memory_archive(entries)))

    def test_unicode_names(self):
        """Preserve Unicode characters in virtual paths."""
        name = "caf\u00e9/note.txt"
        vfs = load_vfs(memory_archive([(name, b"text")]))
        self.assertIn("/" + name, vfs)

    def test_contents_remain_available_after_archive_closes(self):
        """Keep file contents available after closing the archive."""
        buffer = memory_archive([("note.txt", b"hello")])
        vfs = load_vfs(buffer)
        buffer.close()
        self.assertEqual(
            base64.b64decode(vfs["/note.txt"]["content"]), b"hello"
        )

    def test_no_extraction_or_archive_modification(self):
        """Reject extraction calls and preserve the source bytes."""
        buffer = memory_archive([("a/file.txt", b"hello")])
        before = buffer.getvalue()
        forbidden = AssertionError("Extraction is forbidden")
        with patch.object(zipfile.ZipFile, "extract", side_effect=forbidden):
            with patch.object(zipfile.ZipFile, "extractall",
                              side_effect=forbidden):
                vfs = load_vfs(buffer)
        self.assertIn("/a/file.txt", vfs)
        self.assertEqual(before, buffer.getvalue())

    def test_invalid_archive(self):
        """Reject data that is not a ZIP archive."""
        with self.assertRaises(zipfile.BadZipFile):
            load_vfs(io.BytesIO(b"not a ZIP"))

    def test_invalid_paths(self):
        """Reject absolute paths and parent traversal."""
        for name in ["../file.txt", "/absolute.txt", "a/../file.txt"]:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    load_vfs(memory_archive([(name, b"text")]))

    def test_duplicate_files(self):
        """Reject duplicate file entries."""
        entries = [("file.txt", b"first"), ("file.txt", b"second")]
        with self.assertRaises(ValueError):
            load_vfs(memory_archive(entries))

    def test_file_directory_conflicts(self):
        """Reject paths used as both files and directories."""
        cases = [
            [("a", b"file"), ("a/b.txt", b"text")],
            [("a/b.txt", b"text"), ("a", b"file")],
            [("a", b"file"), ("a/", b"")],
        ]
        for entries in cases:
            with self.subTest(entries=entries):
                with self.assertRaises(ValueError):
                    load_vfs(memory_archive(entries))

    def test_command_result_codes(self):
        """Check success, error, and exit status codes."""
        cases = [("", 0), ("ls", 0), ("ls /", 0), ("cd", 0),
                 ("cd /a", 0), ("exit", 2), ("unknown", 1),
                 ("ls a b", 1), ("cd a b", 1), ("exit extra", 1)]
        for command, expected in cases:
            with self.subTest(command=command):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(run_command(command), expected)


class StartupTests(unittest.TestCase):
    """Test emulator startup and interactive command execution."""

    @classmethod
    def setUpClass(cls):
        """Find the fixture directory supplied by the test runner."""
        value = os.environ.get("VFS_FIXTURE_DIR")
        if not value:
            raise RuntimeError("Set VFS_FIXTURE_DIR to generated fixtures")
        cls.fixtures = Path(value).resolve()

    def launch(self, arguments, input_text=""):
        """Run the emulator with captured input and output."""
        command = [sys.executable, "-B", str(SRC / "main.py")]
        return subprocess.run(
            command + arguments, input=input_text, text=True,
            encoding="utf-8", capture_output=True, timeout=10,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            cwd=str(self.fixtures),
        )

    def arguments(self, archive="multiple.zip", script="startup_vfs.txt"):
        """Build launch arguments for an archive and startup file."""
        args = ["--vfs", str(self.fixtures / archive)]
        if script:
            args += ["--script", str(ROOT / "Emulator/tests" / script)]
        return args

    def test_all_vfs_variants(self):
        """Launch the emulator with each valid test archive."""
        for name in ["minimal.zip", "multiple.zip", "deep.zip"]:
            with self.subTest(name=name):
                result = self.launch(self.arguments(name))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("DEBUG: VFS loaded:", result.stdout)
                self.assertIn("Command: ls,", result.stdout)
                self.assertNotIn("Traceback", result.stderr)

    def test_deep_structure_and_binary_fixture(self):
        """Check nested paths and binary file contents."""
        result = self.launch(self.arguments("deep.zip"))
        path = "/documents/course/week1/data.bin"
        self.assertIn(f"VFS file {path}, size=4 bytes", result.stdout)
        vfs = load_vfs(self.fixtures / "deep.zip")
        self.assertEqual(
            base64.b64decode(vfs[path]["content"]), b"\x00\xff\x80\x01"
        )

    def test_source_archives_unchanged_and_no_extracted_files(self):
        """Preserve source archives and avoid extracted files."""
        before_names = sorted(p.name for p in self.fixtures.iterdir())
        for name in ["minimal.zip", "multiple.zip", "deep.zip"]:
            path = self.fixtures / name
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            self.launch(self.arguments(name))
            after = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(before, after)
        after_names = sorted(p.name for p in self.fixtures.iterdir())
        self.assertEqual(before_names, after_names)

    def test_vfs_load_errors(self):
        """Report missing, invalid, and damaged archives."""
        for name in ["missing.zip", "invalid.zip", "corrupt.zip"]:
            with self.subTest(name=name):
                result = self.launch(self.arguments(name))
                self.assertEqual(result.returncode, 1)
                self.assertIn("VFS loading error:", result.stdout)
                self.assertNotIn("Command:", result.stdout)
                self.assertNotIn("Traceback", result.stderr)

    def test_startup_stops_at_every_command_error(self):
        """Stop the startup script at its first command error."""
        scripts = ["startup_error.txt", "startup_bad_ls.txt",
                   "startup_bad_cd.txt", "startup_bad_exit.txt"]
        for script in scripts:
            with self.subTest(script=script):
                result = self.launch(self.arguments(script=script), "exit\n")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("Startup script stopped", result.stdout)
                self.assertNotIn("SHOULD_NOT_RUN", result.stdout)
                self.assertNotIn("cd documents", result.stdout)

    def test_missing_startup_file_returns_to_interactive_mode(self):
        """Enter interactive mode when the startup file is missing."""
        result = self.launch(self.arguments(script="missing.txt"), "exit\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Script reading error:", result.stdout)

    def test_interactive_without_script(self):
        """Run interactive commands without a startup script."""
        result = self.launch(
            self.arguments(script=None), "\nunknown\nls /\nexit\n"
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("script_path = None", result.stdout)
        self.assertIn("unknown command", result.stdout)
        self.assertIn("Command: ls,", result.stdout)

    def test_exit_in_startup_does_not_enter_interactive_mode(self):
        """Exit immediately when the startup script requests it."""
        result = self.launch(self.arguments(), "unknown\n")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("unknown command", result.stdout)

    def test_command_line_errors(self):
        """Reject invalid command-line arguments."""
        cases = [[], ["--vfs"], ["--vfs", "x", "--script"],
                 ["--vfs", "x", "--unknown"]]
        for arguments in cases:
            with self.subTest(arguments=arguments):
                result = self.launch(arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("error:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_help(self):
        """Show the supported command-line arguments."""
        result = self.launch(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("--vfs", result.stdout)
        self.assertIn("--script", result.stdout)


if __name__ == "__main__":
    unittest.main()
