# tea_assistant

Внутренний web-ассистент для сотрудников чайного магазина.

Помогает быстро подобрать пуэр по запросу клиента: матрица выбора, поиск, фильтры, карточка чая и рекомендации на правилах (без AI). Отдельно генерируется печатный PDF-каталог A5.

**Стек:** React + Vite · данные в JSON · без backend и авторизации.

---

## Быстрый старт

### Требования

- Node.js 18+ (лучше LTS) и npm
- для импорта Excel / PDF: Python 3.10+ и зависимости из `scripts/requirements.txt`

### Установка

```bash
npm install
pip install -r scripts/requirements.txt
```

### Локальный запуск

```bash
npm run dev
```

Откройте адрес из терминала (обычно `http://localhost:5173`).

### Production-сборка

```bash
npm run build
npm run preview
```

Сборка попадает в `dist/`.

---

## Что уже реализовано

- каталог из `public/teas.json` + фото чаёв
- **матрица выбора**: когда пить, задача (эффект), вкус, характер
- поиск по артикулу и названию
- фильтры: вид чая, термос, проливы
- список, детальная карточка, рекомендации (лучший + альтернативы) на score
- импорт Excel → JSON
- генерация печатного PDF-каталога A5 (карточки, факты, правила, матрицы)

## Что отключено / не сделано

- **AI-помощник** скрыт флагом `ENABLE_AI_ASSISTANT = false` в `src/config/featureFlags.js` (DeepSeek пока не подключаем)
- backend, БД, авторизация, админка

Матрицу выбора можно выключить флагом `ENABLE_SELECTION_MATRIX`.

---

## Где лежат данные

| Что | Путь |
|-----|------|
| Рабочий каталог приложения | `public/teas.json` |
| Фото в UI | `public/images/tea/` |
| Исходные фото для импорта | `public_images_tea/` |
| Excel-источник ассортимента | `teas_data.xlsx` (лист `таблица (итог)`) |
| Факты и правила заваривания (PDF) | `Tea_fact.xlsx` |
| Матрицы для PDF | `matrica_tea.xlsx` |
| Логотип | `public/logo/logo-main.jpg` |
| Иконки PDF | `public/catalog-icons/` |

Приложение читает только `public/teas.json` и файлы из `public/`.

---

## Импорт Excel → JSON

```bash
python scripts/import_teas_from_excel.py
# или
npm run import:teas
```

Скрипт обновляет `public/teas.json` и копирует фото из `public_images_tea/` в `public/images/tea/`.

---

## Печатный PDF-каталог

```bash
pip install -r scripts/requirements.txt
npm run catalog:pdf
```

Результат (локально, **не коммитится**): `tea_catalog_a5.pdf`

- формат **152×214 мм**, верх **15 мм** под сшивку
- страницы чаёв, факты, правила заваривания, матрицы выбора
- обложка с логотипом

Пробная страница:

```bash
python scripts/generate_tea_catalog_pdf.py --sample
python scripts/generate_tea_catalog_pdf.py --sample --article ПУ-89
```

---

## Структура репозитория

```text
tea_assistant/
├── public/                 # статика для Vite (teas.json, images, logo)
├── public_images_tea/      # исходные фото для импорта
├── src/                    # React-приложение
│   ├── components/
│   ├── config/featureFlags.js
│   ├── services/
│   └── utils/
├── scripts/                # Excel-импорт, PDF, smoke
├── docs/                   # обзор продукта и логика (справочно)
├── teas_data.xlsx
├── Tea_fact.xlsx
├── matrica_tea.xlsx
├── .env.example
└── package.json
```

Подробнее про продукт и данные: папка `docs/`.

---

## Переменные окружения

Сейчас **не обязательны**. AI отключён.

Когда будете подключать DeepSeek:

```bash
copy .env.example .env
```

Заполните `VITE_DEEPSEEK_API_KEY`. Файл `.env` в Git не попадает.

---

## Основные команды

| Команда | Назначение |
|--------|------------|
| `npm install` | зависимости Node |
| `npm run dev` | разработка |
| `npm run build` | сборка в `dist/` |
| `npm run preview` | просмотр сборки |
| `npm run lint` | oxlint |
| `npm run import:teas` | Excel → JSON |
| `npm run catalog:pdf` | PDF-каталог A5 |
| `npm run smoke:preview` | smoke при запущенном preview |
| `npm run deploy` / `deploy:preview` | Vercel (нужен login) |

---

## Деплой

Рекомендуется **Vercel** (`vercel.json` уже в репозитории). Запасной вариант — Netlify (`netlify.toml`).

```bash
npx vercel login
npm run deploy
```

Или: залить репозиторий на GitHub → Import на vercel.com (Framework: Vite, output: `dist`).

---

## Передача другому разработчику

1. Клонировать репозиторий  
2. `npm install` (+ при необходимости `pip install -r scripts/requirements.txt`)  
3. `npm run dev`  
4. Данные править в Excel → `npm run import:teas`  
5. PDF: `npm run catalog:pdf`  
6. AI не включать, пока нет ключа и решения по продукту  

Секреты только в `.env` / настройках хостинга, не в коде.
