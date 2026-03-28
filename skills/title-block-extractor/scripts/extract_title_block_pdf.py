#!/usr/bin/env python3
"""Extract title block fields from a PDF (OCR-first, heuristic cropping).

Usage:
  python extract_title_block_pdf.py /path/to/file.pdf

Notes:
- OCR via pdftoppm + tesseract; supports chi_sim + eng if tessdata present.
- Heuristic crops: bottom-right for title block, full-page for project/company/notes.
- Keyword mapping is simple; extend via references/field-mapping.md.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path("/Users/taohong/.openclaw/workspace")
TESSDATA = WORKSPACE / "tessdata"
TMP = WORKSPACE / "tmp" / "titleblock"


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)


def ensure_tessdata():
    TMP.mkdir(parents=True, exist_ok=True)
    TESSDATA.mkdir(parents=True, exist_ok=True)
    # best-effort: if missing, use system defaults
    for lang, url in {
        "chi_sim": "https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata",
        "eng": "https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata",
    }.items():
        td = TESSDATA / f"{lang}.traineddata"
        if not td.exists():
            try:
                run(["/usr/bin/curl", "-L", "-o", str(td), url])
            except Exception:
                pass


def pdf_page_size_points(pdf_path: Path):
    info = run(["/usr/local/bin/pdfinfo", str(pdf_path)])
    m = re.search(r"Page size:\s*([0-9.]+) x ([0-9.]+) pts", info)
    if not m:
        raise RuntimeError("Unable to read page size from pdfinfo")
    return float(m.group(1)), float(m.group(2))


def render_crop(pdf_path: Path, out_png: Path, dpi: int, crop):
    x, y, w, h = crop
    run(
        [
            "/usr/local/bin/pdftoppm",
            "-f",
            "1",
            "-l",
            "1",
            "-r",
            str(dpi),
            "-x",
            str(x),
            "-y",
            str(y),
            "-W",
            str(w),
            "-H",
            str(h),
            "-png",
            str(pdf_path),
            str(out_png.with_suffix("")),
        ]
    )
    # pdftoppm writes with -1 suffix
    return out_png.with_name(out_png.stem + "-1.png")


def render_full(pdf_path: Path, out_png: Path, dpi: int):
    run([
        "/usr/local/bin/pdftoppm",
        "-f",
        "1",
        "-l",
        "1",
        "-r",
        str(dpi),
        "-png",
        str(pdf_path),
        str(out_png.with_suffix("")),
    ])
    return out_png.with_name(out_png.stem + "-1.png")


def ocr(png: Path, langs: str = "chi_sim+eng") -> str:
    env = {"TESSDATA_PREFIX": str(TESSDATA)} if TESSDATA.exists() else None
    cmd = ["/usr/local/bin/tesseract", str(png), "stdout", "-l", langs]
    return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, env=env)


def extract_fields(title_text: str, full_text: str):
    def compact(text: str) -> str:
        return re.sub(r"\s+", "", text)

    def find_first(text: str, patterns):
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return (m.group(1) if m.lastindex else m.group(0)).strip()
        return None

    def trim_at_keywords(val: str):
        if not val:
            return val
        for kw in ["说明", "图名", "图号", "日期", "图幅", "比例", "SCALE", "注:", "注："]:
            idx = val.find(kw)
            if idx > 0:
                return val[:idx]
        return val

    t = title_text
    tc = compact(title_text)
    f = full_text
    fc = compact(full_text)

    fields = {}
    fields["project_name"] = trim_at_keywords(
        find_first(fc, [
            r"项目名称[:：]?([^\n]+)",
            r"工程名称[:：]?([^\n]+)",
            r"项目[:：]?([^\n]+)",
        ]) or find_first(f, [
            r"项\s*目\s*名\s*称[:：]?\s*([^\n]+)",
            r"工\s*程\s*名\s*称[:：]?\s*([^\n]+)",
            r"项\s*目[:：]?\s*([^\n]+)",
        ])
    )

    fields["company"] = trim_at_keywords(
        find_first(fc, [
            r"设计单位[:：]?([^\n]+)",
            r"公司[:：]?([^\n]+)",
            r"FutureConceptDesign",
        ]) or find_first(f, [
            r"设\s*计\s*单\s*位[:：]?\s*([^\n]+)",
            r"公\s*司[:：]?\s*([^\n]+)",
            r"Future Concept Design",
        ])
    )

    # title: capture between label and next known label
    m = re.search(r"图\s*名[:：]?\s*(.+?)(图\s*号|日\s*期|图\s*幅|比\s*例|$)", t)
    if m:
        title_raw = m.group(1).strip()
    else:
        title_raw = trim_at_keywords(
            find_first(tc, [
                r"图名[:：]?([^\n]+)",
                r"DrawingTitle[:：]?([^\n]+)",
            ]) or find_first(t, [
                r"图\s*名[:：]?\s*([^\n]+)",
                r"Drawing\s*Title[:：]?\s*([^\n]+)",
            ])
        )

    # drawing no: prefer explicit pattern in compact title text
    drawing_no = find_first(tc, [
        r"图号[:：]?([A-Za-z0-9\-_/]+)",
        r"DrawingNo\.?[:：]?([A-Za-z0-9\-_/]+)",
        r"([A-Za-z0-9]{1,3}-[A-Za-z0-9]{1,4}-\d{1,4})",
    ]) or find_first(t, [
        r"图\s*号[:：]?\s*([A-Za-z0-9\-_/]+)",
        r"Drawing\s*No\.?[:：]?\s*([A-Za-z0-9\-_/]+)",
    ])
    if drawing_no:
        drawing_no = re.sub(r"[^A-Za-z0-9\-_/]", "", drawing_no)
        drawing_no = drawing_no.lstrip("-_/")
        # If multiple leading digits before first letter, keep only last digit
        m = re.search(r"[A-Za-z]", drawing_no)
        if m and m.start() > 1:
            lead = drawing_no[:m.start()]
            drawing_no = lead[-1] + drawing_no[m.start():]

    # clean title: strip drawing no if appended, remove stray punctuation
    if title_raw:
        if drawing_no and drawing_no in title_raw:
            title_raw = title_raw.replace(drawing_no, "")
        title_raw = re.sub(r"[^0-9A-Za-z一-龥（）()·\-\s]", " ", title_raw)
        title_raw = re.sub(r"\s+", " ", title_raw).strip()
        title_raw = re.sub(r"\s+\d+$", "", title_raw).strip()

    fields["drawing_title"] = title_raw
    fields["drawing_no"] = drawing_no

    fields["date"] = find_first(tc, [
        r"日期[:：]?([0-9]{4}[./-][0-9]{1,2})",
        r"([0-9]{4}[./-][0-9]{1,2})",
    ]) or find_first(t, [
        r"日\s*期[:：]?\s*([0-9]{4}[./-][0-9]{1,2})",
        r"([0-9]{4}[./-][0-9]{1,2})",
    ])

    fields["page_size"] = find_first(tc, [
        r"图幅[:：]?(A\d)",
        r"\b(A\d)\b",
    ]) or find_first(t, [
        r"图\s*幅[:：]?\s*(A\d)",
        r"\b(A\d)\b",
    ])

    fields["scale"] = find_first(tc, [
        r"比例[:：]?(1[:：]\d+)",
        r"SCALE(1[:：]\d+)",
        r"1[:：]\d+",
    ]) or find_first(t, [
        r"比\s*例[:：]?\s*(1\s*[:：]\s*\d+)",
        r"SCALE\s*(1\s*[:：]\s*\d+)",
        r"\b1\s*[:：]\s*\d+\b",
    ])

    return fields


def normalize(text: str):
    # basic cleanup for OCR artifacts
    return re.sub(r"[\s\|]+", " ", text).strip()


def main(pdf_path: str):
    p = Path(pdf_path)
    if not p.exists():
        raise SystemExit(f"File not found: {p}")

    ensure_tessdata()

    wpt, hpt = pdf_page_size_points(p)
    # 400 dpi bottom-right crop (25% x 25%)
    wpx = int(wpt / 72 * 400)
    hpx = int(hpt / 72 * 400)
    cw, ch = int(wpx * 0.25), int(hpx * 0.25)
    x, y = wpx - cw, hpx - ch

    title_png = render_crop(p, TMP / "tb.png", 400, (x, y, cw, ch))
    title_text = ocr(title_png)

    full_png = render_full(p, TMP / "full.png", 300)
    full_text = ocr(full_png)

    title_norm = normalize(title_text)
    full_norm = normalize(full_text)
    fields = extract_fields(title_norm, full_norm)

    merged_text = normalize(title_text + "\n" + full_text)

    result = {
        "project_name": fields.get("project_name"),
        "drawing_title": fields.get("drawing_title"),
        "discipline": None,
        "drawing_no": fields.get("drawing_no"),
        "version": None,
        "date": fields.get("date"),
        "scale": fields.get("scale"),
        "company": fields.get("company"),
        "review_no": None,
        "review_agency": None,
        "design_stage": None,
        "drawing_stage": None,
        "page_size": fields.get("page_size"),
        "sheet_index": None,
        "confidence": 0.6,
        "raw_text": merged_text,
        "candidates": {},
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: extract_title_block_pdf.py <file.pdf>")
    main(sys.argv[1])
