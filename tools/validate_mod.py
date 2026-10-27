#!/usr/bin/env python3
"""Validate mod data and that selectable faction technologies are discoverable."""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "tolkien"
DATA = MOD / "simulation" / "data"
TEMPLATES = MOD / "simulation" / "templates"


def load_json(path: Path, errors: list[str]) -> Any:
    try:
        with path.open(encoding="utf-8-sig") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"{path.relative_to(ROOT)}: {error}")
        return None


def validate_mod_files(errors: list[str]) -> None:
    for path in sorted(MOD.rglob("*.json")):
        load_json(path, errors)

    for path in sorted(MOD.rglob("*.xml")):
        try:
            ET.parse(path)
        except (OSError, ET.ParseError) as error:
            errors.append(f"{path.relative_to(ROOT)}: {error}")


def collect_technologies(errors: list[str]) -> dict[str, tuple[Path, dict[str, Any]]]:
    technologies: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in sorted((DATA / "technologies").rglob("*.json")):
        data = load_json(path, errors)
        if not isinstance(data, dict):
            continue
        name = data.get("genericName")
        if not isinstance(name, str) or not name.strip():
            continue
        if name in technologies:
            errors.append(
                f"{path.relative_to(ROOT)}: duplicate technology name {name!r}"
            )
        technologies[name] = (path, data)
    return technologies


def collect_researchable_techs() -> dict[str, set[str]]:
    tech_ids: dict[str, set[str]] = {}
    for path in sorted(TEMPLATES.rglob("*.xml")):
        relative = path.relative_to(TEMPLATES)
        if len(relative.parts) < 3 or relative.parts[0] != "structures":
            continue
        civ = relative.parts[1]
        try:
            root = ET.parse(path).getroot()
        except (OSError, ET.ParseError):
            continue
        for node in root.findall("./Researcher/Technologies"):
            tech_ids.setdefault(civ, set()).update((node.text or "").split())
    return tech_ids


def collect_structure_names(civ: str) -> set[str]:
    names: set[str] = set()
    for path in sorted((TEMPLATES / "structures" / civ).glob("*.xml")):
        try:
            root = ET.parse(path).getroot()
        except (OSError, ET.ParseError):
            continue
        identity = root.find("./Identity")
        if identity is None:
            continue
        for field in ("GenericName", "SpecificName"):
            value = identity.findtext(field)
            if value and value.strip():
                names.add(value.strip())
    return names


def validate_civilizations(errors: list[str]) -> None:
    technologies = collect_technologies(errors)
    researchable = collect_researchable_techs()
    civ_dir = DATA / "civs"
    faction_count = 0

    for path in sorted(civ_dir.glob("*.json")):
        civ_data = load_json(path, errors)
        if not isinstance(civ_data, dict):
            continue
        factions = civ_data.get("Factions")
        if not isinstance(factions, list) or not factions:
            continue
        civ = str(civ_data.get("Code", path.stem)).lower()
        faction_count += 1
        if civ_data.get("SelectableInGameSetup") is not True:
            errors.append(
                f"{path.relative_to(ROOT)}: faction catalog civ must be selectable"
            )
        bonuses = civ_data.get("CivBonuses")
        if not isinstance(bonuses, list) or not bonuses:
            errors.append(f"{path.relative_to(ROOT)}: CivBonuses must be a non-empty list")
            bonuses = []
        for bonus in bonuses:
            if not isinstance(bonus, dict):
                errors.append(f"{path.relative_to(ROOT)}: CivBonuses entries must be objects")
                continue
            for field in ("Name", "History", "Description"):
                if not isinstance(bonus.get(field), str) or not bonus[field].strip():
                    errors.append(
                        f"{path.relative_to(ROOT)}: civ bonus is missing {field}"
                    )

        for faction in factions:
            if not isinstance(faction, dict):
                errors.append(f"{path.relative_to(ROOT)}: Factions entries must be objects")
                continue
            for field in ("Name", "Description"):
                if not isinstance(faction.get(field), str) or not faction[field].strip():
                    errors.append(
                        f"{path.relative_to(ROOT)}: faction entry is missing {field}"
                    )

            catalog_names: set[str] = set()
            catalog = faction.get("Technologies", [])
            if not isinstance(catalog, list):
                errors.append(f"{path.relative_to(ROOT)}: Technologies must be a list")
                catalog = []
            for entry in catalog:
                if not isinstance(entry, dict):
                    errors.append(f"{path.relative_to(ROOT)}: technology entry must be an object")
                    continue
                name = entry.get("Name")
                if not isinstance(name, str) or not name.strip():
                    errors.append(f"{path.relative_to(ROOT)}: technology entry is missing Name")
                    continue
                catalog_names.add(name)
                for field in ("History", "Description"):
                    if not isinstance(entry.get(field), str) or not entry[field].strip():
                        errors.append(
                            f"{path.relative_to(ROOT)}: technology {name!r} is missing {field}"
                        )
                technology = technologies.get(name)
                if technology is None:
                    errors.append(
                        f"{path.relative_to(ROOT)}: no technology JSON matches {name!r}"
                    )
                    continue
                tech_path, tech_data = technology
                if not tech_path.stem.startswith(f"{civ}_"):
                    errors.append(
                        f"{path.relative_to(ROOT)}: {name!r} resolves to "
                        f"{tech_path.relative_to(ROOT)}, not a {civ} technology"
                    )
                if tech_path.stem not in researchable.get(civ, set()):
                    errors.append(
                        f"{tech_path.relative_to(ROOT)}: not reachable from any "
                        f"{civ} structure Researcher/Technologies list"
                    )
                if not isinstance(tech_data.get("tooltip"), str) or not tech_data["tooltip"].strip():
                    errors.append(
                        f"{tech_path.relative_to(ROOT)}: missing player-facing tooltip"
                    )

            if len(catalog_names) != len(catalog):
                errors.append(
                    f"{path.relative_to(ROOT)}: duplicate technology names in faction catalog"
                )
            actual_ids = {
                tech_path.stem
                for tech_path in (DATA / "technologies").glob(f"{civ}_*.json")
            }
            listed_ids = {
                technologies[name][0].stem
                for name in catalog_names
                if name in technologies
            }
            if actual_ids != listed_ids:
                missing = sorted(actual_ids - listed_ids)
                stale = sorted(listed_ids - actual_ids)
                if missing:
                    errors.append(
                        f"{path.relative_to(ROOT)}: faction catalog omits technologies: "
                        + ", ".join(missing)
                    )
                if stale:
                    errors.append(
                        f"{path.relative_to(ROOT)}: faction catalog has invalid technologies: "
                        + ", ".join(stale)
                    )

            structures = faction.get("Structures", [])
            if not isinstance(structures, list):
                errors.append(f"{path.relative_to(ROOT)}: Structures must be a list")
                structures = []
            structure_names = collect_structure_names(civ)
            for entry in structures:
                if not isinstance(entry, dict):
                    errors.append(f"{path.relative_to(ROOT)}: structure entry must be an object")
                    continue
                name = entry.get("Name")
                if not isinstance(name, str) or not name.strip():
                    errors.append(f"{path.relative_to(ROOT)}: structure entry is missing Name")
                    continue
                for field in ("History", "Description"):
                    if not isinstance(entry.get(field), str) or not entry[field].strip():
                        errors.append(
                            f"{path.relative_to(ROOT)}: structure {name!r} is missing {field}"
                        )
                if name not in structure_names:
                    errors.append(
                        f"{path.relative_to(ROOT)}: structure {name!r} does not match "
                        f"a {civ} structure template name"
                    )

    if not faction_count:
        errors.append("No faction catalogs found in simulation/data/civs")


def main() -> int:
    errors: list[str] = []
    if not (MOD / "mod.json").is_file():
        errors.append("tolkien/mod.json is missing")
    validate_mod_files(errors)
    validate_civilizations(errors)

    if errors:
        print(f"Validation failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Validated JSON/XML and faction technology/structure catalogs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
