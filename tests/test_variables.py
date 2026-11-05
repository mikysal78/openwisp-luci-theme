import json
from pathlib import Path

import pytest

from openwisp_luci_theme.variables import COLOR_RE, FIELDS, build_context

TEMPLATE = Path(__file__).parents[1] / "integration" / "luci-theme-ninux.json"


def test_empty_fields_are_left_out():
    assert build_context({"brand": "", "accent": None, "logo": "", "default_mode": ""}) == {}


def test_values_become_template_variables():
    ctx = build_context(
        {
            "logo": "data:image/svg+xml;base64,AAAA",
            "brand": " Ninux Basilicata ",
            "accent": "#0b5394",
            "accent_dark": "#6fa8dc",
            "default_mode": "advanced",
            "allow_advanced": "0",
        }
    )
    assert ctx == {
        "luci_logo": "data:image/svg+xml;base64,AAAA",
        "luci_brand": "Ninux Basilicata",
        "luci_accent": "#0b5394",
        "luci_accent_dark": "#6fa8dc",
        "luci_mode": "advanced",
        "luci_allow_advanced": "0",
    }


@pytest.mark.parametrize("value", ["#abc", "#AABBCC", "#d93d1c"])
def test_valid_colors(value):
    assert COLOR_RE.match(value)


@pytest.mark.parametrize("value", ["red", "#abcd", "#gggggg", "d93d1c", "#d93d1c;", "#d93d1c}body{"])
def test_invalid_colors(value):
    assert not COLOR_RE.match(value)


def test_variables_match_the_template():
    """Le variabili prodotte sono tutte e sole quelle del template OpenWISP."""
    config = json.loads(TEMPLATE.read_text())["config"]["luci"][0]
    used = {v.strip("{} ") for v in config.values() if isinstance(v, str) and v.startswith("{{")}
    assert used == {variable for _field, variable in FIELDS}
    # nessun default value: vincerebbe sull'impostazione dell'organizzazione
    assert "default_values" not in json.loads(TEMPLATE.read_text())
