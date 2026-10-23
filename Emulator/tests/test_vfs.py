import base64
import contextlib
import hashlib
import io
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "Emulator" / "src"
sys.path.insert(0, str(SRC))

from main import loadVfs, runCommand


def memoryArchive(entries):
    buffer = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(buffer, "w") as archive:
            for name, data in entries:
                archive.writestr(name, data)
    buffer.seek(0)
    return buffer


class VfsTests(unittest.TestCase):
    def testEmptyArchiveHasRoot(self):
        vfs = loadVfs(memoryArchive([]))
        self.assertEqual(vfs, {"/": {"type": "directory"}})

    def testBinaryDataSurvivesBase64(self):
        data = bytes(range(256))
        vfs = loadVfs(memoryArchive([("binary.bin", data)]))
        node = vfs["/binary.bin"]
        self.assertEqual(node["type"], "file")
        self.assertEqual(node["size"], 256)
        self.assertEqual(base64.b64decode(node["content"]), data)

    def testEmptyFileIsNotDirectory(self):
        vfs = loadVfs(memoryArchive([("empty.txt", b"")]))
        self.assertEqual(vfs["/empty.txt"]["type"], "file")
        self.assertEqual(vfs["/empty.txt"]["content"], "")
        self.assertEqual(vfs["/empty.txt"]["size"], 0)

    def testImplicitParentsAndEmptyDirectory(self):
        entries = [("a/b/c/note.txt", b"text"), ("a/b/empty/", b"")]
        vfs = loadVfs(memoryArchive(entries))
        for name in ["/", "/a", "/a/b", "/a/b/c", "/a/b/empty"]:
            self.assertEqual(vfs[name]["type"], "directory")
        self.assertEqual(vfs["/a/b/c/note.txt"]["size"], 4)

    def testExplicitParentsAfterFiles(self):
        entries = [("a/note.txt", b"text"), ("a/", b"")]
        self.assertIn("/a/note.txt", loadVfs(memoryArchive(entries)))

    def testUnicodeNames(self):
        name = "caf\u00e9/note.txt"
        vfs = loadVfs(memoryArchive([(name, b"text")]))
        self.assertIn("/" + name, vfs)

    def testContentsRemainAvailableAfterArchiveCloses(self):
        buffer = memoryArchive([("note.txt", b"hello")])
        vfs = loadVfs(buffer)
        buffer.close()
        self.assertEqual(
            base64.b64decode(vfs["/note.txt"]["content"]), b"hello"
        )

    def testNoExtractionOrArchiveModification(self):
        buffer = memoryArchive([("a/file.txt", b"hello")])
        before = buffer.getvalue()
        forbidden = AssertionError("Extraction is forbidden")
        with patch.object(zipfile.ZipFile, "extract", side_effect=forbidden):
            with patch.object(zipfile.ZipFile, "extractall",
                              side_effect=forbidden):
                vfs = loadVfs(buffer)
        self.assertIn("/a/file.txt", vfs)
        self.assertEqual(before, buffer.getvalue())

    def testInvalidArchive(self):
        with self.assertRaises(zipfile.BadZipFile):
            loadVfs(io.BytesIO(b"not a ZIP"))

    def testInvalidPaths(self):
        for name in ["../file.txt", "/absolute.txt", "a/../file.txt"]:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    loadVfs(memoryArchive([(name, b"text")]))

    def testDuplicateFiles(self):
        entries = [("file.txt", b"first"), ("file.txt", b"second")]
        with self.assertRaises(ValueError):
            loadVfs(memoryArchive(entries))

    def testFileDirectoryConflicts(self):
        cases = [
            [("a", b"file"), ("a/b.txt", b"text")],
            [("a/b.txt", b"text"), ("a", b"file")],
            [("a", b"file"), ("a/", b"")],
        ]
        for entries in cases:
            with self.subTest(entries=entries):
                with self.assertRaises(ValueError):
                    loadVfs(memoryArchive(entries))

    def testCommandResultCodes(self):
        cases = [("", 0), ("ls", 0), ("ls /", 0), ("cd", 0),
                 ("cd /a", 0), ("exit", 2), ("unknown", 1),
                 ("ls a b", 1), ("cd a b", 1), ("exit extra", 1)]
        for command, expected in cases:
            with self.subTest(command=command):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(runCommand(command), expected)


class StartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        value = os.environ.get("VFS_FIXTURE_DIR")
        if not value:
            raise RuntimeError("Set VFS_FIXTURE_DIR to generated fixtures")
        cls.fixtures = Path(value).resolve()

    def launch(self, arguments, inputText=""):
        command = [sys.executable, "-B", str(SRC / "main.py")]
        return subprocess.run(
            command + arguments, input=inputText, text=True,
            encoding="utf-8", capture_output=True, timeout=10,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            cwd=str(self.fixtures),
        )

    def arguments(self, archive="multiple.zip", script="startup_vfs.txt"):
        args = ["--vfs", str(self.fixtures / archive)]
        if script:
            args += ["--script", str(ROOT / "Emulator/tests" / script)]
        return args

    def testAllVfsVariants(self):
        for name in ["minimal.zip", "multiple.zip", "deep.zip"]:
            with self.subTest(name=name):
                result = self.launch(self.arguments(name))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("DEBUG: VFS loaded:", result.stdout)
                self.assertIn("Command: ls,", result.stdout)
                self.assertNotIn("Traceback", result.stderr)

    def testDeepStructureAndBinaryFixture(self):
        result = self.launch(self.arguments("deep.zip"))
        path = "/documents/course/week1/data.bin"
        self.assertIn(f"VFS file {path}, size=4 bytes", result.stdout)
        vfs = loadVfs(self.fixtures / "deep.zip")
        self.assertEqual(
            base64.b64decode(vfs[path]["content"]), b"\x00\xff\x80\x01"
        )

    def testSourceArchivesUnchangedAndNoExtractedFiles(self):
        beforeNames = sorted(p.name for p in self.fixtures.iterdir())
        for name in ["minimal.zip", "multiple.zip", "deep.zip"]:
            path = self.fixtures / name
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            self.launch(self.arguments(name))
            after = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(before, after)
        afterNames = sorted(p.name for p in self.fixtures.iterdir())
        self.assertEqual(beforeNames, afterNames)

    def testVfsLoadErrors(self):
        for name in ["missing.zip", "invalid.zip", "corrupt.zip"]:
            with self.subTest(name=name):
                result = self.launch(self.arguments(name))
                self.assertEqual(result.returncode, 1)
                self.assertIn("VFS loading error:", result.stdout)
                self.assertNotIn("Command:", result.stdout)
                self.assertNotIn("Traceback", result.stderr)

    def testStartupStopsAtEveryCommandError(self):
        scripts = ["startup_error.txt", "startup_bad_ls.txt",
                   "startup_bad_cd.txt", "startup_bad_exit.txt"]
        for script in scripts:
            with self.subTest(script=script):
                result = self.launch(self.arguments(script=script), "exit\n")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("Startup script stopped", result.stdout)
                self.assertNotIn("SHOULD_NOT_RUN", result.stdout)
                self.assertNotIn("cd documents", result.stdout)

    def testMissingStartupFileReturnsToInteractiveMode(self):
        result = self.launch(self.arguments(script="missing.txt"), "exit\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Script reading error:", result.stdout)

    def testInteractiveWithoutScript(self):
        result = self.launch(
            self.arguments(script=None), "\nunknown\nls /\nexit\n"
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("script_path = None", result.stdout)
        self.assertIn("unknown command", result.stdout)
        self.assertIn("Command: ls,", result.stdout)

    def testExitInStartupDoesNotEnterInteractiveMode(self):
        result = self.launch(self.arguments(), "unknown\n")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("unknown command", result.stdout)

    def testCommandLineErrors(self):
        cases = [[], ["--vfs"], ["--vfs", "x", "--script"],
                 ["--vfs", "x", "--unknown"]]
        for arguments in cases:
            with self.subTest(arguments=arguments):
                result = self.launch(arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn("error:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def testHelp(self):
        result = self.launch(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("--vfs", result.stdout)
        self.assertIn("--script", result.stdout)


if __name__ == "__main__":
    unittest.main()
