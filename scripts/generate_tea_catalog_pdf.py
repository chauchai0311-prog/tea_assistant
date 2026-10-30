"""
Генерация печатного PDF-каталога чаёв (A5 под верхнюю сшивку).

Формат: 152 × 214 мм
Верхний отступ под сшивку: 15 мм
1 чай = 1 страница

Макет (как в приложении):
  слева фото | справа название, артикул, иконки проливов,
               строка термоса, оттенки вкуса, характер, время
  ниже — описание, вкус, аромат, эффект, правила заваривания
После каталога: страницы «Интересный факт» + «Правила заваривания»
  (данные из Tea_fact.xlsx).

Примеры:
  python scripts/generate_tea_catalog_pdf.py --sample
  python scripts/generate_tea_catalog_pdf.py --sample --article ПУ-89
  python scripts/generate_tea_catalog_pdf.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

from fpdf import FPDF
from fpdf.drawing import Transform
from openpyxl import load_workbook
from openpyxl.cell.rich_text import CellRichText, TextBlock
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TEAS_JSON = ROOT / "public" / "teas.json"
IMAGES_DIR = ROOT / "public" / "images" / "tea"
ICONS_DIR = ROOT / "public" / "catalog-icons"
FACTS_XLSX = ROOT / "Tea_fact.xlsx"
MATRIX_XLSX = ROOT / "matrica_tea.xlsx"
LOGO_MAIN = ROOT / "public" / "logo" / "logo-main.jpg"
OUT_PDF = ROOT / "tea_catalog_a5.pdf"
OUT_SAMPLE = ROOT / "tea_catalog_a5_sample.pdf"

COVER_GREEN = (45, 90, 55)
COVER_QUOTE = (
    "«Пуэр не должен быть элементом роскоши,\n"
    "ведь чай входит в «7 необходимых для жизни продуктов»"
)
COVER_QUOTE_ATTR = "Основатели Хайваня"
COVER_TITLE = "ПУЭРЫ"
COVER_SUBTITLE = "(блины)"

THERMOS_COLORS = {
    "ideal": (61, 110, 55),
    "yes": (90, 110, 60),
    "ok": (120, 110, 55),
    "avoid": (140, 100, 55),
    "no": (130, 90, 80),
    "forbidden": (140, 70, 65),
}

PAGE_W = 152
PAGE_H = 214
MARGIN_TOP = 15
MARGIN_X = 10
MARGIN_BOTTOM = 10

CONTENT_W = PAGE_W - 2 * MARGIN_X
CONTENT_BOTTOM = PAGE_H - MARGIN_BOTTOM

# Верхний блок: фото слева
PHOTO_W = 58
PHOTO_GAP = 4
RIGHT_W = CONTENT_W - PHOTO_W - PHOTO_GAP

TASTE_FLAVORS = {
    "Древесно-землистый",
    "Минеральный",
    "Освежающий",
    "Ореховый",
    "Сливочный",
    "Карамельный",
    "Сухофруктовый",
    "Фруктовый",
    "Цветочный",
    "Медовый",
    "Шоколадный",
}
TASTE_CHARACTERS = {"Мягкий", "Плотный", "Спокойный", "Терпкий", "Яркий"}

# Порядок групп вкуса в каталоге (как в таблице сортировки)
TASTE_GROUP_ORDER: list[tuple[str, ...]] = [
    ("Древесно-землистый",),
    ("Ореховый",),
    ("Шоколадный",),
    ("Сливочный", "Карамельный"),
    ("Сухофруктовый", "Фруктовый"),
    ("Цветочный", "Медовый"),
    ("Минеральный", "Освежающий"),
]

# Заливка ячейки «Вкус» по ноте / названию цвета из Excel
FLAVOR_FILLS: dict[str, tuple[int, int, int]] = {
    "Древесно-землистый": (232, 232, 228),  # светло-серый
    "Ореховый": (255, 236, 214),  # светло-оранжевый
    "Шоколадный": (235, 220, 205),  # светло-коричневый
    "Сливочный": (255, 236, 214),  # светло-оранжевый
    "Карамельный": (255, 236, 214),
    "Сухофруктовый": (255, 230, 232),  # светло-розовый
    "Фруктовый": (255, 230, 232),
    "Цветочный": (255, 246, 210),  # светло-жёлтый
    "Медовый": (255, 246, 210),
    "Минеральный": (228, 242, 232),  # светло-зелёный
    "Освежающий": (228, 242, 232),
}

TASTE_COLOR_NAME_FILLS: dict[str, tuple[int, int, int]] = {
    "светло-серый": (232, 232, 228),
    "светло-оранжевый": (255, 236, 214),
    "светло-коричневый": (235, 220, 205),
    "светло-розовый": (255, 230, 232),
    "светло-желтый": (255, 246, 210),
    "светло-жёлтый": (255, 246, 210),
    "светло-зеленый": (228, 242, 232),
    "светло-зелёный": (228, 242, 232),
}

DEFAULT_TASTE_FILL = (245, 242, 232)
TABLE_LINE = (200, 205, 185)

FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\arial.ttf"),
    Path(r"C:\Windows\Fonts\segoeui.ttf"),
    Path(r"C:\Windows\Fonts\calibri.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/Library/Fonts/Arial.ttf"),
]
FONT_BOLD_CANDIDATES = [
    Path(r"C:\Windows\Fonts\arialbd.ttf"),
    Path(r"C:\Windows\Fonts\segoeuib.ttf"),
    Path(r"C:\Windows\Fonts\calibrib.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]
FONT_ITALIC_CANDIDATES = [
    Path(r"C:\Windows\Fonts\ariali.ttf"),
    Path(r"C:\Windows\Fonts\segoeuii.ttf"),
    Path(r"C:\Windows\Fonts\calibrii.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"),
]


def pick_font(candidates: list[Path]) -> Path:
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("Не найден Unicode-шрифт с кириллицей (Arial/DejaVu).")


def join_list(value) -> str:
    if not value:
        return ""
    if isinstance(value, list):
        return ", ".join(str(v).strip() for v in value if str(v).strip())
    return str(value).strip()


def split_taste_tags(tags: list | None) -> tuple[list[str], list[str]]:
    flavors, characters = [], []
    for tag in tags or []:
        if tag in TASTE_FLAVORS:
            flavors.append(tag)
        elif tag in TASTE_CHARACTERS:
            characters.append(tag)
    return flavors, characters


def format_taste_cell(flavors: list[str], characters: list[str]) -> str:
    """«Цветочный, медовый, яркий» — первая с заглавной, остальные строчными."""
    parts = [*(flavors or []), *(characters or [])]
    if not parts:
        return ""
    lowered = [p.strip().lower() for p in parts if p and str(p).strip()]
    if not lowered:
        return ""
    lowered[0] = lowered[0][:1].upper() + lowered[0][1:]
    return ", ".join(lowered)


# При нескольких нотах — цвет по порядку групп каталога
FLAVOR_FILL_PRIORITY = [f for group in TASTE_GROUP_ORDER for f in group]


def taste_group_index(flavors: list[str] | None, taste_color: str = "") -> int:
    """Индекс группы для сортировки каталога (меньше = раньше)."""
    color_key = (taste_color or "").strip().lower().replace("ё", "е")
    color_to_group = {
        "светло-серый": 0,
        "светло-оранжевый": None,  # ореховый или сливочный — уточняем по тегам
        "светло-коричневый": 2,
        "светло-розовый": 4,
        "светло-желтый": 5,
        "светло-зеленый": 6,
    }
    present = set(flavors or [])
    for idx, group in enumerate(TASTE_GROUP_ORDER):
        if present.intersection(group):
            return idx
    # оранжевый без тегов → группа ореховых (1)
    if color_key == "светло-оранжевый":
        return 1
    mapped = color_to_group.get(color_key)
    if mapped is not None:
        return mapped
    return 99


def taste_fill_color(flavors: list[str] | None = None, taste_color: str = "") -> tuple[int, int, int]:
    color_key = (taste_color or "").strip().lower().replace("ё", "е")
    if color_key in TASTE_COLOR_NAME_FILLS:
        return TASTE_COLOR_NAME_FILLS[color_key]
    present = set(flavors or [])
    for name in FLAVOR_FILL_PRIORITY:
        if name in present:
            return FLAVOR_FILLS[name]
    for name in flavors or []:
        if name in FLAVOR_FILLS:
            return FLAVOR_FILLS[name]
    return DEFAULT_TASTE_FILL


def sort_teas_for_catalog(teas: list[dict]) -> list[dict]:
    def key(tea: dict):
        flavors, _ = split_taste_tags(tea.get("tags") or [])
        group = taste_group_index(flavors, str(tea.get("tasteColor") or ""))
        article = str(tea.get("article") or "")
        name = str(tea.get("name") or "")
        return (group, article, name)

    return sorted(teas, key=key)


def format_best_time(value) -> str:
    text = join_list(value)
    if not text:
        return ""
    # «Утро, День» → «Утро / день»
    parts = [p.strip() for p in text.replace("/", ",").split(",") if p.strip()]
    if not parts:
        return text
    out = [parts[0]]
    out.extend(p.lower() for p in parts[1:])
    return " / ".join(out)


# Универсальный рецепт проливов (если в данных пусто)
DEFAULT_BREW_DOSE = "5–7г/100–120мл"
DEFAULT_BREW_TEMP = "95–98°C"
DEFAULT_BREW_TEMP_SHENG = "85–90°C"
DEFAULT_BREW_TIME = "10…15 сек"
DEFAULT_BREW_STEEPS = "6–8"


def is_sheng(tea: dict) -> bool:
    cat = str(tea.get("category") or "").lower()
    name = str(tea.get("name") or "").lower()
    article = str(tea.get("article") or "").upper()
    return "шен" in cat or "шен" in name or article.startswith("ПЕ-")


def brew_value(tea: dict, key: str) -> str:
    """Значение для иконок проливов; пустое → универсальный рецепт (не прочерк)."""
    value = str(tea.get(key) or "").strip()
    if value and value != "—":
        return value
    if key == "brewDose":
        return DEFAULT_BREW_DOSE
    if key == "brewTemp":
        return DEFAULT_BREW_TEMP_SHENG if is_sheng(tea) else DEFAULT_BREW_TEMP
    if key == "brewTime":
        return DEFAULT_BREW_TIME
    if key == "brewSteeps":
        return DEFAULT_BREW_STEEPS
    return "—"


def thermos_status(tea: dict) -> tuple[str, tuple[int, int, int]]:
    label = str(tea.get("thermosLabel") or "").strip()
    fit = str(tea.get("thermosFit") or "").strip().lower()
    if not label:
        label = "Да" if tea.get("forThermos") else "Нет"
    color = THERMOS_COLORS.get(fit, (90, 95, 85))
    return label, color


def resolve_image(tea: dict) -> Path | None:
    image = str(tea.get("image") or "").strip()
    if not image:
        return None
    path = IMAGES_DIR / Path(image).name
    return path if path.exists() else None


def _round_corners_rgba(img: Image.Image, radius_px: int) -> Image.Image:
    """Скругление углов фото (PNG с прозрачностью)."""
    img = img.convert("RGBA")
    w, h = img.size
    radius_px = max(1, min(radius_px, w // 2, h // 2))
    mask = Image.new("L", (w, h), 0)
    from PIL import ImageDraw

    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius_px, fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(img, (0, 0))
    out.putalpha(mask)
    return out


def prepare_image(
    src: Path,
    max_w_mm: float,
    max_h_mm: float,
    dpi: int = 160,
    corner_radius_mm: float = 2.5,
) -> tuple[Path, float, float]:
    img = Image.open(src).convert("RGB")
    max_w_px = int(max_w_mm / 25.4 * dpi)
    max_h_px = int(max_h_mm / 25.4 * dpi)
    img.thumbnail((max_w_px, max_h_px), Image.Resampling.LANCZOS)
    w_mm = img.width / dpi * 25.4
    h_mm = img.height / dpi * 25.4
    radius_px = int(corner_radius_mm / 25.4 * dpi)
    rounded = _round_corners_rgba(img, radius_px)
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp_path = Path(tmp.name)
    tmp.close()
    rounded.save(tmp_path, format="PNG", optimize=True)
    return tmp_path, w_mm, h_mm


class TeaCatalogPDF(FPDF):
    def __init__(self) -> None:
        super().__init__(unit="mm", format=(PAGE_W, PAGE_H))
        self.set_auto_page_break(auto=False)
        self.add_font("Catalog", "", str(pick_font(FONT_CANDIDATES)))
        self.add_font("Catalog", "B", str(pick_font(FONT_BOLD_CANDIDATES)))
        try:
            self.add_font("Catalog", "I", str(pick_font(FONT_ITALIC_CANDIDATES)))
            self._has_italic = True
        except FileNotFoundError:
            self._has_italic = False
        self._tmp_files: list[Path] = []

    def soft_rect(self, x: float, y: float, w: float, h: float, r: float = 2.0, style: str = "DF") -> None:
        """Прямоугольник со скруглёнными углами.

        Заливку делаем обычным rect (у rounded fill иногда короче высоты),
        обводку — скруглённой.
        """
        from fpdf.enums import RenderStyle

        style_u = (style or "DF").upper()
        if "F" in style_u:
            self.rect(x, y, w, h, style="F")
        if "D" in style_u:
            self._draw_rounded_rect(x, y, w, h, RenderStyle.D, True, r)

    def cleanup(self) -> None:
        for path in self._tmp_files:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

    def remaining(self) -> float:
        return CONTENT_BOTTOM - self.get_y()

    def _col_text(self, text: str, width: float, x: float, line_h: float = 3.8) -> None:
        """Текст строго в колонке x..x+width (не уезжает под фото)."""
        self.set_x(x)
        self.multi_cell(width, line_h, text)
        self.set_x(x)

    def _taste_table_rows(
        self, flavors: list[str], characters: list[str], best_time
    ) -> list[tuple[str, str, str]]:
        rows: list[tuple[str, str, str]] = []
        taste_text = format_taste_cell(flavors, characters)
        time_text = format_best_time(best_time)
        if taste_text:
            rows.append(("taste", "Вкус", taste_text))
        if time_text:
            rows.append(("time", "Лучшее время", time_text))
        return rows

    def taste_table_height(
        self, flavors: list[str], characters: list[str], best_time, width: float
    ) -> float:
        rows = self._taste_table_rows(flavors, characters, best_time)
        if not rows:
            return 0.0
        label_w = 24.0
        value_w = width - label_w
        row_pad_y = 1.4
        line_h = 3.6
        total = 0.0
        for _, _, value in rows:
            self.set_font("Catalog", "", 7.4)
            lines = self.multi_cell(value_w - 2.4, line_h, value, dry_run=True, output="LINES")
            total += max(line_h, len(lines) * line_h) + row_pad_y * 2
        return total

    def draw_taste_table(
        self,
        flavors: list[str],
        characters: list[str],
        best_time,
        x: float,
        width: float,
        taste_color: str = "",
    ) -> None:
        """Таблица: Вкус (с заливкой) / Лучшее время — только H/V линии сетки."""
        rows = self._taste_table_rows(flavors, characters, best_time)
        if not rows:
            return

        label_w = 24.0
        value_w = width - label_w
        row_pad_y = 1.4
        line_h = 3.6

        row_heights: list[float] = []
        for _, _, value in rows:
            self.set_font("Catalog", "", 7.4)
            lines = self.multi_cell(value_w - 2.4, line_h, value, dry_run=True, output="LINES")
            row_heights.append(max(line_h, len(lines) * line_h) + row_pad_y * 2)

        table_y = self.get_y()
        table_h = sum(row_heights)
        value_x = x + label_w

        self.set_draw_color(*TABLE_LINE)
        self.set_line_width(0.3)
        self.line(value_x, table_y, value_x, table_y + table_h)

        y = table_y
        for idx, (kind, label, value) in enumerate(rows):
            row_h = row_heights[idx]
            if kind == "taste":
                self.set_fill_color(*taste_fill_color(flavors, taste_color))
                self.soft_rect(value_x, y, value_w, row_h, r=1.2, style="F")

            self.set_xy(x, y + (row_h - 3.2) / 2)
            self.set_font("Catalog", "", 7.5)
            self.set_text_color(35, 40, 32)
            self.cell(label_w - 1.0, 3.2, label)

            self.set_xy(value_x + 1.2, y + row_pad_y)
            self.set_font("Catalog", "", 7.4)
            self.set_text_color(35, 40, 32)
            self.multi_cell(value_w - 2.4, line_h, value)

            y += row_h
            if idx < len(rows) - 1:
                self.set_draw_color(*TABLE_LINE)
                self.line(x, y, x + width, y)

        self.set_line_width(0.2)
        self.set_y(table_y + table_h)
        self.set_x(x)
        self.set_text_color(35, 40, 32)

    def brew_chars_height(self, tea: dict) -> float:
        """Высота блока иконок + термоса (без отрисовки)."""
        h = 6.2 + 4.2  # иконки + подписи
        if not tea.get("forProliv"):
            h += 3.6
        h += 0.6 + 5.5 + 1.2  # строка термоса
        return h

    def draw_brew_chars(self, tea: dict, x: float, width: float) -> None:
        """Ряд иконок проливов + отдельная строка термоса."""
        muted = not tea.get("forProliv")
        label_rgb = (150, 150, 145) if muted else (55, 58, 52)

        items = [
            ("dose", brew_value(tea, "brewDose")),
            ("temp", brew_value(tea, "brewTemp")),
            ("time", brew_value(tea, "brewTime")),
            ("steeps", brew_value(tea, "brewSteeps")),
        ]
        n = len(items)
        gap = 1.2
        cell_w = (width - gap * (n - 1)) / n
        icon_size = 6.2
        y0 = self.get_y()

        for i, (icon_name, value) in enumerate(items):
            cx = x + i * (cell_w + gap)
            icon_path = ICONS_DIR / f"{icon_name}.png"
            ix = cx + (cell_w - icon_size) / 2
            if icon_path.exists():
                self.image(str(icon_path), x=ix, y=y0, w=icon_size, h=icon_size)
            self.set_xy(cx, y0 + icon_size + 0.8)
            self.set_font("Catalog", "", 6.2)
            self.set_text_color(*label_rgb)
            display = value
            if len(display) > 12:
                self.set_font("Catalog", "", 5.5)
            self.cell(cell_w, 3.0, display, align="C")

        self.set_y(y0 + icon_size + 4.2)
        self.set_x(x)

        if muted:
            self.set_font("Catalog", "", 6.5)
            self.set_text_color(140, 140, 135)
            self._col_text("Не для проливов", width, x, 3.0)
            self.ln(0.6)
            self.set_x(x)

        thermos_icon = ICONS_DIR / "thermos.png"
        label, color = thermos_status(tea)
        row_y = self.get_y() + 0.6
        t_icon = 5.5
        if thermos_icon.exists():
            self.image(str(thermos_icon), x=x, y=row_y, w=t_icon, h=t_icon)
        self.set_xy(x + t_icon + 1.5, row_y + 0.6)
        self.set_font("Catalog", "B", 7.5)
        self.set_text_color(*color)
        self.cell(width - t_icon - 1.5, 4.0, f"Термос / {label}")
        self.set_y(row_y + t_icon + 1.2)
        self.set_x(x)
        self.set_text_color(35, 40, 32)

    def draw_boxed_section(self, label: str, text: str, size: float = 8.2) -> None:
        """Блок в рамке, как в карточке приложения."""
        text = (text or "").strip()
        if not text or self.remaining() < 12:
            return

        pad = 2.2
        label_h = 3.6
        body_size = size
        if len(text) > 480 and self.remaining() < 40:
            body_size = 7.4

        # Оценка высоты текста
        self.set_font("Catalog", "", body_size)
        lines = self.multi_cell(CONTENT_W - 2 * pad, 3.5, text, dry_run=True, output="LINES")
        body_h = max(3.5, len(lines) * 3.5)
        box_h = pad + label_h + body_h + pad

        if box_h > self.remaining():
            # ужимаем шрифт ещё раз
            body_size = 7.0
            self.set_font("Catalog", "", body_size)
            lines = self.multi_cell(CONTENT_W - 2 * pad, 3.3, text, dry_run=True, output="LINES")
            body_h = max(3.3, len(lines) * 3.3)
            box_h = pad + label_h + body_h + pad
            if box_h > self.remaining():
                # обрезаем мягко по доступной высоте
                max_lines = max(2, int((self.remaining() - pad - label_h - pad) / 3.3))
                text = "\n".join(lines[:max_lines])
                if len(lines) > max_lines:
                    text = text.rstrip(" .,;") + "…"
                body_h = max_lines * 3.3
                box_h = pad + label_h + body_h + pad

        x = MARGIN_X
        y = self.get_y()
        self.set_draw_color(210, 200, 185)
        self.set_fill_color(255, 252, 248)
        self.soft_rect(x, y, CONTENT_W, box_h, r=2.0, style="DF")

        self.set_xy(x + pad, y + pad * 0.7)
        self.set_font("Catalog", "B", 7)
        self.set_text_color(95, 105, 90)
        self.cell(CONTENT_W - 2 * pad, label_h, label.upper(), new_x="LEFT", new_y="NEXT")

        self.set_x(x + pad)
        self.set_font("Catalog", "", body_size)
        self.set_text_color(35, 40, 32)
        self.multi_cell(CONTENT_W - 2 * pad, 3.5 if body_size >= 8 else 3.3, text)

        self.set_y(y + box_h + 2.0)
        self.set_x(MARGIN_X)

    def add_tea_page(self, tea: dict, index: int, total: int) -> None:
        self.add_page()
        self.set_left_margin(MARGIN_X)
        self.set_right_margin(MARGIN_X)
        self.set_y(MARGIN_TOP)
        self.set_x(MARGIN_X)

        article = str(tea.get("article") or "").strip() or "—"

        # Шапка
        self.set_font("Catalog", "B", 8.5)
        self.set_text_color(61, 92, 58)
        self.cell(CONTENT_W * 0.55, 4, article, align="L")
        self.cell(CONTENT_W * 0.45, 4, f"{index} / {total}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(205, 196, 178)
        line_y = self.get_y() + 0.6
        self.line(MARGIN_X, line_y, PAGE_W - MARGIN_X, line_y)
        self.set_y(line_y + 2.2)
        self.set_text_color(35, 40, 32)

        top_y = self.get_y()
        photo_bottom = top_y
        right_x = MARGIN_X + PHOTO_W + PHOTO_GAP

        # ---- Фото слева (фиксированная колонка) ----
        image_path = resolve_image(tea)
        if image_path:
            try:
                tmp, w_mm, h_mm = prepare_image(image_path, PHOTO_W - 0.5, 72, corner_radius_mm=2.5)
                self._tmp_files.append(tmp)
                # мягкая рамка под фото
                self.set_draw_color(210, 200, 185)
                self.set_fill_color(247, 243, 234)
                self.soft_rect(MARGIN_X, top_y, PHOTO_W, h_mm + 1.5, r=2.5, style="DF")
                self.image(str(tmp), x=MARGIN_X + (PHOTO_W - w_mm) / 2, y=top_y + 0.75, w=w_mm, h=h_mm)
                photo_bottom = top_y + h_mm + 1.5
            except Exception:  # noqa: BLE001
                self.set_xy(MARGIN_X, top_y)
                self.set_font("Catalog", "", 7.5)
                self.set_text_color(140, 100, 90)
                self.multi_cell(PHOTO_W, 4, "[нет фото]")
                photo_bottom = self.get_y()
                self.set_text_color(35, 40, 32)

        # ---- Правая колонка: временно сужаем left margin ----
        old_left = self.l_margin
        old_right = self.r_margin
        self.set_left_margin(right_x)
        self.set_right_margin(MARGIN_X)
        self.set_xy(right_x, top_y)

        name = str(tea.get("name") or "").strip() or "Без названия"
        self.set_font("Catalog", "B", 11)
        self.set_text_color(35, 40, 32)
        self._col_text(name, RIGHT_W, right_x, 4.4)
        self.ln(0.8)
        self.set_x(right_x)

        self.set_font("Catalog", "", 9)
        self.set_text_color(110, 115, 105)
        self._col_text(article, RIGHT_W, right_x, 3.8)
        self.ln(0.6)
        self.set_x(right_x)

        category = str(tea.get("category") or "").strip()
        if category:
            self.set_font("Catalog", "", 7.5)
            self.set_text_color(100, 110, 90)
            self._col_text(category, RIGHT_W, right_x, 3.3)
            self.ln(1.2)
            self.set_x(right_x)

        # Иконки сразу под шапкой; таблицу вкуса — к низу фото (единый блок)
        flavors, characters = split_taste_tags(tea.get("tags") or [])
        brew_h = self.brew_chars_height(tea)
        table_h = self.taste_table_height(flavors, characters, tea.get("bestTime"), RIGHT_W)
        min_gap = 2.0

        self.ln(min_gap)
        self.set_x(right_x)
        brew_top = self.get_y()
        self.draw_brew_chars(tea, right_x, RIGHT_W)

        if photo_bottom > top_y and table_h > 0:
            table_top = photo_bottom - table_h
            if table_top < brew_top + brew_h + min_gap:
                table_top = brew_top + brew_h + min_gap
            self.set_xy(right_x, table_top)
        else:
            self.ln(min_gap)
            self.set_x(right_x)

        self.draw_taste_table(
            flavors,
            characters,
            tea.get("bestTime"),
            right_x,
            RIGHT_W,
            str(tea.get("tasteColor") or ""),
        )

        right_bottom = self.get_y()

        # возвращаем поля страницы
        self.set_left_margin(old_left)
        self.set_right_margin(old_right)
        self.set_x(MARGIN_X)
        self.set_y(max(photo_bottom, right_bottom) + 3.5)

        # ---- Нижние блоки в рамках ----
        self.draw_boxed_section("Описание", str(tea.get("description") or ""))
        self.draw_boxed_section("Вкус", join_list(tea.get("taste")))
        self.draw_boxed_section("Аромат", join_list(tea.get("aroma")))

        effect_parts = []
        if tea.get("effectDescription"):
            effect_parts.append(str(tea["effectDescription"]).strip())
        effect_tags = join_list(tea.get("effect"))
        if effect_tags:
            effect_parts.append(effect_tags)
        self.draw_boxed_section("Эффект", "\n".join(effect_parts))
        self.draw_boxed_section("Правила заваривания", str(tea.get("brewingGuide") or ""), size=7.8)

    def _page_header(self, left: str, right: str = "") -> None:
        self.set_font("Catalog", "B", 8.5)
        self.set_text_color(61, 92, 58)
        self.cell(CONTENT_W * 0.55, 4, left, align="L")
        self.cell(CONTENT_W * 0.45, 4, right, align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(205, 196, 178)
        line_y = self.get_y() + 0.6
        self.line(MARGIN_X, line_y, PAGE_W - MARGIN_X, line_y)
        self.set_y(line_y + 2.5)
        self.set_text_color(35, 40, 32)

    def estimate_rich_height(
        self,
        parts: list[tuple[str, bool]],
        width: float,
        line_h: float = 4.0,
        size: float = 8.6,
    ) -> float:
        """Оценка высоты rich-текста (с учётом размера шрифта)."""
        plain = rich_parts_to_plain(parts)
        if not plain:
            return line_h
        if self.page == 0:
            self.add_page()
        # bold чуть шире — считаем по bold, чтобы не занижать число строк
        has_bold = any(b for _, b in parts if b)
        self.set_font("Catalog", "B" if has_bold else "", size)
        lines = self.multi_cell(width, line_h, plain, dry_run=True, output="LINES")
        extra = plain.count("\n") * (line_h * 0.2)
        return max(line_h, len(lines) * line_h + extra)

    def draw_rich_text(
        self,
        parts: list[tuple[str, bool]],
        width: float,
        line_h: float = 4.0,
        size: float = 8.6,
    ) -> None:
        """Печать текста с <br> (перевод строки) и жирным выделением."""
        x0 = self.get_x()
        y_limit = CONTENT_BOTTOM - 1
        old_l = self.l_margin
        old_r = self.r_margin
        # write() после переноса возвращается к l_margin — фиксируем колонку
        self.set_left_margin(x0)
        self.set_right_margin(max(MARGIN_X, PAGE_W - (x0 + width)))
        self.set_x(x0)
        self.set_text_color(35, 40, 32)
        try:
            for text, bold in parts:
                if self.get_y() > y_limit:
                    break
                if text == "\n":
                    self.ln(line_h * 0.95)
                    self.set_x(x0)
                    continue
                if not text:
                    continue
                self.set_font("Catalog", "B" if bold else "", size)
                self.write(line_h, text)
        finally:
            self.set_left_margin(old_l)
            self.set_right_margin(old_r)
            self.set_x(old_l)

    def draw_rich_box(
        self,
        parts: list[tuple[str, bool]],
        x: float,
        y: float,
        width: float,
        pad: float = 2.5,
        line_h: float = 4.0,
        size: float = 8.6,
        fixed_h: float | None = None,
    ) -> float:
        """Мягкий блок с rich-текстом. Возвращает Y после блока.

        fixed_h — зафиксировать высоту (боковая колонка = высота фото).
        Без fixed_h блок расширяется по тексту с запасом.
        """
        if not parts:
            return y
        inner_w = width - 2 * pad
        text_h = self.estimate_rich_height(parts, inner_w, line_h, size=size)
        self.set_fill_color(255, 250, 240)
        self.set_draw_color(210, 195, 160)

        if fixed_h is not None:
            # боковой блок: высота строго = фото
            self.soft_rect(x, y, width, fixed_h, r=2.0, style="DF")
            self.set_xy(x + pad, y + pad)
            self.draw_rich_text(parts, inner_w, line_h=line_h, size=size)
            return y + fixed_h

        # нижний блок: одна рамка по оценке, при нехватке — только расширяем
        box_h = min(CONTENT_BOTTOM - y, pad * 2 + text_h + line_h * 1.15)
        box_h = max(box_h, pad * 2 + line_h)
        self.soft_rect(x, y, width, box_h, r=2.0, style="DF")
        self.set_xy(x + pad, y + pad)
        self.draw_rich_text(parts, inner_w, line_h=line_h, size=size)
        y_after = self.get_y()
        needed_h = (y_after - y) + pad + line_h
        needed_h = min(CONTENT_BOTTOM - y, max(needed_h, pad * 2 + line_h))
        if needed_h > box_h + 0.4:
            self.set_fill_color(255, 250, 240)
            self.set_draw_color(210, 195, 160)
            self.soft_rect(x, y, width, needed_h, r=2.0, style="DF")
            self.set_xy(x + pad, y + pad)
            self.draw_rich_text(parts, inner_w, line_h=line_h, size=size)
            return y + needed_h
        return y + box_h

    def add_fact_page(
        self,
        fact: dict,
        tea: dict | None,
        index: int,
        total: int,
    ) -> None:
        """Страница «Интересный факт» со свитком и фото блина."""
        self.add_page()
        self.set_left_margin(MARGIN_X)
        self.set_right_margin(MARGIN_X)
        self.set_y(MARGIN_TOP)
        self.set_x(MARGIN_X)

        article = str(fact.get("article") or "").strip()
        self._page_header("Интересный факт")

        scroll = ICONS_DIR / "scroll.png"
        icon_y = self.get_y()
        if scroll.exists():
            self.image(str(scroll), x=MARGIN_X, y=icon_y, w=12, h=12)
        self.set_xy(MARGIN_X + 14, icon_y + 2)
        self.set_font("Catalog", "B", 14)
        self.set_text_color(90, 70, 40)
        self.cell(CONTENT_W - 14, 8, "Интересный факт")
        self.set_y(icon_y + 14)

        name = str(fact.get("name") or (tea or {}).get("name") or "").strip()
        self.set_font("Catalog", "B", 10)
        self.set_text_color(35, 40, 32)
        self.multi_cell(CONTENT_W, 4.5, name)
        self.ln(0.5)
        if article:
            self.set_font("Catalog", "", 9)
            self.set_text_color(110, 115, 105)
            self.cell(CONTENT_W, 4, article, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        top_y = self.get_y()
        photo_h = 0.0
        photo_w = 48.0
        gap = 4.0
        image_path = resolve_image(tea) if tea else None
        if image_path:
            try:
                tmp, w_mm, h_mm = prepare_image(image_path, photo_w - 0.5, 54, corner_radius_mm=2.5)
                self._tmp_files.append(tmp)
                self.set_draw_color(210, 200, 185)
                self.set_fill_color(247, 243, 234)
                self.soft_rect(MARGIN_X, top_y, photo_w, h_mm + 1.5, r=2.5, style="DF")
                self.image(
                    str(tmp),
                    x=MARGIN_X + (photo_w - w_mm) / 2,
                    y=top_y + 0.75,
                    w=w_mm,
                    h=h_mm,
                )
                photo_h = h_mm + 1.5
            except Exception:  # noqa: BLE001
                photo_h = 0.0

        parts = fact.get("parts") or plain_to_rich_parts(str(fact.get("fact") or ""))
        fact_size = 9.8
        fact_lh = 4.5
        pad_side = 2.2
        pad_bottom = 2.5

        if photo_h:
            text_x = MARGIN_X + photo_w + gap
            text_w = CONTENT_W - photo_w - gap
            # боковой блок = высота фото; невлезающие предложения целиком вниз
            avail_text_h = max(fact_lh, photo_h - 2 * pad_side - 1.0)
            side_parts, rest_parts = split_rich_parts_by_sentences(
                self,
                parts,
                text_w - 2 * pad_side,
                avail_text_h,
                line_h=fact_lh,
                size=fact_size,
            )
            if side_parts:
                self.draw_rich_box(
                    side_parts,
                    text_x,
                    top_y,
                    text_w,
                    pad=pad_side,
                    line_h=fact_lh,
                    size=fact_size,
                    fixed_h=photo_h,
                )
            below_y = top_y + photo_h + 3.0
            if rest_parts and below_y < CONTENT_BOTTOM - 10:
                self.draw_rich_box(
                    rest_parts,
                    MARGIN_X,
                    below_y,
                    CONTENT_W,
                    pad=pad_bottom,
                    line_h=fact_lh,
                    size=fact_size,
                )
        else:
            self.draw_rich_box(
                parts, MARGIN_X, top_y, CONTENT_W, pad=pad_bottom, line_h=fact_lh, size=fact_size
            )

    def add_cover_page(self) -> None:
        """Обложка каталога: логотип, цитата, заголовок."""
        self.add_page()
        self.set_left_margin(MARGIN_X)
        self.set_right_margin(MARGIN_X)

        # Логотип сверху по центру — крупнее, чем в макете-скриншоте
        logo_w = 118.0
        if LOGO_MAIN.exists():
            with Image.open(LOGO_MAIN) as im:
                lw, lh = im.size
            logo_h = logo_w * (lh / lw)
            logo_x = (PAGE_W - logo_w) / 2
            logo_y = MARGIN_TOP + 6
            self.image(str(LOGO_MAIN), x=logo_x, y=logo_y, w=logo_w, h=logo_h)
            quote_top = logo_y + logo_h + 14
        else:
            quote_top = MARGIN_TOP + 40

        # Цитата — справа, курсив
        quote_w = CONTENT_W * 0.88
        quote_x = MARGIN_X + (CONTENT_W - quote_w)
        self.set_xy(quote_x, quote_top)
        if self._has_italic:
            self.set_font("Catalog", "I", 9.5)
        else:
            self.set_font("Catalog", "", 9.5)
        self.set_text_color(40, 55, 40)
        self.multi_cell(quote_w, 5.0, COVER_QUOTE, align="R")

        self.ln(4)
        self.set_x(quote_x)
        if self._has_italic:
            self.set_font("Catalog", "I", 9)
        else:
            self.set_font("Catalog", "", 9)
        self.set_text_color(55, 70, 55)
        self.multi_cell(quote_w, 4.5, COVER_QUOTE_ATTR, align="R")

        # Заголовок в нижней трети
        title_y = PAGE_H * 0.62
        self.set_xy(MARGIN_X, title_y)
        self.set_font("Catalog", "B", 36)
        self.set_text_color(*COVER_GREEN)
        self.cell(CONTENT_W, 14, COVER_TITLE, align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Catalog", "", 20)
        self.cell(CONTENT_W, 10, COVER_SUBTITLE, align="C")

    def add_brewing_rules_page(self, rules_parts: list[tuple[str, bool]]) -> None:
        """Страница общих правил заваривания с чайником."""
        self.add_page()
        self.set_left_margin(MARGIN_X)
        self.set_right_margin(MARGIN_X)
        self.set_y(MARGIN_TOP)
        self.set_x(MARGIN_X)

        self._page_header("Правила заваривания")

        teapot = ICONS_DIR / "teapot.png"
        icon_y = self.get_y()
        if teapot.exists():
            self.image(str(teapot), x=MARGIN_X + CONTENT_W / 2 - 14, y=icon_y, w=28, h=28)
            self.set_y(icon_y + 30)
        else:
            self.ln(2)

        self.set_font("Catalog", "B", 13)
        self.set_text_color(90, 70, 40)
        self.cell(CONTENT_W, 7, "Как правильно заваривать", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Catalog", "", 9)
        self.set_text_color(110, 100, 85)
        self.cell(CONTENT_W, 5, "методом проливов", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

        # убираем дублирующий заголовок из начала rich-текста
        parts = strip_leading_title(rules_parts, "как правильно заваривать")
        self.draw_rich_box(parts, MARGIN_X, self.get_y(), CONTENT_W, pad=3.0, line_h=4.3, size=9.0)

    def add_matrix_page(self, table: dict) -> None:
        """Матрица на портретном A5: таблица повёрнута, печать как у всего каталога.

        Страница 152×214 как остальные. Широкая таблица лежит «горизонтально»
        (повёрнута на 90°): при чтении лист поворачивают, на принтер — тот же A5.
        Левый край таблицы (в чтении) = верх страницы под сшивку 15 мм.
        """
        self.add_page()  # тот же портрет A5

        # Координаты «чтения» таблицы: ширина = высота страницы, высота = ширина
        land_w, land_h = PAGE_H, PAGE_W  # 214 × 152
        m_left = MARGIN_TOP  # сшивка — физический верх страницы
        m_right = MARGIN_BOTTOM
        m_top = MARGIN_X
        m_bottom = MARGIN_X
        content_w = land_w - m_left - m_right
        content_h = land_h - m_top - m_bottom

        rows: list[list[dict]] = table.get("rows") or []
        if not rows:
            return
        n_cols = max(len(r) for r in rows)
        if n_cols == 3:
            col_ws = [content_w * 0.20, content_w * 0.28, content_w * 0.52]
        elif n_cols == 4:
            col_ws = [content_w * 0.27, content_w * 0.29, content_w * 0.24, content_w * 0.20]
        else:
            first = content_w * 0.11
            rest = (content_w - first) / max(n_cols - 1, 1)
            col_ws = [first] + [rest] * (n_cols - 1)

        is_taste = bool(table.get("is_taste"))
        font_size = 5.8 if is_taste else (6.5 if n_cols == 3 else 7.2)
        line_h = 2.45 if is_taste else 2.85
        title_h = 7.0
        start_y = m_top + title_h
        avail_h = content_h - title_h - 1

        def measure_row_h(row: list[dict], header: bool) -> float:
            self.set_font("Catalog", "B" if header else "", font_size)
            needed = line_h + 1.4
            for ci in range(n_cols):
                cell = row[ci] if ci < len(row) else {"text": ""}
                text = str(cell.get("text") or "").strip()
                if not text:
                    continue
                tw = col_ws[ci] - 2.0
                lines = self.multi_cell(tw, line_h, text, dry_run=True, output="LINES")
                h = len(lines) * line_h + 1.4
                if h > needed:
                    needed = h
            return needed

        heights = [measure_row_h(row, ri == 0) for ri, row in enumerate(rows)]
        total_h = sum(heights)
        if total_h > avail_h and total_h > 0:
            scale = avail_h / total_h
            heights = [max(4.0, h * scale) for h in heights]
            if scale < 0.85:
                font_size = max(5.0, font_size - 0.8)
                line_h = max(2.2, line_h - 0.3)

        # (lx, ly) → портрет (PAGE_W - ly, lx): чтение после поворота листа по часовой
        land_to_page = Transform(0, 1, -1, 0, PAGE_W, 0)
        with self.transform(land_to_page):
            title = str(table.get("title") or "Матрица выбора")
            self.set_font("Catalog", "B", 12)
            self.set_text_color(61, 92, 58)
            self.set_xy(m_left, m_top)
            self.cell(content_w, title_h - 1.0, title)
            self.set_text_color(35, 40, 32)

            y = start_y
            for ri, row in enumerate(rows):
                row_h = heights[ri]
                is_header = ri == 0
                x = m_left
                for ci in range(n_cols):
                    cell = row[ci] if ci < len(row) else {"text": "", "fill": None}
                    text = str(cell.get("text") or "").strip()
                    fill = cell.get("fill")
                    cw = col_ws[ci]

                    if fill:
                        self.set_fill_color(*fill)
                        self.rect(x, y, cw, row_h, style="F")
                    self.set_draw_color(180, 180, 180)
                    self.set_line_width(0.2)
                    self.rect(x, y, cw, row_h, style="D")

                    self.set_xy(x + 1.0, y + 0.6)
                    self.set_font("Catalog", "B" if is_header else "", font_size)
                    self.set_text_color(35, 40, 32)
                    self.multi_cell(cw - 2.0, line_h, text)
                    x += cw
                y += row_h


# Тема Excel: bg1, tx1, bg2, tx2, accent1..accent6
_THEME_SCHEME_ORDER = (
    "lt1",
    "dk1",
    "lt2",
    "dk2",
    "accent1",
    "accent2",
    "accent3",
    "accent4",
    "accent5",
    "accent6",
)


def _workbook_theme_rgbs(wb) -> list[tuple[int, int, int]]:
    """Базовые RGB темы книги (10 слотов)."""
    defaults = [
        (255, 255, 255),
        (0, 0, 0),
        (231, 230, 230),
        (68, 84, 106),
        (68, 114, 196),
        (237, 125, 49),
        (165, 165, 165),
        (255, 192, 0),
        (91, 155, 213),
        (112, 173, 71),
    ]
    if not getattr(wb, "loaded_theme", None):
        return defaults
    try:
        from openpyxl.xml.functions import fromstring

        root = fromstring(wb.loaded_theme)
        ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
        scheme = root.find(".//a:clrScheme", ns)
        if scheme is None:
            return defaults
        by_name: dict[str, tuple[int, int, int]] = {}
        for el in list(scheme):
            name = el.tag.split("}")[-1]
            srgb = el.find("a:srgbClr", ns)
            sys = el.find("a:sysClr", ns)
            hexv = None
            if srgb is not None:
                hexv = srgb.get("val")
            elif sys is not None:
                hexv = sys.get("lastClr")
            if hexv and len(hexv) == 6:
                by_name[name] = (
                    int(hexv[0:2], 16),
                    int(hexv[2:4], 16),
                    int(hexv[4:6], 16),
                )
        return [by_name.get(n, defaults[i]) for i, n in enumerate(_THEME_SCHEME_ORDER)]
    except Exception:
        return defaults


def _apply_excel_tint(rgb: tuple[int, int, int], tint: float) -> tuple[int, int, int]:
    if not tint:
        return rgb
    r, g, b = rgb
    if tint < 0:
        f = 1.0 + float(tint)
        return (int(r * f), int(g * f), int(b * f))
    t = float(tint)
    return (
        int(r + (255 - r) * t),
        int(g + (255 - g) * t),
        int(b + (255 - b) * t),
    )


def _parse_excel_rgb(rgb_val) -> tuple[int, int, int] | None:
    if not rgb_val:
        return None
    s = str(rgb_val).strip()
    if s in ("00000000", "None"):
        return None
    if len(s) == 8:  # AARRGGBB
        s = s[2:]
    if len(s) != 6:
        return None
    try:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    except ValueError:
        return None


def _cell_fill_rgb(cell, theme_rgbs: list[tuple[int, int, int]] | None = None) -> tuple[int, int, int] | None:
    fill = cell.fill
    if not fill or not fill.fill_type:
        return None
    fg = fill.fgColor
    if not fg:
        return None
    tint = float(getattr(fg, "tint", 0) or 0)
    if fg.type == "rgb":
        base = _parse_excel_rgb(fg.rgb)
        return _apply_excel_tint(base, tint) if base else None
    if fg.type == "theme" and theme_rgbs is not None:
        idx = fg.theme
        if idx is None or idx < 0 or idx >= len(theme_rgbs):
            return None
        return _apply_excel_tint(theme_rgbs[idx], tint)
    return None


def load_matrix_tables() -> list[dict]:
    """Читает 3 таблицы из matrica_tea.xlsx."""
    if not MATRIX_XLSX.exists():
        return []
    wb = load_workbook(MATRIX_XLSX, data_only=False)
    ws = wb[wb.sheetnames[0]]
    theme_rgbs = _workbook_theme_rgbs(wb)

    blocks: list[list[int]] = []
    current: list[int] = []
    for r in range(1, ws.max_row + 1):
        has_val = any(ws.cell(r, c).value not in (None, "") for c in range(1, ws.max_column + 1))
        if has_val:
            current.append(r)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)

    titles = [
        "Выбор по задаче",
        "Что выбирает человек",
        "Вкус / Характер",
    ]
    tables: list[dict] = []
    for bi, row_nums in enumerate(blocks[:3]):
        is_taste = bi == 2
        rows_data: list[list[dict]] = []

        # число колонок по шапке
        header_row = row_nums[0]
        n_cols = 0
        for c in range(1, ws.max_column + 1):
            if ws.cell(header_row, c).value not in (None, ""):
                n_cols = c
        if is_taste:
            n_cols = max(n_cols, 8)

        for r in row_nums:
            texts = [
                ("" if ws.cell(r, c).value is None else str(ws.cell(r, c).value).strip())
                for c in range(1, n_cols + 1)
            ]
            # пропуск полностью пустых строк (и «пустой» строки вкуса)
            if not any(texts):
                continue
            if is_taste and r != header_row and not any(texts[1:]):
                continue

            row_cells: list[dict] = []
            for c in range(1, n_cols + 1):
                cell = ws.cell(r, c)
                text = texts[c - 1]
                fill = _cell_fill_rgb(cell, theme_rgbs)
                row_cells.append({"text": text, "fill": fill})

            if not is_taste:
                # таблицы 1–2: заливка только у шапки и первого столбца
                for ci, cell in enumerate(row_cells):
                    if r == header_row or ci == 0:
                        if not cell["fill"]:
                            cell["fill"] = (226, 238, 218)  # светло-зелёный fallback
                    else:
                        cell["fill"] = None
            # таблица 3: заливки из файла как есть

            rows_data.append(row_cells)

        tables.append(
            {
                "title": titles[bi] if bi < len(titles) else f"Матрица {bi + 1}",
                "rows": rows_data,
                "is_taste": is_taste,
            }
        )
    return tables


def clean_extra_text(text: str) -> str:
    """Убрать эмодзи, заменить <br> на перевод строки."""
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(
        r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U0001F1E0-\U0001F1FF]",
        "",
        text,
    )
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def rich_parts_to_plain(parts: list[tuple[str, bool]]) -> str:
    chunks: list[str] = []
    for text, _bold in parts:
        chunks.append("\n" if text == "\n" else text)
    plain = "".join(chunks)
    plain = re.sub(r"\n{3,}", "\n\n", plain)
    return plain.strip()


def plain_to_rich_parts(text: str) -> list[tuple[str, bool]]:
    text = clean_extra_text(text)
    if not text:
        return []
    parts: list[tuple[str, bool]] = []
    for i, chunk in enumerate(text.split("\n")):
        if i:
            parts.append(("\n", False))
        if chunk:
            parts.append((chunk, False))
    return parts


def cell_to_rich_parts(cell) -> list[tuple[str, bool]]:
    """Excel rich text → список (текст|'\\n', bold), с учётом <br>."""
    value = cell.value
    raw_parts: list[tuple[str, bool]] = []
    if isinstance(value, CellRichText):
        for part in value:
            if isinstance(part, TextBlock):
                bold = bool(part.font and part.font.b)
                raw_parts.append((str(part.text or ""), bold))
            else:
                raw_parts.append((str(part or ""), False))
    else:
        raw_parts.append((str(value or ""), False))

    out: list[tuple[str, bool]] = []
    for text, bold in raw_parts:
        text = re.sub(
            r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF\U0001F1E0-\U0001F1FF]",
            "",
            text.replace("\r\n", "\n").replace("\r", "\n"),
        )
        chunks = re.split(r"(<br\s*/?>|\n)", text, flags=re.I)
        for chunk in chunks:
            if not chunk:
                continue
            if chunk == "\n" or re.fullmatch(r"<br\s*/?>", chunk, flags=re.I):
                out.append(("\n", False))
            else:
                # не оставляем ведущие пробелы после перевода строки как «пустоты»
                out.append((chunk, bold))

    # схлопываем подряд идущие \n (макс. 2 = абзац)
    compact: list[tuple[str, bool]] = []
    nl_run = 0
    for text, bold in out:
        if text == "\n":
            nl_run += 1
            if nl_run <= 2:
                compact.append(("\n", False))
            continue
        nl_run = 0
        compact.append((text, bold))
    # trim leading/trailing newlines
    while compact and compact[0][0] == "\n":
        compact.pop(0)
    while compact and compact[-1][0] == "\n":
        compact.pop()
    return compact


def strip_leading_title(parts: list[tuple[str, bool]], title_prefix: str) -> list[tuple[str, bool]]:
    plain = rich_parts_to_plain(parts)
    if plain.lower().startswith(title_prefix.lower()):
        # вырезаем первую строку
        rest = re.sub(r"(?is)^[^\n]*\n?", "", plain, count=1).strip()
        return plain_to_rich_parts(rest) if not any(b for _, b in parts[1:]) else _strip_parts_first_line(parts)
    return parts


def _strip_parts_first_line(parts: list[tuple[str, bool]]) -> list[tuple[str, bool]]:
    out: list[tuple[str, bool]] = []
    skipping = True
    for text, bold in parts:
        if skipping:
            if text == "\n":
                skipping = False
            continue
        out.append((text, bold))
    while out and out[0][0] == "\n":
        out.pop(0)
    return out


def _split_parts_into_paragraphs(
    parts: list[tuple[str, bool]],
) -> list[list[tuple[str, bool]]]:
    """Режет rich-parts на абзацы по переводам строки (<br>)."""
    paragraphs: list[list[tuple[str, bool]]] = []
    current: list[tuple[str, bool]] = []
    for text, bold in parts:
        if text == "\n":
            if current:
                paragraphs.append(current)
                current = []
            continue
        current.append((text, bold))
    if current:
        paragraphs.append(current)
    return paragraphs


def _flatten_units(units: list[list[tuple[str, bool]]], sep: str = "\n") -> list[tuple[str, bool]]:
    out: list[tuple[str, bool]] = []
    for i, unit in enumerate(units):
        if i:
            out.append((sep, False))
        out.extend(unit)
    return out


_SENT_END_RE = re.compile(r'([.!?…]+["»”)\] ]*)(\s+|$)')


def _paragraph_to_sentences(para: list[tuple[str, bool]]) -> list[list[tuple[str, bool]]]:
    """Делит абзац на целые предложения, сохраняя bold."""
    sentences: list[list[tuple[str, bool]]] = []
    buf: list[tuple[str, bool]] = []
    for text, bold in para:
        pos = 0
        for m in _SENT_END_RE.finditer(text):
            end = m.end(1)
            chunk = text[pos:end]
            if chunk:
                buf.append((chunk, bold))
            # конец предложения, если после него пробел/конец или это явный терминатор
            if m.group(2) or end == len(text):
                if buf:
                    sentences.append(buf)
                    buf = []
            pos = m.end()
        rest = text[pos:]
        if rest:
            buf.append((rest, bold))
    if buf:
        sentences.append(buf)
    return sentences or [para]


def _append_sentence(
    dest: list[tuple[str, bool]],
    sentence: list[tuple[str, bool]],
    *,
    new_paragraph: bool,
) -> None:
    if dest:
        dest.append(("\n", False) if new_paragraph else (" ", False))
    dest.extend(sentence)


def split_rich_parts_by_sentences(
    pdf: TeaCatalogPDF,
    parts: list[tuple[str, bool]],
    width: float,
    max_h: float,
    line_h: float = 4.5,
    size: float = 9.8,
) -> tuple[list[tuple[str, bool]], list[tuple[str, bool]]]:
    """В боковую колонку — только целые предложения, полностью влезающие по высоте."""
    if max_h < line_h:
        return [], parts

    paragraphs = _split_parts_into_paragraphs(parts)
    if not paragraphs:
        return [], []

    limit = max_h * 0.85
    side: list[tuple[str, bool]] = []
    rest: list[tuple[str, bool]] = []
    to_rest = False

    for para in paragraphs:
        sentences = _paragraph_to_sentences(para)
        for si, sent in enumerate(sentences):
            if to_rest:
                _append_sentence(rest, sent, new_paragraph=(si == 0 and bool(rest)))
                continue

            trial = list(side)
            _append_sentence(trial, sent, new_paragraph=(si == 0 and bool(side)))
            if pdf.estimate_rich_height(trial, width, line_h, size=size) <= limit:
                _append_sentence(side, sent, new_paragraph=(si == 0 and bool(side)))
                continue

            # предложение целиком уходит вниз
            to_rest = True
            if not side:
                return [], parts
            _append_sentence(rest, sent, new_paragraph=True)
            for sent2 in sentences[si + 1 :]:
                _append_sentence(rest, sent2, new_paragraph=False)
            break

    return side, rest


def load_teas() -> list[dict]:
    if not TEAS_JSON.exists():
        raise FileNotFoundError(f"Не найден файл данных: {TEAS_JSON}")
    data = json.loads(TEAS_JSON.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("teas.json должен содержать массив чаёв")
    return data


def load_facts_and_rules() -> tuple[list[dict], list[tuple[str, bool]]]:
    """Читает Tea_fact.xlsx → факты (с rich-parts) и правила заваривания."""
    if not FACTS_XLSX.exists():
        return [], []
    wb = load_workbook(FACTS_XLSX, data_only=False, rich_text=True)
    ws = wb[wb.sheetnames[0]]
    facts: list[dict] = []
    rules_parts: list[tuple[str, bool]] = []
    for r in range(2, ws.max_row + 1):
        article = str(ws.cell(r, 1).value or "").strip()
        name = str(ws.cell(r, 2).value or "").strip()
        body_cell = ws.cell(r, 3)
        parts = cell_to_rich_parts(body_cell)
        if not parts:
            continue
        plain = rich_parts_to_plain(parts)
        if not article and ("заваривать" in plain.lower() or "пролив" in plain.lower()):
            rules_parts = parts
            continue
        if article:
            facts.append({"article": article, "name": name, "fact": plain, "parts": parts})
    return facts, rules_parts


def main() -> int:
    parser = argparse.ArgumentParser(description="PDF-каталог чаёв A5")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Сгенерировать только 1 страницу для согласования макета",
    )
    parser.add_argument(
        "--article",
        default="ПУ-89",
        help="Артикул для sample-страницы (по умолчанию ПУ-89)",
    )
    args = parser.parse_args()

    try:
        teas = load_teas()
    except Exception as exc:  # noqa: BLE001
        print(exc, file=sys.stderr)
        return 1

    teas = sort_teas_for_catalog(teas)
    teas_by_article = {str(t.get("article") or "").strip(): t for t in teas}

    if args.sample:
        tea = next((t for t in teas if str(t.get("article")) == args.article), None)
        if not tea:
            print(f"Артикул не найден: {args.article}", file=sys.stderr)
            return 1
        pages = [tea]
        out = OUT_SAMPLE
        include_extras = False
    else:
        pages = teas
        out = OUT_PDF
        include_extras = True

    facts, rules_parts = load_facts_and_rules() if include_extras else ([], [])

    pdf = TeaCatalogPDF()
    try:
        if include_extras:
            pdf.add_cover_page()
            print("[обложка]")

        total = len(pages)
        for i, tea in enumerate(pages, start=1):
            pdf.add_tea_page(tea, i, total if not args.sample else 1)
            print(f"[{i}/{total}] {tea.get('article')} — {tea.get('name')}")

        if include_extras:
            fact_total = len(facts)
            for i, fact in enumerate(facts, start=1):
                tea = teas_by_article.get(fact["article"])
                pdf.add_fact_page(fact, tea, i, fact_total)
                print(f"[факт {i}/{fact_total}] {fact['article']}")
            if rules_parts:
                pdf.add_brewing_rules_page(rules_parts)
                print("[правила заваривания]")
            matrices = load_matrix_tables()
            for mi, table in enumerate(matrices, start=1):
                pdf.add_matrix_page(table)
                print(f"[матрица {mi}/{len(matrices)}] {table.get('title')}")

        pdf.output(str(out))
    finally:
        pdf.cleanup()

    print(f"\nГотово: {out}")
    print(f"Формат: {PAGE_W}×{PAGE_H} мм, верх {MARGIN_TOP} мм под сшивку")
    if args.sample:
        print("Это пробная страница. После согласования запустите без --sample.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
