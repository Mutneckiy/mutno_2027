"""Deterministic personal vector art; no image model or external requests."""

from hashlib import sha256
from html import escape
import json
from math import cos, sin, pi

from symbolism import WESTERN, ANIMALS, ELEMENTS


def personalize_art(talisman, profile, context):
    fingerprint = sha256(json.dumps(profile.model_dump(mode="json"), ensure_ascii=False,
                                    sort_keys=True).encode()).hexdigest()
    numbers = context["numerology"]
    answers = profile.answers
    talisman["art"] = {
        "version": 4, "fingerprint": fingerprint,
        "petals": numbers["life_path"] + 3,
        "rings": answers["resource"] + 2,
        "rays": 8 + answers["step"] * 4,
        "flow": answers["change"],
        "zodiac": [entry[1] for entry in WESTERN].index(context["western"]["sign"]),
        "animal": ANIMALS.index(context["chinese"]["animal"]),
        "element": ELEMENTS.index(context["chinese"]["element"]),
        "name_number": numbers["name_number"],
        "year_number": numbers["personal_year"],
    }
    talisman["meaning"] += (
        f" В орнаменте {numbers['life_path'] + 3} лепестков по числу пути; "
        f"{answers['resource'] + 2} кольца отражают выбранный источник сил. "
        f"Метки на внешнем круге — {context['western']['sign']} и "
        f"{context['chinese']['animal']}. Цвет задаёт выбранная стихия, "
        "а рисунок звёзд складывается из всей анкеты, включая имя и желание."
    )
    return talisman


def point(radius, angle):
    radians = angle * pi / 180
    return f"{256 + radius * cos(radians):.2f},{256 + radius * sin(radians):.2f}"


def render_svg(talisman):
    art = talisman["art"]
    digest = bytes.fromhex(art["fingerprint"])
    tones = {"#c7a8ff": "#374134", "#ffd399": "#164747", "#9dcfff": "#30344e", "#9fe1c4": "#653324"}
    background = tones.get(talisman["primary"], "#164747")
    a, b = "#e6be77", "#b88849"
    zodiac = WESTERN[art["zodiac"]][1].upper()
    ornaments = []
    for i in range(art["petals"]):
        angle = i * 360 / art["petals"] + digest[0] % 30
        width = 22 + art["flow"] * 9
        ornaments.append(f'<path transform="rotate({angle:.2f} 256 256)" d="M256 217 Q{256-width} 150 256 105 Q{256+width} 150 256 217Z"/>')
    for i in range(art["rings"]):
        ornaments.append(f'<circle cx="256" cy="256" r="{156+i*9}" opacity="{.25+i*.1:.2f}"/>')
    for i in range(art["rays"]):
        ornaments.append(f'<path transform="rotate({i*360/art["rays"]:.2f} 256 256)" d="M256 45V{55+art["element"]*3}"/>')
    # A fictional constellation, not a claim to depict the astronomical sky.
    points = [point(100 + digest[i] % 45, digest[i+8] * 360 / 256) for i in range(7)]
    constellation = '<polyline points="' + ' '.join(points) + '" fill="none" opacity=".45"/>'
    for i, p in enumerate(points):
        x, y = p.split(',')
        constellation += f'<circle cx="{x}" cy="{y}" r="{2+digest[i+16]%3}"/>'
    centers = {
        "star": '<path d="M256 209 268 244 303 256 268 268 256 303 244 268 209 256 244 244Z"/>',
        "sun": '<circle cx="256" cy="256" r="30"/><circle cx="256" cy="256" r="43" stroke-dasharray="2 8"/>',
        "compass": '<path d="M256 207 276 256 256 305 236 256ZM207 256H305"/>',
        "seed": '<path d="M256 301V242M256 269Q214 267 218 228Q256 226 256 269ZM256 248Q256 213 292 217Q294 249 256 248Z"/>',
    }
    marks = []
    for index, radius in [(art["zodiac"], 199), (art["animal"], 184)]:
        x, y = point(radius, index * 30 - 90).split(',')
        marks.append(f'<circle cx="{x}" cy="{y}" r="6" fill="{b}"/>')
    name_dots = ''.join(f'<circle cx="{256+(i-(art["name_number"] or 0)/2+.5)*9}" cy="327" r="2"/>' for i in range(art["name_number"] or 0))
    stars = ''
    for i in range(32):
        x, y = point(205 + digest[i] % 30, digest[(i+11)%32]*360/256).split(',')
        stars += f'<circle cx="{x}" cy="{y}" r="{.6+digest[(i+5)%32]%3*.3:.1f}" opacity=".5"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-labelledby="title desc">
<title id="title">{escape(talisman['name'])}</title><desc id="desc">{escape(talisman['meaning'])}</desc>
<defs><radialGradient id="bg"><stop stop-color="{background}"/><stop offset="1" stop-color="#0b1418"/></radialGradient><linearGradient id="ink" x2="1" y2="1"><stop stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient></defs>
<circle cx="256" cy="256" r="255" fill="url(#bg)"/>
<g fill="{a}">{stars}</g>
<g fill="none" stroke="url(#ink)" stroke-width="1.4"><circle cx="256" cy="256" r="246"/><circle cx="256" cy="256" r="238" opacity=".4"/><circle cx="256" cy="256" r="218" opacity=".6"/><circle cx="256" cy="256" r="199"/>{''.join(ornaments)}<circle cx="256" cy="256" r="58"/>
<g stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round">{centers[talisman['id']]}</g></g>
<g stroke="{a}" fill="{a}">{constellation}{''.join(marks)}{name_dots}</g>
<text x="256" y="362" text-anchor="middle" font-family="Georgia,serif" font-size="12" letter-spacing="3" fill="{a}">{zodiac}</text>
<text x="256" y="384" text-anchor="middle" font-family="Georgia,serif" font-size="15" letter-spacing="4" fill="{a}">2027 · {art['year_number']}</text>
</svg>'''
