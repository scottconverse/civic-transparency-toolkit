"""
Configuration management for Civic Transparency Toolkit.
Handles persistent settings: API key, city config, sources, and preferences.
"""

import copy
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def _log_debug(message):
    """Append a timestamped debug message to debug.log next to config.json."""
    try:
        log_path = get_config_path().parent / "debug.log"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {message}\n")
    except Exception:
        pass  # Never crash on logging


DEFAULT_CONFIG = {
    "api_key": "",
    "model": "claude-haiku-4-5-20251001",
    "research_model": "",  # Cheaper model for web-search-heavy prompts (1, 3, 9). Blank = use main model.
    "city_name": "",
    "state": "",
    "state_open_records_law": "",
    "city_clerk_contact": "",
    "sources": {
        "city_agenda_portal_url": "",
        "city_news_url": "",
        "school_district_name": "",
        "school_district_url": "",
        "transit_agency_name": "",
        "transit_agency_url": "",
        "county_name": "",
        "county_gov_url": "",
        "state_gov_url": "",
        "local_media_outlet": "",
        "local_media_url": "",
        "youtube_channel_url": "",
    },
    "meeting_schedule": {
        "council_day": "",
        "council_time": "",
        "council_location": "",
        "school_board_day": "",
        "school_board_time": "",
        "county_commissioners_day": "",
        "county_commissioners_time": "",
        "planning_commission_day": "",
        "planning_commission_time": "",
    },
    "additional_sources": [],  # User-imported list of {name, url, tier, category}
    "last_lane": "daily_production",
    "step_by_step": False,
    "output_directory": "",
}


def get_config_path():
    """Return the path to the config file, next to the executable or script."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent
    return base / "config.json"


def load_config():
    """Load config from disk, merging with defaults for any missing keys."""
    config_path = get_config_path()
    config = copy.deepcopy(DEFAULT_CONFIG)

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            if not isinstance(saved, dict):
                saved = {}  # Corrupted — fall back to defaults
            # Deep merge: update top-level, and nested dicts
            for key, value in saved.items():
                if key in config and isinstance(config[key], dict):
                    if isinstance(value, dict):
                        config[key].update(value)
                    # else: saved has wrong type for this key — keep default
                elif key in config and isinstance(config[key], list):
                    if isinstance(value, list):
                        config[key] = value
                    # else: wrong type — keep default
                else:
                    config[key] = value
        except (json.JSONDecodeError, IOError, TypeError):
            pass  # Fall back to defaults

    return config


def save_config(config):
    """Save config to disk. Internal state keys (prefixed with _) are excluded."""
    config_path = get_config_path()
    try:
        # Strip internal UI state keys (e.g. _seen_api_info) from persisted config
        clean = {k: v for k, v in config.items() if not k.startswith("_")}
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(clean, f, indent=2, ensure_ascii=False)
        _log_debug(f"save_config: wrote to {config_path}")
        _log_debug(f"save_config: state='{config.get('state', '')}' "
                   f"records_law='{config.get('state_open_records_law', '')}' "
                   f"clerk='{config.get('city_clerk_contact', '')}' "
                   f"youtube='{config.get('sources', {}).get('youtube_channel_url', '')}'")
    except IOError as e:
        _log_debug(f"save_config: FAILED — {e}")
        print(f"Warning: Could not save config: {e}")


def import_sources_from_file(filepath):
    """
    Parse a text file of sources. Supported formats:

    Simple (one URL per line):
        https://example.gov/agendas
        https://example.gov/news

    Labeled (name: URL):
        City Agenda Portal: https://example.gov/agendas
        City News Page: https://example.gov/news

    CSV-style (name, url, type, category):
        City Agenda Portal, https://example.gov/agendas, A, Government
        School District, https://example.edu/news, B, Education
        Local Paper, https://localnews.com/, News, Journalism

    Type field accepts: A/B/C or Official Record/News/Community (case-insensitive).

    Returns a list of dicts: [{name, url, tier, category}]
    """
    # Human-readable labels → internal A/B/C codes
    _type_to_code = {
        "a": "A", "b": "B", "c": "C",
        "official record": "A", "official": "A",
        "news": "B", "news reporting": "B", "journalism": "B",
        "community": "C", "community source": "C",
    }

    sources = []
    metadata = {}  # Parsed from "# key: value" comment lines
    # utf-8-sig handles Windows BOM (\xef\xbb\xbf) transparently

    # Flexible label → metadata key mapping
    # Accepts many natural variations of field names
    _meta_aliases = {
        "city": "city", "city_name": "city", "city name": "city",
        "state": "state",
        "state_open_records_law": "state_open_records_law",
        "state open records law": "state_open_records_law",
        "open_records_law": "state_open_records_law",
        "open records law": "state_open_records_law",
        "records_law": "state_open_records_law",
        "records law": "state_open_records_law",
        "foia_law": "state_open_records_law",
        "foia law": "state_open_records_law",
        "city_clerk_contact": "city_clerk_contact",
        "city clerk contact": "city_clerk_contact",
        "city_clerk": "city_clerk_contact",
        "city clerk": "city_clerk_contact",
        "clerk_contact": "city_clerk_contact",
        "clerk contact": "city_clerk_contact",
        "clerk_email": "city_clerk_contact",
        "clerk email": "city_clerk_contact",
        "clerk": "city_clerk_contact",
    }

    with open(filepath, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                # Parse metadata from comments like "# city: YourCity"
                meta_line = line.lstrip("#").strip()
                if ": " in meta_line and not meta_line.startswith(("Tier", "Type", "Format")):
                    key, val = meta_line.split(": ", 1)
                    key_normalized = key.strip().lower().replace("_", " ").replace("-", " ")
                    key_normalized_under = key_normalized.replace(" ", "_")
                    # Check both "open records law" and "open_records_law" forms
                    meta_key = (_meta_aliases.get(key_normalized)
                                or _meta_aliases.get(key_normalized_under))
                    if meta_key:
                        metadata[meta_key] = val.strip()
                continue

            # CSV-style: 4 comma-separated fields
            if line.count(",") >= 3:
                parts = [p.strip() for p in line.split(",", 3)]
                raw_type = parts[2].lower() if len(parts) > 2 else "b"
                tier_code = _type_to_code.get(raw_type, "B")
                sources.append({
                    "name": parts[0],
                    "url": parts[1],
                    "tier": tier_code,
                    "category": parts[3] if len(parts) > 3 else "General",
                })
            # Labeled: "Name: URL"
            elif ": http" in line:
                name, url = line.split(": ", 1)
                sources.append({
                    "name": name.strip(),
                    "url": url.strip(),
                    "tier": "B",
                    "category": "General",
                })
            # Simple: just a URL — derive a name from the domain
            elif line.startswith("http"):
                try:
                    domain = line.split("//", 1)[1].split("/", 1)[0]
                    domain = domain.replace("www.", "")
                    auto_name = domain.split(".")[0].title()
                except (IndexError, ValueError):
                    auto_name = ""
                sources.append({
                    "name": auto_name,
                    "url": line,
                    "tier": "B",
                    "category": "General",
                })

    _log_debug(f"import_sources_from_file: parsed {len(sources)} sources from {filepath}")
    _log_debug(f"import_sources_from_file: metadata = {metadata}")
    return sources, metadata


def auto_populate_config_from_sources(config, sources, metadata=None):
    """
    Scan imported sources and fill in blank City Configuration fields
    so users don't have to enter the same data twice.

    Only fills fields that are currently empty — never overwrites
    values the user has already set.
    """
    if metadata is None:
        metadata = {}

    _log_debug(f"auto_populate: received metadata keys: {list(metadata.keys())}")
    _log_debug(f"auto_populate: received {len(sources)} sources")

    # Apply metadata from file comments (city, state, etc.)
    # These always overwrite on re-import — the source file is the authority.
    for meta_key, config_key in [("city", "city_name"), ("state", "state"),
                                  ("state_open_records_law", "state_open_records_law"),
                                  ("city_clerk_contact", "city_clerk_contact")]:
        val = metadata.get(meta_key)
        if val:
            old = config.get(config_key, "")
            config[config_key] = val
            _log_debug(f"auto_populate: config['{config_key}'] = '{val}' (was '{old}')")
        else:
            _log_debug(f"auto_populate: metadata['{meta_key}'] is empty, skipping")

    if "sources" not in config:
        config["sources"] = {}

    cfg = config["sources"]

    # Mapping: (name keyword, url keyword) -> config field
    # Checked in order; first match wins for each field
    field_rules = {
        "city_agenda_portal_url": [
            (["primegov", "agenda", "legistar", "granicus"], []),
        ],
        "city_news_url": [
            (["news"], ["/news"]),
        ],
        "school_district_name": "name_only",  # special: grab name, not URL
        "school_district_url": [
            (["school district"], ["svvsd", ".edu", "school"]),
        ],
        "transit_agency_name": "name_only",
        "transit_agency_url": [
            (["transit", "rtd", "transportation district"], ["rtd", "transit"]),
        ],
        "county_name": "name_only",
        "county_gov_url": [
            (["county government", "county"], ["county"]),
        ],
        "state_gov_url": [
            (["state government", "state portal"], ["state.co", "co.colorado"]),
        ],
        "local_media_outlet": "name_only",
        "local_media_url": [
            ([], []),  # matched via category below
        ],
        "youtube_channel_url": [
            (["youtube"], ["youtube.com"]),
        ],
    }

    # Category-based fallbacks
    category_map = {
        "Journalism": ("local_media_url", "local_media_outlet"),
        "Education": ("school_district_url", "school_district_name"),
    }

    # Track which fields have been matched during THIS import
    # (first match from the source file wins, but re-imports overwrite old values)
    matched_this_import = set()

    for source in sources:
        name_lower = source.get("name", "").lower()
        url = source.get("url", "")
        url_lower = url.lower()
        category = source.get("category", "")

        for field, rules in field_rules.items():
            # Skip fields already matched during this import (first match wins)
            if field in matched_this_import:
                continue

            if rules == "name_only":
                continue  # handled alongside URL fields below

            for name_keywords, url_keywords in rules:
                name_match = any(kw in name_lower for kw in name_keywords) if name_keywords else False
                url_match = any(kw in url_lower for kw in url_keywords) if url_keywords else False

                if name_match or url_match:
                    cfg[field] = url
                    matched_this_import.add(field)

                    # Also fill the paired name field
                    # Some URL fields don't follow the simple _url → _name pattern
                    name_field_overrides = {
                        "county_gov_url": "county_name",
                        "local_media_url": "local_media_outlet",
                    }
                    name_field = name_field_overrides.get(field, field.replace("_url", "_name"))
                    if name_field in cfg:
                        src_name = source.get("name", "")
                        # Clean up county names: "Boulder County Government" → "Boulder County"
                        if name_field == "county_name" and src_name:
                            src_name = re.sub(
                                r'\s+(?:government|gov|commission(?:ers)?|admin(?:istration)?)\s*$',
                                '', src_name, flags=re.IGNORECASE).strip()
                        cfg[name_field] = src_name
                        matched_this_import.add(name_field)
                    break

        # Category-based matching for fields not yet matched this import
        if category in category_map:
            url_field, name_field = category_map[category]
            if url_field not in matched_this_import:
                cfg[url_field] = url
                matched_this_import.add(url_field)
            if name_field in cfg and name_field not in matched_this_import:
                cfg[name_field] = source.get("name", "")
                matched_this_import.add(name_field)

    _log_debug(f"auto_populate: matched fields this import: {matched_this_import}")
    _log_debug(f"auto_populate: youtube_channel_url = '{cfg.get('youtube_channel_url', '')}'")

    # Try to infer city_name and state from source names if still blank
    if not config.get("city_name"):
        # Common suffixes that are NOT part of the city name
        _stop_words = (
            r'\s+(?:official|website|news|portal|youtube|page|government|'
            r'gov|clerk|planning|water|library|public|department|dept)\b'
        )
        for source in sources:
            name = source.get("name", "")
            # Look for "City of X Y Z <suffix>" pattern
            if "city of " in name.lower():
                # Split at "ity of " to preserve original casing
                after = name.split("ity of ", 1)[1]
                # Take words up to the first common non-city suffix
                city = re.split(_stop_words, after, maxsplit=1,
                                 flags=re.IGNORECASE)[0].strip().rstrip(" -—,")
                if city:
                    config["city_name"] = city
                    break

    # Final state logging for the 4 key fields
    _log_debug(f"auto_populate FINAL: city_name='{config.get('city_name', '')}' "
               f"state='{config.get('state', '')}' "
               f"records_law='{config.get('state_open_records_law', '')}' "
               f"clerk='{config.get('city_clerk_contact', '')}' "
               f"youtube='{config.get('sources', {}).get('youtube_channel_url', '')}'")
    return config
