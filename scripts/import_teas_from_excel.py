"""
Одноразовый / повторный импорт teas_data.xlsx → public/teas.json

Запуск из корня проекта:
  python scripts/import_teas_from_excel.py

Требует: openpyxl
  pip install openpyxl
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

try:
    from openpyxl import load_workbook
except ImportError:
    print("Нужен openpyxl: pip install openpyxl", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "teas_data.xlsx"
OUT = ROOT / "public" / "teas.json"
IMG_SRC = ROOT / "public_images_tea"
IMG_DST = ROOT / "public" / "images" / "tea"
SHEET_NAME = "таблица (итог)"

CYR = {
    "А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D", "Е": "E", "Ё": "E",
    "Ж": "ZH", "З": "Z", "И": "I", "Й": "Y", "К": "K", "Л": "L", "М": "M",
    "Н": "N", "О": "O", "П": "P", "Р": "R", "С": "S", "Т": "T", "У": "U",
    "Ф": "F", "Х": "H", "Ц": "TS", "Ч": "CH", "Ш": "SH", "Щ": "SCH",
    "Ъ": "", "Ы": "Y", "Ь": "", "Э": "E", "Ю": "YU", "Я": "YA",
}

# Поддержка и русских, и уже нормализованных английских заголовков
COLUMN_ALIASES = {
    "image": "image",
    "фото": "image",
    "article": "article",
    "артикул": "article",
    "name": "name",
    "наименование": "name",
    "category": "category",
    "вид чая": "category",
    "teaclass": "teaClass",
    "класс": "teaClass",
    "description": "description",
    "рецепт (описание)": "description",
    "besttime": "bestTime",
    "когда пить": "bestTime",
    "brewingguide": "brewingGuide",
    "правила заваривания": "brewingGuide",
    "taste": "taste",
    "вкус": "taste",
    "aroma": "aroma",
    "аромат": "aroma",
    "effectdescription": "effectDescription",
    "эффект описание": "effectDescription",
    "tags": "tags",
    "ключевые теги": "tags",
    "antitags": "antiTags",
    "анти-теги": "antiTags",
    "effect": "effect",
    "effecttags или лучше effect": "effect",
    "тег эффект": "effect",
    "forproliv": "forProliv",
    "подходит для проливов?": "forProliv",
    "forthermos": "forThermos",
    "подходит для термоса?": "forThermos",
    "brewdose": "brewDose",
    "дозировка": "brewDose",
    "brewtemp": "brewTemp",
    "температура": "brewTemp",
    "brewtime": "brewTime",
    "время пролива": "brewTime",
    "brewsteeps": "brewSteeps",
    "число заварок": "brewSteeps",
    "tastecolor": "tasteColor",
    "цвет вкуса": "tasteColor",
}


def translit(s: str) -> str:
    out = []
    for ch in s:
        up = ch.upper()
        if up in CYR:
            t = CYR[up]
            out.append(t.lower() if ch.islower() else t)
        else:
            out.append(ch)
    return "".join(out)


def clean_str(v) -> str:
    if v is None:
        return ""
    s = str(v).strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        s = s[1:-1].strip()
    return s


def to_bool(v) -> bool:
    s = clean_str(v).lower()
    if not s:
        return False
    norm = re.sub(r"\s+", " ", s).strip().rstrip(".")
    truthy = {"да", "yes", "true", "1", "допустимо", "да. идеально", "да идеально"}
    falsy = {"нет", "no", "false", "0", "категорически нет", "не желательно", "нежелательно"}
    if norm in truthy:
        return True
    if norm in falsy:
        return False
    if norm.startswith("да"):
        return True
    if "нет" in norm:
        return False
    return False


def parse_thermos_fit(v) -> tuple[bool, str, str]:
    """
    Возвращает (forThermos, thermosFit, thermosLabel).
    thermosFit:
      ideal | yes | ok | avoid | no | forbidden | unknown
    """
    label = clean_str(v)
    if not label:
        return False, "unknown", ""

    norm = re.sub(r"\s+", " ", label.lower()).strip().rstrip(".")

    if "категорически" in norm and "нет" in norm:
        return False, "forbidden", label
    if norm in {"не желательно", "нежелательно"} or "не желательн" in norm:
        return False, "avoid", label
    if "идеальн" in norm:
        return True, "ideal", label
    if norm in {"допустимо"} or "допустим" in norm:
        return True, "ok", label
    if norm in {"да", "yes", "true", "1"} or (norm.startswith("да") and "нет" not in norm):
        return True, "yes", label
    if norm in {"нет", "no", "false", "0"} or "нет" in norm:
        return False, "no", label

    # fallback к старому boolean
    flag = to_bool(v)
    return flag, ("yes" if flag else "no"), label


def make_id(article: str) -> str:
    slug = translit(clean_str(article)).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "tea-unknown"


def split_tags(v) -> list[str]:
    s = clean_str(v)
    if not s:
        return []
    s = re.sub(r"<br\s*/?>", ",", s, flags=re.I)
    return [p.strip() for p in re.split(r"[,;]", s) if p.strip()]


def as_text_list(v) -> list[str]:
    s = clean_str(v)
    if not s:
        return []
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip()
    return [s]


def split_best_time(v) -> list[str]:
    s = clean_str(v)
    if not s:
        return []
    return [p.strip() for p in re.split(r"[,;/]", s) if p.strip()]


def to_effect(v) -> list[str]:
    s = clean_str(v)
    if not s:
        return []
    return [p.strip() for p in re.split(r"[,;/]", s) if p.strip()]


def image_path(v) -> str:
    s = clean_str(v)
    if not s:
        return ""
    name = Path(s.strip("\"'").replace("\\", "/")).name
    return f"/images/tea/{name}" if name else ""


def brewing_guide(v) -> str:
    s = clean_str(v)
    if not s:
        return ""
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    # убираем лишнюю пометку «Экспертно:» / «Эксперно:»
    s = re.sub(r"(?im)(^|\n)\s*экспертн[оа]\s*:\s*", r"\1", s)
    s = re.sub(r"(?i)\bэкспертн[оа]\s*:\s*", "", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def normalize_header(cell) -> str | None:
    key = clean_str(cell).lower()
    if not key:
        return None
    return COLUMN_ALIASES.get(key)


def main() -> int:
    if not XLSX.exists():
        print(f"Файл не найден: {XLSX}", file=sys.stderr)
        return 1

    wb = load_workbook(XLSX, data_only=True, read_only=True)
    if SHEET_NAME not in wb.sheetnames:
        print(f"Лист «{SHEET_NAME}» не найден. Есть: {wb.sheetnames}", file=sys.stderr)
        return 1

    ws = wb[SHEET_NAME]
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        print("Пустой лист", file=sys.stderr)
        return 1

    header_map: dict[int, str] = {}
    for idx, cell in enumerate(rows[0]):
        field = normalize_header(cell)
        if field:
            header_map[idx] = field

    teas = []
    issues = []
    seen = set()

    for row_num, row in enumerate(rows[1:], start=2):
        raw = {field: (row[idx] if idx < len(row) else None) for idx, field in header_map.items()}
        article = clean_str(raw.get("article"))
        name = clean_str(raw.get("name"))
        if not article and not name:
            issues.append({"row": row_num, "reason": "пустые артикул и название — пропущена"})
            continue

        tid = make_id(article) if article else f"tea-row-{row_num}"
        if tid in seen:
            issues.append({"row": row_num, "article": article, "reason": f"дубликат id {tid}"})
            tid = f"{tid}-{row_num}"
        seen.add(tid)

        img = image_path(raw.get("image"))
        if img and not (IMG_SRC / Path(img).name).exists():
            issues.append({"row": row_num, "article": article, "reason": f"нет файла {Path(img).name}"})

        teas.append(
            {
                "id": tid,
                "article": article,
                "name": name,
                "category": clean_str(raw.get("category")),
                "teaClass": clean_str(raw.get("teaClass")),
                "description": clean_str(raw.get("description")),
                "bestTime": split_best_time(raw.get("bestTime")),
                "brewingGuide": brewing_guide(raw.get("brewingGuide")),
                "taste": as_text_list(raw.get("taste")),
                "aroma": as_text_list(raw.get("aroma")),
                "effectDescription": clean_str(raw.get("effectDescription")),
                "tags": split_tags(raw.get("tags")),
                "antiTags": split_tags(raw.get("antiTags")),
                "effect": to_effect(raw.get("effect")),
                "forProliv": to_bool(raw.get("forProliv")),
                "brewDose": clean_str(raw.get("brewDose")),
                "brewTemp": clean_str(raw.get("brewTemp")),
                "brewTime": clean_str(raw.get("brewTime")),
                "brewSteeps": clean_str(raw.get("brewSteeps")),
                "tasteColor": clean_str(raw.get("tasteColor")),
                "image": img,
            }
        )

        for_thermos, thermos_fit, thermos_label = parse_thermos_fit(raw.get("forThermos"))
        teas[-1]["forThermos"] = for_thermos
        teas[-1]["thermosFit"] = thermos_fit
        teas[-1]["thermosLabel"] = thermos_label


    IMG_DST.mkdir(parents=True, exist_ok=True)
    if IMG_SRC.exists():
        for f in IMG_SRC.iterdir():
            if f.is_file():
                shutil.copy2(f, IMG_DST / f.name)

    OUT.write_text(json.dumps(teas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Импортировано: {len(teas)}")
    print(f"Записано: {OUT}")
    print(f"Проблем: {len(issues)}")
    for item in issues:
        print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
