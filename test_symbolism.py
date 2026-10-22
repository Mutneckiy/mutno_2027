from datetime import date

import pytest

from symbolism import chinese_sign, symbolic_profile


@pytest.mark.parametrize("birthday,animal,year", [
    (date(2024, 2, 9), "Кролик", 2023),
    (date(2024, 2, 10), "Дракон", 2024),
    (date(1987, 1, 28), "Тигр", 1986),
    (date(1987, 1, 29), "Кролик", 1987),
    (date(1900, 1, 1), "Свинья", 1899),
    (date(1900, 1, 31), "Крыса", 1900),
])
def test_lunar_year_boundary(birthday, animal, year):
    result = chinese_sign(birthday)
    assert result["animal"] == animal
    assert result["year"] == year


@pytest.mark.parametrize("birthday,sign", [
    (date(2000, 1, 1), "Козерог"), (date(2000, 1, 19), "Козерог"),
    (date(2000, 1, 20), "Водолей"), (date(2000, 3, 20), "Рыбы"),
    (date(2000, 3, 21), "Овен"), (date(2000, 12, 22), "Козерог"),
])
def test_popular_western_boundaries(birthday, sign):
    assert symbolic_profile("Андрей", birthday)["western"]["sign"] == sign


def test_name_normalization_and_known_numbers():
    result = symbolic_profile("Андрей", date(1987, 10, 6))
    assert result["western"]["sign"] == "Весы"
    assert result["chinese"]["animal"] == "Кролик"
    assert result["chinese"]["element"] == "Огонь"
    assert result["numerology"]["life_path"] == 5
    assert result["numerology"]["name_number"] == 2
    assert result["numerology"]["personal_year"] == 9
    assert symbolic_profile(" АНДРЕЙ- ", date(1987, 10, 6)) == result
    assert symbolic_profile("李", date(1987, 10, 6))["numerology"]["name_number"] is None
    assert symbolic_profile("Анна", date(1987, 10, 6))["numerology"]["name_number"] == 5


def test_2027_changes_in_february():
    year = symbolic_profile("A", date(2000, 1, 1))["year_2027"]
    assert year["from"] == "2027-02-06"
    assert year["before_new_year"]["animal"] == "Лошадь"
    assert year["after_new_year"]["animal"] == "Коза"
    assert year["after_new_year"]["element"] == "Огонь"
