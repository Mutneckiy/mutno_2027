from copy import deepcopy
from xml.etree import ElementTree as ET

import pytest

from app_final import Profile, personalize, render_svg


BASE = {
    "full_name": "Анна", "birth_date": "1990-02-10", "wish": "Открыть мастерскую",
    "answers": {"direction": 0, "change": 1, "resource": 2, "element": 3, "step": 0},
}


def art(data):
    return personalize(Profile(**data))["talisman"]


@pytest.mark.parametrize("field", ["full_name", "birth_date", "wish", "direction", "change", "resource", "element", "step"])
def test_every_input_changes_visible_geometry(field):
    changed = deepcopy(BASE)
    replacements = {"full_name": "Мария", "birth_date": "1990-02-11", "wish": "Изучить музыку"}
    if field in replacements:
        changed[field] = replacements[field]
    else:
        changed["answers"][field] = (changed["answers"][field] + 1) % 4
    first, second = ET.fromstring(render_svg(art(BASE))), ET.fromstring(render_svg(art(changed)))
    # Compare actual drawing, not just title, explanation or fingerprint metadata.
    def geometry(root):
        return [node.attrib for node in root.iter() if node.tag.split('}')[-1] in {"path", "circle", "polyline"}]
    assert geometry(first) != geometry(second)


def test_stable_art_and_symbolic_mapping():
    result = personalize(Profile(**BASE))
    drawing = result["talisman"]["art"]
    assert drawing["petals"] == result["symbolic_profile"]["numerology"]["life_path"] + 3
    assert drawing["rings"] == 4
    assert drawing["rays"] == 8
    assert render_svg(result["talisman"]) == render_svg(art(deepcopy(BASE)))


def test_svg_is_passive_and_contains_no_raw_questionnaire():
    data = deepcopy(BASE)
    data["full_name"] = '<script>alert("name")</script>'
    data["wish"] = '<image href="https://example.invalid/track" />'
    svg = render_svg(art(data))
    root = ET.fromstring(svg)
    allowed = {"svg", "title", "desc", "defs", "radialGradient", "linearGradient", "stop", "rect", "g", "circle", "path", "polyline", "text"}
    assert all(node.tag.split('}')[-1] in allowed for node in root.iter())
    assert all(not key.startswith('on') and 'href' not in key for node in root.iter() for key in node.attrib)
    assert data["full_name"] not in svg
    assert data["birth_date"] not in svg
    assert data["wish"] not in svg
