# Мутно · 2027

Небольшое приложение на FastAPI: пользователь указывает имя, дату рождения,
отвечает на пять вопросов и формулирует желание на 2027 год. Сервис возвращает
символическое послание и персональный векторный SVG-талисман для скачивания.
Приложение предназначено для развлечения и вдохновения, а не достоверного
предсказания будущего.

## Текущий этап

Версия 0.1.0 работает **по шаблонам, без LLM**. Выбор направления, способа действия,
источника сил и разрешения себе влияет на текст, стихия задаёт палитру.
Все данные анкеты, включая имя, дату рождения и желание, участвуют в стабильном
выборе символа и варианта узора. Одинаковая анкета даёт одинаковый результат.
Персональные данные не сохраняются в базе, файлах или логах приложения.
Они передаются в POST-теле, обрабатываются в памяти и возвращаются браузеру.
На странице они остаются до закрытия или перезагрузки вкладки.

Следующий этап: отдельный генератор на домашнем Windows-ПК, обращение к нему
из VPS по закрытому туннелю и возврат к шаблонам при недоступности модели.
Сейчас интеграция LLM ещё не реализована.

## Быстрый запуск

Требуется Python 3.11+; CI проверяет Python 3.13 (версия Debian 13).

```bash
git clone https://github.com/Mutneckiy/mutno_2027.git
cd mutno_2027
python -m venv .venv
```

Активация в Linux/macOS:

```bash
source .venv/bin/activate
```

Активация в Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

```bash
python -m pip install -r requirements-dev.txt
```

Необязательно: скопировать `.env.example` в `.env` и изменить настройки.
В PowerShell: `Copy-Item .env.example .env`; в Linux: `cp .env.example .env`.

Обычный запуск без автоматической перезагрузки:

```bash
python -m uvicorn app_final:app --host 127.0.0.1 --port 8017 --no-access-log
```

Открыть http://127.0.0.1:8017/ и http://127.0.0.1:8017/docs.
Для разработки можно добавить `--reload`. Команды выполняются из корня проекта.

## Настройки

| Переменная | Значение по умолчанию | Назначение |
| --- | --- | --- |
| APP_TITLE | Мутно · 2027 | Название в OpenAPI |
| APP_VERSION | 0.1.0 | Версия в `/version` и OpenAPI |
| LOG_LEVEL | INFO | Уровень логирования: INFO, WARNING, DEBUG |

`.env` автоматически читается из папки проекта. Переменные процесса имеют
приоритет. Настоящий `.env` исключён из Git; в репозитории только `.env.example`.
Для применения настроек нужно перезапустить приложение.

## API

| Метод | Маршрут | Назначение |
| --- | --- | --- |
| GET | `/` | Сайт с анкетой |
| GET | `/health` | Проверка работы, `status=ok` |
| GET | `/version` | Версия приложения |
| GET | `/api/questions` | Пять вопросов с вариантами |
| GET | `/api/talismans` | Каталог символов |
| POST | `/api/predictions` | Прогноз и SVG по параметрам анкеты |
| POST | `/api/talisman.svg` | Скачать SVG по параметрам анкеты |
| GET | `/docs` | Интерактивная документация API |

Пример тела POST (варианты ответов нумеруются от 0 до 3):

```json
{
  "full_name": "Андрей",
  "birth_date": "1987-10-06",
  "answers": {"direction": 0, "change": 1, "resource": 2, "element": 3, "step": 0},
  "wish": "Создать свой проект"
}
```

Неверные или пропущенные ответы, пустое имя, желание короче 3 символов и дата
рождения в будущем возвращают HTTP 422. Поля вне схемы запрещены.
SVG формируется из фиксированных геометрических элементов, а не пользовательской
разметки. В браузере пользовательские строки вставляются через `textContent`.

## Тесты и CI

```bash
python -m pytest -v
```

Проверяются health, версия из окружения, главная страница, статические файлы,
каталог вопросов и символов, персонализация, повторяемость, влияние ответов,
ошибочные параметры, SVG-скачивание и отсутствие анкетных данных в логах.

GitHub Actions (`.github/workflows/ci.yml`) запускается на каждый push и pull request.
После успешных тестов создаётся artifact `mutno-2027` с приложением и инструкциями.
Workflow проверяет и упаковывает приложение, но не разворачивает его на VPS.

## Debian 13: установка рядом с OpenClaw

Сначала проверить существующие слушающие порты и веб-серверы:

```bash
ss -lntup
systemctl status nginx caddy apache2 --no-pager
```

Если порты 80/443 уже заняты OpenClaw или другим прокси, необходимо добавить домен
в существующий прокси. Не запускать второй веб-сервер на тех же портах.
Ниже сценарий **для свободных портов 80, 443 и 8017**. Он не меняет конфигурацию
OpenClaw, firewall, SSH или VPN. Команды установки выполняются от root.

```bash
apt update
apt install -y git python3 python3-venv nginx certbot python3-certbot-nginx
adduser --system --group --no-create-home mutno
git clone https://github.com/Mutneckiy/mutno_2027.git /opt/mutno_2027
cd /opt/mutno_2027
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -v
cp .env.example .env
chown root:mutno .env
chmod 640 .env
cp deploy/mutno.service /etc/systemd/system/mutno.service
systemctl daemon-reload
systemctl enable --now mutno
curl --fail http://127.0.0.1:8017/health
```

Процесс работает от отдельного системного пользователя и слушает только loopback.
Папка проекта остаётся под управлением root; приложению запись на диск не требуется.

Настройка HTTP, если Nginx выбран в качестве внешнего прокси:

```bash
cp deploy/mutno.nginx.conf /etc/nginx/sites-available/mutno
ln -s /etc/nginx/sites-available/mutno /etc/nginx/sites-enabled/mutno
nginx -t && systemctl reload nginx
```

В DNS SpaceWeb создать A-запись для основного домена (пустой поддомен) и `www`,
значение `213.183.51.225`. Домен должен использовать DNS-серверы SpaceWeb.
Если есть старые A/AAAA-записи, ведущие на другие серверы, их нужно исправить.
AAAA пока не добавлять: конфигурация выше сначала проверяется по IPv4.

Проверка DNS и HTTP:

```bash
getent ahostsv4 mutno.online
getent ahostsv4 www.mutno.online
curl --fail http://mutno.online/health
```

Порты TCP 80/443 должны быть доступны извне; если есть firewall в панели провайдера
или на VPS, разрешить их, сохранив доступ по SSH. После правильного DNS включить HTTPS:

```bash
certbot --nginx -d mutno.online -d www.mutno.online --redirect
certbot renew --dry-run
curl --fail https://mutno.online/health
curl --fail https://mutno.online/version
```

Certbot задаст вопросы о почте и условиях выпуска сертификата. Если `www` ещё
не настроен, сначала исправить его DNS либо выпускать только для `mutno.online`.
До HTTPS пользоваться только вымышленными тестовыми данными.

## Логи и диагностика

Локально сообщения идут в терминал. На VPS:

```bash
systemctl status mutno --no-pager
journalctl -u mutno -n 100 --no-pager
journalctl -u mutno -f
nginx -t
tail -n 50 /var/log/nginx/mutno-error.log
```

Приложение логирует запуск/остановку, HTTP-метод, путь, код ответа и длительность.
Тела анкет и параметры URL не логируются. Поставляемая команда отключает access-log
Uvicorn; конфигурация Nginx отключает access-log именно для этого сайта.

| Проблема | Что проверить |
| --- | --- |
| 502 от Nginx | `systemctl status mutno`, затем `curl http://127.0.0.1:8017/health` |
| Address already in use | `ss -lntup`; не останавливать OpenClaw, согласовать другой порт и прокси |
| Домен ведёт не туда | A/AAAA, DNS-серверы домена, DNS-кеш |
| Ошибка сертификата | A-записи обоих имён, доступность TCP 80 извне |
| HTTP 422 | Все пять ответов 0–3, дата не в будущем, ограничения длины |
| Вопросы не загрузились | `/health`, `/api/questions`, логи и соединение |
| ModuleNotFoundError | Активирована ли `.venv`, установлены ли зависимости |

Обновление после загрузки новых коммитов в GitHub:

```bash
cd /opt/mutno_2027
git pull --ff-only
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -v && systemctl restart mutno
```

## История разработки и сдача

Сохранять осмысленные этапы отдельными коммитами: каркас, API анкеты,
генератор талисманов, интерфейс, тесты, CI и развёртывание. Не создавать фиктивную
историю задним числом. Перед сдачей проверить публичность репозитория,
чистую установку по README, зелёный workflow и наличие artifact.

Преподавателю: ссылка на публичный репозиторий, ссылка на последний успешный
GitHub Actions и одно предложение о назначении приложения.
