"""Create ZIP archives for filesystem and startup tests."""

import argparse
import struct
import zipfile
from pathlib import Path


def write_archive(path, entries):
    """Write the supplied entries to a test ZIP archive."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)


def create_fixtures(output):
    """Create valid and invalid archives for VFS tests."""
    output.mkdir(parents=True, exist_ok=True)
    write_archive(output / "minimal.zip", {})
    write_archive(output / "multiple.zip", {
        "readme.txt": b"Hello from the VFS!\n",
        "empty.txt": b"",
        "binary.bin": bytes(range(256)),
        "empty/": b"",
    })
    write_archive(output / "deep.zip", {
        "documents/course/week1/notes.txt": b"Three directory levels.\n",
        "documents/course/week1/data.bin": b"\x00\xff\x80\x01",
        "documents/course/week1/empty/": b"",
    })
    (output / "invalid.zip").write_bytes(b"This is not a ZIP archive.")
    create_corrupt_archive(output / "corrupt.zip")
    print(f"VFS fixtures created in: {output.resolve()}")


def create_corrupt_archive(path):
    """Create an archive with a damaged file checksum."""
    write_archive(path, {"broken.bin": b"checksum test"})
    data = bytearray(path.read_bytes())
    name_size, extra_size = struct.unpack_from("<HH", data, 26)
    data[30 + name_size + extra_size] ^= 255
    path.write_bytes(data)


def main():
    """Parse arguments and create the requested test archives."""
    parser = argparse.ArgumentParser(description="Create VFS test fixtures")
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    create_fixtures(args.output_dir)


if __name__ == "__main__":
    main()
