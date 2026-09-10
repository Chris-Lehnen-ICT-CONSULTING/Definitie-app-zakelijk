"""Deterministic, read-only instruction publication for ALG-399."""

from __future__ import annotations

import json
import os
import re
import stat
from pathlib import Path

ENVIRONMENTS = {"codex-app", "codex-cli", "claude-cli", "cowork"}
ALLOWED = {
    "shared": ENVIRONMENTS,
    "claude-only": {"claude-cli", "cowork"},
    "codex-only": {"codex-app", "codex-cli"},
}


def read_regular_bytes(path, *, dir_fd=None) -> bytes:
    """Read an opened regular file without following its final symlink."""
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    descriptor = os.open(path, flags, dir_fd=dir_fd)
    with os.fdopen(descriptor, "rb") as source:
        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
            raise ValueError("Instructiebron is geen regulier bestand")
        return source.read()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Dubbele JSON-sleutel: {key}")
        result[key] = value
    return result


def _fields(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError(f"Ongeldige velden in {label}")


def _identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", value):
        raise ValueError(f"Ongeldige instructie-ID: {value!r}")


def _mapping(value, label):
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{label} moet een niet-lege mapping zijn")
    for key in value:
        _identifier(key)


def _references(value, known, label, *, allow_empty=False):
    if not isinstance(value, list) or (not value and not allow_empty):
        raise ValueError(f"{label} moet een expliciete lijst zijn")
    seen = set()
    for ref in value:
        _identifier(ref)
        if ref not in known or ref in seen:
            raise ValueError(f"Onbekende of dubbele verwijzing in {label}: {ref}")
        seen.add(ref)
    return seen


def _load_sources(parent: Path, blocks: dict) -> dict[str, str]:
    for name, block in blocks.items():
        _fields(block, {"disposition", "required_in"}, name)
        if block["disposition"] not in ALLOWED:
            raise ValueError(f"Niet-geclassificeerd blok: {name}")
    descriptor = os.open(
        parent / "blocks", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    )
    try:
        if set(os.listdir(descriptor)) != {name + ".md" for name in blocks}:
            raise ValueError(
                "Bronlijst wijkt af: onbekende of ontbrekende blokbestanden"
            )
        texts = {}
        for name in blocks:
            raw = read_regular_bytes(name + ".md", dir_fd=descriptor)
            text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
            if not text.strip():
                raise ValueError(f"Leeg instructieblok: {name}")
            texts[name] = text.rstrip("\n")
        return texts
    finally:
        os.close(descriptor)


def _assemble(publications, blocks, texts):
    result = {}
    used = set()
    for name, publication in publications.items():
        _fields(publication, {"environment", "blocks"}, name)
        environment = publication["environment"]
        if environment not in ENVIRONMENTS:
            raise ValueError(f"Onbekende omgeving: {environment}")
        selected = _references(publication["blocks"], blocks, name)
        for ref in selected:
            if environment not in ALLOWED[blocks[ref]["disposition"]]:
                raise ValueError(f"Verkeerde clientdispositie in {name}: {ref}")
        used.update(selected)
        result[name] = "\n\n".join(texts[ref] for ref in publication["blocks"]) + "\n"
    for ref, block in blocks.items():
        targets = _references(
            block["required_in"], publications, ref + ".required_in", allow_empty=True
        )
        for target in targets:
            if ref not in publications[target]["blocks"]:
                raise ValueError(f"Verplichte instructie ontbreekt in {target}: {ref}")
    if used != set(blocks):
        raise ValueError("Een gedeclareerd instructieblok is nergens gepubliceerd")
    return result


def _check_chains(chains, publications, rendered):
    used = set()
    for name, chain in chains.items():
        _fields(chain, {"publications", "max_bytes"}, name)
        refs = _references(chain["publications"], publications, name)
        if len({publications[ref]["environment"] for ref in refs}) != 1:
            raise ValueError(
                f"Instructieketen combineert verschillende omgevingen: {name}"
            )
        limit = chain["max_bytes"]
        if type(limit) is not int or limit < 1:
            raise ValueError(f"Ongeldig bytebudget in {name}")
        size = len(
            "\n".join(rendered[ref] for ref in chain["publications"]).encode("utf-8")
        )
        if size > limit:
            raise ValueError(
                f"Instructiebudget overschreden in {name}: {size} > {limit}"
            )
        used.update(refs)
    if used != set(publications):
        raise ValueError("Een publicatie heeft geen expliciet ketenbudget")


def load_publications(manifest_path: Path) -> dict[str, str]:
    """Validate all sources and intended chains before returning any output."""
    manifest = json.loads(
        read_regular_bytes(manifest_path).decode("utf-8"),
        object_pairs_hook=_unique_object,
    )
    _fields(manifest, {"version", "blocks", "publications", "chains"}, "manifest")
    if type(manifest["version"]) is not int or manifest["version"] != 1:
        raise ValueError("Onbekende manifestversie")
    for key in ("blocks", "publications", "chains"):
        _mapping(manifest[key], key)
    texts = _load_sources(manifest_path.parent, manifest["blocks"])
    rendered = _assemble(manifest["publications"], manifest["blocks"], texts)
    _check_chains(manifest["chains"], manifest["publications"], rendered)
    return rendered
