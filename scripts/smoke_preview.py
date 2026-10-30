"""Быстрая проверка production preview: teas.json, logo, изображения."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:4173"
ROOT = Path(__file__).resolve().parents[1]


def fetch(path: str) -> tuple[int | None, bytes]:
    # Кодируем кириллицу в пути (как делают браузеры)
    encoded = urllib.parse.quote(path, safe="/:%")
    try:
        with urllib.request.urlopen(BASE + encoded, timeout=5) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL {path}: {exc}")
        return None, b""


def main() -> int:
    failed = 0

    status, body = fetch("/")
    if status != 200:
        print("FAIL index.html")
        failed += 1
    else:
        print("OK   index.html")

    status, body = fetch("/teas.json")
    if status != 200:
        print("FAIL teas.json")
        failed += 1
        teas = []
    else:
        teas = json.loads(body.decode("utf-8"))
        print(f"OK   teas.json ({len(teas)} records)")

    status, _ = fetch("/logo.svg")
    print(("OK  " if status == 200 else "FAIL") + " logo.svg")
    if status != 200:
        failed += 1

    missing = []
    ok_images = 0
    for tea in teas:
        image = tea.get("image") or ""
        if not image:
            missing.append(f"{tea.get('article')}: empty image")
            continue
        status, _ = fetch(image)
        if status == 200:
            ok_images += 1
        else:
            missing.append(f"{tea.get('article')}: {image} -> {status}")

    print(f"OK   images reachable: {ok_images}/{len(teas)}")
    if missing:
        failed += len(missing)
        print("FAIL missing images:")
        for item in missing[:10]:
            print("  -", item)

    pub_count = len(list((ROOT / "public" / "images" / "tea").glob("*.jpg")))
    dist_count = len(list((ROOT / "dist" / "images" / "tea").glob("*.jpg")))
    print(f"OK   public/images/tea: {pub_count}, dist/images/tea: {dist_count}")
    if pub_count != dist_count:
        print("FAIL image count mismatch between public and dist")
        failed += 1

    # Простая sanity-проверка полей, нужных UI
    if teas:
        sample = teas[0]
        for field in ("id", "article", "name", "tags", "forThermos", "forProliv"):
            if field not in sample:
                print(f"FAIL sample missing field: {field}")
                failed += 1

    if failed:
        print(f"\nSmoke failed: {failed} issue(s)")
        return 1

    print("\nSmoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
