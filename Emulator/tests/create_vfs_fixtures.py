import argparse
from pathlib import Path
import struct
import zipfile


def writeArchive(path, entries):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)


def createFixtures(output):
    output.mkdir(parents=True, exist_ok=True)
    writeArchive(output / "minimal.zip", {})
    writeArchive(output / "multiple.zip", {
        "readme.txt": b"Hello from the VFS!\n",
        "empty.txt": b"",
        "binary.bin": bytes(range(256)),
        "empty/": b"",
    })
    writeArchive(output / "deep.zip", {
        "documents/course/week1/notes.txt": b"Three directory levels.\n",
        "documents/course/week1/data.bin": b"\x00\xff\x80\x01",
        "documents/course/week1/empty/": b"",
    })
    (output / "invalid.zip").write_bytes(b"This is not a ZIP archive.")
    createCorruptArchive(output / "corrupt.zip")
    print(f"VFS fixtures created in: {output.resolve()}")


def createCorruptArchive(path):
    writeArchive(path, {"broken.bin": b"checksum test"})
    data = bytearray(path.read_bytes())
    nameSize, extraSize = struct.unpack_from("<HH", data, 26)
    data[30 + nameSize + extraSize] ^= 255
    path.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description="Create VFS test fixtures")
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    createFixtures(args.output_dir)


if __name__ == "__main__":
    main()
