import argparse
import csv
from pathlib import Path
from urllib.parse import urlsplit


FIELDS = ("package", "version", "repository", "test_mode")


def read_config(path):
    config = {}

    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file, strict=True)
        header = next(reader, None)

        if header != ["key", "value"]:
            raise ValueError("CSV header must be: key,value")

        for row in reader:
            if not row:
                continue

            if len(row) != 2:
                raise ValueError(
                    f"CSV line {reader.line_num} must contain two columns"
                )

            key = row[0].strip()
            value = row[1].strip()
            config[key] = value

    return config


def validate_config(config, config_path):
    for key in FIELDS:
        if key not in config or not config[key]:
            raise ValueError(f"Setting is missing or empty: {key}")

    if config["test_mode"] not in ("true", "false"):
        raise ValueError("test_mode must be true or false")

    if config["test_mode"] == "true":
        path = Path(config["repository"])

        if not path.is_absolute():
            path = config_path.parent / path

        if not path.is_file():
            raise ValueError(f"Test repository file not found: {path}")

    else:
        url = urlsplit(config["repository"])

        if not url.scheme or not url.hostname:
            raise ValueError("Repository must be a URL")


def main():
    parser = argparse.ArgumentParser(description="Maven dependency graph")
    default_path = Path(__file__).resolve().parents[1] / "config.csv"
    parser.add_argument("--config", type=Path, default=default_path)
    args = parser.parse_args()

    try:
        config = read_config(args.config)
        validate_config(config, args.config)

    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"Configuration error: {error}")
        return 1

    for key in FIELDS:
        print(f"{key} = {config[key]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
