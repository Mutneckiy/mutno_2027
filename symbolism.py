"""Calendar-based signs and explicitly symbolic (not predictive) numerology."""

from datetime import date
import unicodedata

from lunar_python import Solar

# Conventional popular sun-sign boundaries; no birth time/location is collected.
WESTERN = [
    ((1, 20), "Водолей", "Воздух", "свобода мысли и новые связи"),
    ((2, 19), "Рыбы", "Вода", "воображение и чуткость"),
    ((3, 21), "Овен", "Огонь", "инициатива и смелость первого шага"),
    ((4, 20), "Телец", "Земля", "терпение и создание устойчивой опоры"),
    ((5, 21), "Близнецы", "Воздух", "любопытство и обмен идеями"),
    ((6, 21), "Рак", "Вода", "забота и чувство дома"),
    ((7, 23), "Лев", "Огонь", "творчество и открытое самовыражение"),
    ((8, 23), "Дева", "Земля", "внимание к деталям и полезные привычки"),
    ((9, 23), "Весы", "Воздух", "равновесие и искусство сотрудничества"),
    ((10, 23), "Скорпион", "Вода", "глубина и готовность к обновлению"),
    ((11, 22), "Стрелец", "Огонь", "поиск смысла и расширение горизонтов"),
    ((12, 22), "Козерог", "Земля", "последовательность и долгосрочный замысел"),
]
ANIMALS = ["Крыса", "Бык", "Тигр", "Кролик", "Дракон", "Змея",
           "Лошадь", "Коза", "Обезьяна", "Петух", "Собака", "Свинья"]
ANIMAL_THEMES = ["находчивость", "надёжность", "отвага", "дипломатичность",
                 "масштаб замысла", "наблюдательность", "свобода движения",
                 "созидание и бережность", "изобретательность", "ясность и порядок",
                 "верность своим ценностям", "щедрость и простые радости"]
ELEMENTS = ["Дерево", "Огонь", "Земля", "Металл", "Вода"]
NUMBER_THEMES = {
    1: "инициатива", 2: "сотрудничество", 3: "самовыражение",
    4: "устойчивость", 5: "исследование", 6: "забота",
    7: "осмысление", 8: "организация", 9: "завершение и щедрость",
}
CYRILLIC = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
LATIN = "abcdefghijklmnopqrstuvwxyz"


def reduce_number(value):
    while value > 9:
        value = sum(map(int, str(value)))
    return value


def chinese_sign(birth_date):
    # Lunar New Year, not January 1 or the alternative Li Chun convention.
    year = Solar.fromYmd(birth_date.year, birth_date.month, birth_date.day).getLunar().getYear()
    index = (year - 4) % 12
    return {"year": year, "animal": ANIMALS[index],
            "element": ELEMENTS[((year - 4) % 10) // 2], "theme": ANIMAL_THEMES[index]}


def symbolic_profile(full_name, birth_date):
    western = WESTERN[-1]
    for entry in WESTERN:
        if (birth_date.month, birth_date.day) >= entry[0]:
            western = entry
    name_sum = 0
    for char in unicodedata.normalize("NFC", full_name).casefold():
        for alphabet in (CYRILLIC, LATIN):
            if char in alphabet:
                name_sum += alphabet.index(char) % 9 + 1
                break
    life = reduce_number(sum(map(int, birth_date.strftime("%Y%m%d"))))
    personal = reduce_number(sum(map(int, f"{birth_date.month}{birth_date.day}2027")))
    name = reduce_number(name_sum) if name_sum else None
    return {
        "western": {"sign": western[1], "element": western[2], "theme": western[3]},
        "chinese": chinese_sign(birth_date),
        "numerology": {
            "life_path": life, "life_theme": NUMBER_THEMES[life],
            "name_number": name, "name_theme": NUMBER_THEMES.get(name),
            "personal_year": personal, "year_theme": NUMBER_THEMES[personal],
        },
        "year_2027": {
            "before_new_year": chinese_sign(date(2027, 1, 1)),
            "from": "2027-02-06", "after_new_year": chinese_sign(date(2027, 2, 6)),
        },
        "method": (
            "Западный знак — по условным календарным границам, без натальной карты. "
            "Китайский год — от лунного Нового года, не от 1 января. "
            "Числа сведены к 1–9: путь — сумма цифр даты рождения; личный год — "
            "день, месяц рождения и 2027; имя — авторская циклическая нумерация букв "
            "русского алфавита с ё и латинского A–Z от 1 до 9. Учитывается всё введённое "
            "имя или ФИО, прочие символы пропускаются. Это развлекательная символика."
        ),
    }


def apply_symbolism(result, profile):
    """Give the offline fallback the same personal foundation as the model."""
    context = symbolic_profile(profile.full_name, profile.birth_date)
    western, chinese, numbers = context["western"], context["chinese"], context["numerology"]
    result["symbolic_profile"] = context
    result["intro"] += (
        f" В языке символов твоя основа — {western['sign']} ({western['element']}) "
        f"и {chinese['animal']} со стихией «{chinese['element']}». "
        "Это образы для размышления, а не заданная судьба."
    )
    result["chapters"][0]["text"] += (
        f" Пусть образ знака «{western['sign']}» — {western['theme']} — "
        "поможет выбрать подходящий тебе способ двигаться к желанию."
    )
    result["chapters"][1]["text"] += (
        f" Китайский образ «{chinese['animal']}» добавляет тему «{chinese['theme']}». "
        f"Число пути {numbers['life_path']} здесь символизирует {numbers['life_theme']}."
    )
    if numbers["name_number"] is not None:
        result["chapters"][1]["text"] += (
            f" Число введённого имени — {numbers['name_number']}: {numbers['name_theme']}."
        )
    result["chapters"][2]["text"] += (
        f" Тема личного года {numbers['personal_year']} — {numbers['year_theme']}. "
        "С 6 февраля 2027 начинается год Огненной Козы: возьми его образ "
        "бережного созидания как напоминание о небольших регулярных шагах."
    )
    return result
