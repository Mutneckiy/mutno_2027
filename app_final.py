"""Personal predictions and SVG talismans. MVP uses local templates, not an LLM."""

from contextlib import asynccontextmanager
from datetime import date
from hashlib import sha256
from html import escape
import json
import logging
import os
from pathlib import Path
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(), format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("mutno")

QUESTIONS = [
    {"id": "direction", "text": "Что сейчас важнее всего?", "options": ["Найти своё дело", "Укрепить отношения", "Обрести спокойствие", "Открыть новое"]},
    {"id": "change", "text": "Как ты встречаешь перемены?", "options": ["Составляю план", "Доверяюсь интуиции", "Прошу поддержки", "Сразу пробую"]},
    {"id": "resource", "text": "Где ты находишь силы?", "options": ["В тишине", "С близкими", "В творчестве", "В движении"]},
    {"id": "element", "text": "Какая стихия тебе ближе?", "options": ["Земля", "Вода", "Воздух", "Огонь"]},
    {"id": "step", "text": "Что хочется разрешить себе в 2027?", "options": ["Начать заново", "Выбирать себя", "Действовать смелее", "Жить медленнее"]},
]
SYMBOLS = [
    {"id": "star", "name": "Путеводная звезда", "meaning": "Помни о своём направлении, даже когда путь ещё не виден."},
    {"id": "sun", "name": "Тихое солнце", "meaning": "Береги энергию и делись теплом в своём ритме."},
    {"id": "compass", "name": "Внутренний компас", "meaning": "Выбирай то, что согласуется с твоими ценностями."},
    {"id": "seed", "name": "Зерно перемен", "meaning": "Большие изменения начинаются с маленького действия."},
]
PALETTES = [("#c7a8ff", "#8be5d1"), ("#ffd399", "#e6a6b9"), ("#9dcfff", "#c5b4ff"), ("#9fe1c4", "#e0d09c")]


class Profile(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    full_name: str = Field(min_length=1, max_length=120)
    birth_date: date
    answers: dict[str, int]
    wish: str = Field(min_length=3, max_length=600)

    @field_validator("birth_date")
    @classmethod
    def valid_birth_date(cls, value):
        if not date(1900, 1, 1) <= value <= date.today():
            raise ValueError("Дата рождения должна быть между 1900 годом и сегодняшним днём")
        return value

    @field_validator("answers", mode="before")
    @classmethod
    def valid_answers(cls, value):
        if not isinstance(value, dict) or set(value) != {q["id"] for q in QUESTIONS}:
            raise ValueError("Ответьте на все пять вопросов")
        if any(type(v) is not int or v not in range(4) for v in value.values()):
            raise ValueError("Ответ должен быть целым числом от 0 до 3")
        return value


def personalize(profile: Profile):
    # Stable seed: identical input gives an identical talisman, independent of process.
    seed = int(sha256(json.dumps(profile.model_dump(mode="json"), ensure_ascii=False, sort_keys=True).encode()).hexdigest(), 16)
    symbol = SYMBOLS[seed % len(SYMBOLS)]
    primary, secondary = PALETTES[profile.answers["element"]]
    direction = ["дела и самореализация", "близость и взаимная поддержка", "равновесие и внутренний покой", "открытия и новый опыт"][profile.answers["direction"]]
    approach = ["Разбей желание на небольшие шаги и выбери первый.", "Запиши то, что подсказывает интуиция, и проверь это небольшим действием.", "Расскажи о своём намерении человеку, которому доверяешь.", "Устрой маленький эксперимент, прежде чем решаться на большую перемену."][profile.answers["change"]]
    resource = ["тихих паузах без спешки", "разговорах с близкими", "творчестве без оценки результата", "прогулках и новых впечатлениях"][profile.answers["resource"]]
    permission = ["начинать с чистого листа", "учитывать собственные желания", "проявлять смелость маленькими шагами", "замедляться без чувства вины"][profile.answers["step"]]
    season = ["Начало года", "Весна", "Лето", "Осень"][seed % 4]
    return {
        "year": 2027,
        "title": f"Твой 2027: {symbol['name'].lower()}",
        "intro": f"{profile.full_name}, тема твоего символического прогноза — {direction}. Пусть 2027 станет поводом разрешить себе {permission}.",
        "chapters": [
            {"title": "Твоё намерение", "text": f"«{profile.wish}» — ориентир, к которому можно возвращаться в течение года. {approach}"},
            {"title": "Точка опоры", "text": f"Ищи восстановление в {resource}. Сделай для этого место в обычной неделе, не дожидаясь идеального момента."},
            {"title": "Время для шага", "text": f"{season} — символическая точка проверки своего курса. Спроси себя: какой небольшой шаг сейчас приблизит меня к желаемому?"},
        ],
        "talisman": {**symbol, "primary": primary, "secondary": secondary, "variant": seed % 12},
        "mode": "template",
        "notice": "Развлекательный символический прогноз, а не достоверное предсказание будущего.",
    }


def render_svg(talisman):
    a, b = talisman["primary"], talisman["secondary"]
    shapes = {
        "star": '<path d="M256 124 285 221 388 256 285 285 256 388 227 285 124 256 227 227Z"/>',
        "sun": '<circle cx="256" cy="256" r="63"/>' + ''.join(f'<path transform="rotate({i * 30} 256 256)" d="M256 137V164"/>' for i in range(12)),
        "compass": '<path d="M256 115 295 256 256 397 217 256Z"/><path d="M115 256H397M256 115V397"/>',
        "seed": '<path d="M256 365V230M256 279C151 279 153 173 153 173S256 172 256 279ZM256 235C256 137 359 147 359 147S364 241 256 235Z"/>',
    }
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-labelledby="title desc">
<title id="title">{escape(talisman['name'])}</title><desc id="desc">{escape(talisman['meaning'])}</desc>
<defs><radialGradient id="bg"><stop stop-color="#282344"/><stop offset="1" stop-color="#11101c"/></radialGradient><linearGradient id="ink" x2="1" y2="1"><stop stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient></defs>
<rect width="512" height="512" rx="48" fill="url(#bg)"/>
<g fill="none" stroke="url(#ink)" stroke-width="1.5"><circle cx="256" cy="256" r="201" opacity=".3"/><circle cx="256" cy="256" r="179" opacity=".6"/>
<g transform="rotate({talisman['variant'] * 5} 256 256)"><path d="M256 55 430 357H82Z" opacity=".22"/><path d="M256 457 82 155H430Z" opacity=".22"/></g>
<g stroke-width="3" stroke-linecap="round" stroke-linejoin="round">{shapes[talisman['id']]}</g></g>
<g fill="{a}"><circle cx="256" cy="55" r="4"/><circle cx="55" cy="256" r="3"/><circle cx="457" cy="256" r="3"/></g>
<text x="256" y="425" text-anchor="middle" font-family="serif" font-size="17" letter-spacing="7" fill="{b}">2027</text></svg>'''


@asynccontextmanager
async def lifespan(app):
    log.info("Application started version=%s mode=template", app.version)
    yield
    log.info("Application stopped")


def create_app():
    application = FastAPI(title=os.getenv("APP_TITLE", "Мутно · 2027"), version=os.getenv("APP_VERSION", "0.1.0"), lifespan=lifespan)
    application.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

    @application.middleware("http")
    async def request_log(request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        # Never log questionnaire bodies, query strings, names or dates of birth.
        log.info("request method=%s path=%s status=%s duration_ms=%.1f", request.method, request.url.path, response.status_code, (time.monotonic() - start) * 1000)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'" if not request.url.path.startswith("/docs") else "frame-ancestors 'none'"
        if request.method == "POST":
            response.headers["Cache-Control"] = "no-store"
        return response

    @application.get("/", include_in_schema=False)
    def index():
        return FileResponse(BASE / "static" / "index.html")

    @application.get("/health")
    def health():
        return {"status": "ok", "mode": "template"}

    @application.get("/version")
    def version():
        return {"version": application.version}

    @application.get("/api/questions")
    def questions():
        return {"questions": QUESTIONS}

    @application.get("/api/talismans")
    def talismans():
        return {"talismans": SYMBOLS}

    @application.post("/api/predictions")
    def predict(profile: Profile):
        result = personalize(profile)
        result["svg"] = render_svg(result["talisman"])
        return result

    @application.post("/api/talisman.svg", response_class=Response)
    def download(profile: Profile):
        return Response(render_svg(personalize(profile)["talisman"]), media_type="image/svg+xml", headers={"Content-Disposition": 'attachment; filename="mutno-2027.svg"'})

    return application


app = create_app()
