"""Read Maven dependencies and display their graph or loading order."""

import argparse
import csv
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen
from xml.etree import ElementTree


FIELDS = ("package", "version", "repository", "test_mode")


def read_config(path):
    """Read the two-column CSV configuration."""
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
    """Check required settings and the repository location."""
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


def resolve_value(value, properties):
    """Substitute properties declared in the current POM."""
    for key in properties:
        value = value.replace("${" + key + "}", properties[key])

    if "${" in value:
        raise ValueError(f"Cannot resolve POM property: {value}")

    return value


def get_dependencies(package, version, repository):
    """Download a POM and read its direct dependencies."""
    group_id, artifact_id = package.split(":")
    group_path = group_id.replace(".", "/")
    file_name = f"{artifact_id}-{version}.pom"
    path = f"{group_path}/{artifact_id}/{version}/{file_name}"
    url = repository.rstrip("/") + "/" + path

    with urlopen(url, timeout=10) as response:
        root = ElementTree.fromstring(response.read())

    if root.tag.split("}")[-1] != "project":
        raise ValueError("The repository did not return a Maven POM")

    properties = {
        "project.version": version,
        "pom.version": version,
        "project.groupId": group_id,
        "project.artifactId": artifact_id,
    }

    for item in root.findall("./{*}properties/*"):
        properties[item.tag.split("}")[-1]] = (item.text or "").strip()

    dependencies = []

    for dependency in root.findall("./{*}dependencies/{*}dependency"):
        group = dependency.findtext("{*}groupId", "").strip()
        artifact = dependency.findtext("{*}artifactId", "").strip()
        dependency_version = dependency.findtext("{*}version", "").strip()

        if not group or not artifact or not dependency_version:
            raise ValueError("A dependency has no name or version")

        name = resolve_value(f"{group}:{artifact}", properties)
        dependency_version = resolve_value(dependency_version, properties)
        dependencies.append(f"{name}:{dependency_version}")

    return dependencies


def read_test_repository(path):
    """Read and validate the local dependency graph."""
    with path.open(encoding="utf-8-sig") as file:
        repository = json.load(file)

    if not isinstance(repository, dict):
        raise ValueError("Test repository must be a JSON object")

    for package, dependencies in repository.items():
        if not package.isascii() or not package.isalpha():
            raise ValueError("Test package names must be uppercase letters")

        if not package.isupper():
            raise ValueError("Test package names must be uppercase letters")

        if not isinstance(dependencies, list):
            raise ValueError(f"Dependencies of {package} must be a list")

        for dependency in dependencies:
            if not isinstance(dependency, str) or dependency not in repository:
                raise ValueError(f"Unknown test dependency of {package}")

    return repository


def bfs(level, graph, visited, config, repository):
    """Process one graph level and recursively visit the next."""
    next_level = []

    for package in level:
        if config["test_mode"] == "true":
            if package not in repository:
                raise ValueError(f"Test package not found: {package}")

            dependencies = repository[package]

        else:
            name, version = package.rsplit(":", 1)
            dependencies = get_dependencies(name, version, repository)

        graph[package] = dependencies

        for dependency in dependencies:
            if dependency not in visited:
                visited.add(dependency)
                next_level.append(dependency)

    if next_level:
        bfs(next_level, graph, visited, config, repository)


def build_graph(config, config_path):
    """Build the reachable graph from the selected repository."""
    if config["test_mode"] == "true":
        path = Path(config["repository"])

        if not path.is_absolute():
            path = config_path.parent / path

        repository = read_test_repository(path)
        start = config["package"]

    else:
        repository = config["repository"]
        start = config["package"] + ":" + config["version"]

    graph = {}
    visited = {start}

    bfs([start], graph, visited, config, repository)

    return graph


def print_graph(graph):
    """Print each package and its direct dependencies."""
    print("Dependency graph:")

    for package, dependencies in graph.items():
        if dependencies:
            text = ", ".join(dependencies)
        else:
            text = "(none)"

        print(f"{package} -> {text}")


def loading_order(graph):
    """Place dependencies first, or reject a cyclic graph."""
    order = []
    remaining = list(graph)

    while remaining:
        ready = []

        for package in remaining:
            if all(dependency in order for dependency in graph[package]):
                ready.append(package)

        if not ready:
            raise ValueError("A cycle prevents dependency loading order")

        order.extend(ready)

        for package in ready:
            remaining.remove(package)

    return order


def to_plantuml(graph):
    """Convert graph nodes and edges into PlantUML text."""
    lines = ["@startuml"]
    names = {}

    for number, package in enumerate(graph):
        name = f"P{number}"
        names[package] = name
        lines.append(f'component "{package}" as {name}')

    for package, dependencies in graph.items():
        for dependency in dependencies:
            lines.append(f"{names[package]} --> {names[dependency]}")

    lines.append("@enduml")

    return "\n".join(lines)


def print_result(graph, args):
    """Print the graph in the selected output format."""
    if args.plantuml:
        print(to_plantuml(graph))

    elif args.order:
        order = loading_order(graph)
        print("Loading order:")
        print(" -> ".join(order))

    else:
        print_graph(graph)


def main():
    """Read settings, build the graph, and handle errors."""
    parser = argparse.ArgumentParser(description="Maven dependency graph")
    default_path = Path(__file__).resolve().parents[1] / "config.csv"
    parser.add_argument("--config", type=Path, default=default_path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--order", action="store_true")
    mode.add_argument("--plantuml", action="store_true")
    args = parser.parse_args()

    try:
        config = read_config(args.config)
        validate_config(config, args.config)

    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"Configuration error: {error}")
        return 1

    try:
        graph = build_graph(config, args.config)
        print_result(graph, args)

    except (OSError, ElementTree.ParseError, ValueError) as error:
        print(f"Dependency loading error: {error}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
