# /// script
# requires-python = ">=3.13"
# dependencies = ["packaging>=24.0"]
# ///
"""Check a uv project or workspace against the python-dependency-management skill's rules.

1. Version rule: every versioned requirement (project dependencies, extras, and
   dependency groups) uses a single ">=" lower bound.
2. Subset rule (workspaces only): every member's [project] dependencies are also
   declared in the workspace root's [project] dependencies, with the same
   specifier.

Also prints notes, which don't fail the check, for root dependencies whose
floor is below the version in uv.lock.

Usage: uv run --script check_deps.py [PROJECT_OR_WORKSPACE_ROOT]
Exits 1 if any rule is violated.
"""

import sys
import tomllib
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version


def load(path):
    with path.open("rb") as f:
        return tomllib.load(f)


def member_dirs(root, workspace):
    excluded = {p.resolve() for pattern in workspace.get("exclude", []) for p in root.glob(pattern)}
    dirs = []
    for pattern in workspace.get("members", []):
        for path in sorted(root.glob(pattern)):
            resolved = path.resolve()
            if resolved == root.resolve() or resolved in excluded:
                continue
            if (path / "pyproject.toml").is_file():
                dirs.append(path)
    return dirs


def non_index_sources(doc):
    """Names sourced from git, a path, a URL, or the workspace; these carry no version."""
    sources = doc.get("tool", {}).get("uv", {}).get("sources", {})
    names = set()
    for name, source in sources.items():
        entries = source if isinstance(source, list) else [source]
        if any(key in entry for entry in entries for key in ("git", "path", "url", "workspace")):
            names.add(canonicalize_name(name))
    return names


def requirement_lists(doc):
    project = doc.get("project", {})
    yield "project.dependencies", project.get("dependencies", [])
    for extra, reqs in project.get("optional-dependencies", {}).items():
        yield f"project.optional-dependencies.{extra}", reqs
    for group, reqs in doc.get("dependency-groups", {}).items():
        # Skip {include-group = "..."} tables.
        yield f"dependency-groups.{group}", [r for r in reqs if isinstance(r, str)]


def parse(raw, where, errors):
    try:
        return Requirement(raw)
    except InvalidRequirement as exc:
        errors.append(f"{where}: cannot parse {raw!r}: {exc}")
        return None


def check_versions(label, doc, unversioned, errors):
    for section, reqs in requirement_lists(doc):
        for raw in reqs:
            req = parse(raw, f"{label} {section}", errors)
            if req is None or req.url or canonicalize_name(req.name) in unversioned:
                continue
            specs = list(req.specifier)
            if len(specs) != 1 or specs[0].operator != ">=":
                errors.append(
                    f"{label} {section}: {raw!r} must use a single '>=<tested version>' bound"
                )


def project_deps(label, doc, errors):
    deps = {}
    for raw in doc.get("project", {}).get("dependencies", []):
        req = parse(raw, f"{label} project.dependencies", errors)
        if req is not None:
            deps[canonicalize_name(req.name)] = req
    return deps


def locked_versions(root):
    lock = root / "uv.lock"
    if not lock.is_file():
        return {}
    versions = {}
    for package in load(lock).get("package", []):
        try:
            version = Version(package["version"])
        except (KeyError, InvalidVersion):
            continue
        versions.setdefault(canonicalize_name(package["name"]), []).append(version)
    return versions


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        sys.exit(f"No pyproject.toml in {root}")

    errors, notes = [], []
    root_doc = load(pyproject)
    workspace = root_doc.get("tool", {}).get("uv", {}).get("workspace")
    members = [(path, load(path / "pyproject.toml")) for path in member_dirs(root, workspace or {})]

    member_names = {
        canonicalize_name(doc["project"]["name"]) for _, doc in members if "name" in doc.get("project", {})
    }
    if "name" in root_doc.get("project", {}):
        member_names.add(canonicalize_name(root_doc["project"]["name"]))

    check_versions("root", root_doc, non_index_sources(root_doc) | member_names, errors)
    for path, doc in members:
        check_versions(str(path.relative_to(root)), doc, non_index_sources(doc) | member_names, errors)

    root_deps = project_deps("root", root_doc, errors)
    if workspace is not None and "project" not in root_doc:
        errors.append(
            "root: workspace root has no [project] table, so there are no workspace "
            "dependencies for members to be a subset of"
        )
    elif workspace is not None:
        for path, doc in members:
            unversioned = non_index_sources(doc) | member_names
            for name, req in project_deps(str(path.relative_to(root)), doc, errors).items():
                if name in unversioned:
                    continue
                if name not in root_deps:
                    errors.append(f"{path.relative_to(root)}: {req.name} is not declared in the root [project] dependencies")
                elif req.specifier != root_deps[name].specifier:
                    errors.append(
                        f"{path.relative_to(root)}: {req.name}{req.specifier} differs from root "
                        f"{root_deps[name].name}{root_deps[name].specifier}"
                    )

    locked = locked_versions(root)
    for name, req in root_deps.items():
        specs = list(req.specifier)
        if len(specs) != 1 or specs[0].operator != ">=" or name not in locked:
            continue
        floor, newest = Version(specs[0].version), max(locked[name])
        if floor < newest:
            notes.append(f"root: {req.name} floor {floor} is below locked {newest}")

    for note in notes:
        print(f"note: {note}")
    for error in errors:
        print(f"error: {error}")
    if errors:
        sys.exit(1)
    print("ok: dependency rules pass")


if __name__ == "__main__":
    main()
