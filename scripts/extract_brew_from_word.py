"""
Извлечение параметров заваривания из обучающего Word → teas_data.xlsx.

Запуск:
  python scripts/extract_brew_from_word.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "Шу-шен блины ( для обуения).docx"
XLSX = ROOT / "teas_data.xlsx"
SHEET = "таблица (итог)"

ART_RE = re.compile(r"Артикул\s*:\s*([А-ЯA-ZЁ]{1,3})\s*[-–]?\s*(\d+)", re.I)
DOSE_RE = re.compile(
    r"(?:Количество чая|Пропорци[яи]|дозировка)\s*:\s*([^\n]+)",
    re.I,
)
TEMP_RE = re.compile(r"Температура(?:\s*воды)?\s*:\s*([^\n]+)", re.I)
# «5–10 секунд», «по 5–10 секунд», «8…40 сек»
SEC_RANGE_RE = re.compile(
    r"(\d+)\s*[–\-….]+\s*(\d+)\s*сек",
    re.I,
)
SEC_SINGLE_RE = re.compile(r"(\d+)\s*сек", re.I)
STEEPS_RE = re.compile(
    r"(?:выдерживает|до|около)\s*(\d+)\s*(?:\+|–|-)?\s*(?:пролив|завар)",
    re.I,
)
GRAMS_RE = re.compile(r"(\d+)\s*[–\-]\s*(\d+)\s*г(?:рамм)?(?:а|ов)?", re.I)
GRAMS_ONE_RE = re.compile(r"(\d+)\s*г(?:рамм)?(?:а|ов)?", re.I)
ML_RE = re.compile(r"(\d+)\s*[–\-]\s*(\d+)\s*мл|(\d+)\s*мл", re.I)


def norm_article(prefix: str, num: str) -> str:
    return f"{prefix.upper()}-{num}"


def clean_temp(raw: str) -> str:
    raw = raw.strip().rstrip(".")
    # берём только диапазон/число °C
    m = re.search(r"(\d{2,3}\s*[–\-]\s*\d{2,3}|\d{2,3})\s*°\s*C", raw, re.I)
    if m:
        return m.group(1).replace(" ", "").replace("-", "–") + "°C"
    m = re.search(r"(\d{2,3}\s*[–\-]\s*\d{2,3}|\d{2,3})", raw)
    if m:
        return m.group(1).replace(" ", "").replace("-", "–") + "°C"
    return ""


def clean_dose(raw: str) -> str:
    raw = raw.strip().rstrip(".")
    g = GRAMS_RE.search(raw) or GRAMS_ONE_RE.search(raw)
    ml = ML_RE.search(raw)
    if not g:
        return ""
    if g.lastindex and g.lastindex >= 2 and g.group(2) and g.re is GRAMS_RE:
        grams = f"{g.group(1)}–{g.group(2)}г"
    elif g.re is GRAMS_RE:
        grams = f"{g.group(1)}–{g.group(2)}г"
    else:
        grams = f"{g.group(1)}г"
    if not ml:
        return grams
    if ml.group(1) and ml.group(2):
        return f"{grams}/{ml.group(1)}–{ml.group(2)}мл"
    ml_val = ml.group(3) or ml.group(1)
    return f"{grams}/{ml_val}мл"


def clean_time(part: str) -> str:
    # предпочитаем диапазон из текста про проливы (не только промывку)
    candidates = []
    for m in SEC_RANGE_RE.finditer(part):
        a, b = int(m.group(1)), int(m.group(2))
        # пропускаем совсем короткие «промывочные» если есть более длинные
        candidates.append((a, b, m.start()))
    if candidates:
        # берём самый «широкий» или первый после слова проливы
        a, b, _ = max(candidates, key=lambda t: (t[1] - t[0], t[1]))
        return f"{a}…{b} сек"
    m = SEC_SINGLE_RE.search(part)
    if m:
        return f"{m.group(1)} сек"
    return ""


def clean_steeps(part: str) -> str:
    m = STEEPS_RE.search(part)
    if m:
        return m.group(1)
    # эвристика: «множество проливов» → 8+
    if re.search(r"множество пролив", part, re.I):
        return "8+"
    if re.search(r"много\s+пролив", part, re.I):
        return "8+"
    return ""


def split_sections(full_text: str) -> dict[str, str]:
    # режем по «Артикул:»
    chunks = re.split(r"(?=Артикул\s*:)", full_text, flags=re.I)
    out: dict[str, str] = {}
    for chunk in chunks:
        m = ART_RE.search(chunk)
        if not m:
            continue
        art = norm_article(m.group(1), m.group(2))
        # если артикул уже был — дополняем (встречается повторно)
        out[art] = (out.get(art, "") + "\n" + chunk).strip()
    return out


def extract_from_section(text: str) -> dict[str, str]:
    dose_m = DOSE_RE.search(text)
    temp_m = TEMP_RE.search(text)
    return {
        "brewDose": clean_dose(dose_m.group(1)) if dose_m else "",
        "brewTemp": clean_temp(temp_m.group(1)) if temp_m else "",
        "brewTime": clean_time(text),
        "brewSteeps": clean_steeps(text),
    }


def main() -> int:
    if not DOCX.exists():
        print(f"Нет файла: {DOCX}", file=sys.stderr)
        return 1
    if not XLSX.exists():
        print(f"Нет файла: {XLSX}", file=sys.stderr)
        return 1

    doc = Document(str(DOCX))
    full = "\n".join(p.text for p in doc.paragraphs)
    # таблицы тоже могут содержать параметры
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells]
            full += "\n" + " | ".join(cells)

    sections = split_sections(full)
    print(f"Секций с артикулом в Word: {len(sections)}")

    wb = load_workbook(XLSX)
    ws = wb[SHEET]
    headers = {str(ws.cell(1, c).value or "").strip().lower(): c for c in range(1, ws.max_column + 1)}
    col_art = headers.get("article")
    col_dose = headers.get("дозировка")
    col_temp = headers.get("температура")
    col_time = headers.get("время пролива")
    col_steeps = headers.get("число заварок")
    if not all([col_art, col_dose, col_temp, col_time, col_steeps]):
        print("Не найдены колонки заваривания в Excel", headers, file=sys.stderr)
        return 1

    updated = 0
    missing = []
    for r in range(2, ws.max_row + 1):
        art = str(ws.cell(r, col_art).value or "").strip()
        if not art:
            continue
        section = sections.get(art)
        if not section:
            missing.append(art)
            continue
        data = extract_from_section(section)
        # не затираем уже вручную заполненные, если Word пуст
        if data["brewDose"]:
            ws.cell(r, col_dose).value = data["brewDose"]
        if data["brewTemp"]:
            ws.cell(r, col_temp).value = data["brewTemp"]
        if data["brewTime"]:
            ws.cell(r, col_time).value = data["brewTime"]
        if data["brewSteeps"]:
            ws.cell(r, col_steeps).value = data["brewSteeps"]
        if any(data.values()):
            updated += 1
            print(
                f"{art}: dose={data['brewDose']!r} temp={data['brewTemp']!r} "
                f"time={data['brewTime']!r} steeps={data['brewSteeps']!r}"
            )

    wb.save(XLSX)
    print(f"\nОбновлено строк: {updated}")
    if missing:
        print(f"Нет в Word ({len(missing)}): {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
