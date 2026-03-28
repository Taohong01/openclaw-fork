---
name: title-block-extractor
description: Extract title block (图签栏) metadata from architectural drawing PDFs. Use for auto-archiving/classifying drawings by project, discipline, drawing number, version, date, scale, design stage, review info, and drawing stage (施工图/过程图/投标图等).
---

# Title Block Extraction (PDF 优先)

## Overview

Parse architectural drawing PDFs to locate the title block, extract key fields, and output normalized JSON with confidence scores.

## Workflow (PDF)

1. **Detect text layer**
   - If PDF has text layer: extract via pdfplumber/pypdf.
   - If not: render + OCR (tesseract/paddleocr).

2. **Locate title block**
   - Prefer **bottom-right**; fallback to right-side strip or bottom band.
   - Use layout cues (dense small text, border lines, table grid).

3. **Extract text**
   - Capture raw text and coordinates for audit.

4. **Parse + normalize fields**
   - Apply keyword mapping + regex rules.
   - If multiple candidates, choose highest-confidence + keep alternatives.

5. **Output JSON + confidence**
   - Missing fields must be `null`.

## Output schema (JSON)

```json
{
  "project_name": null,
  "drawing_title": null,
  "discipline": null,
  "drawing_no": null,
  "version": null,
  "date": null,
  "scale": null,
  "company": null,
  "review_no": null,
  "review_agency": null,
  "design_stage": null,
  "drawing_stage": null,
  "page_size": null,
  "sheet_index": null,
  "confidence": 0.0,
  "raw_text": "...",
  "candidates": {
    "drawing_no": ["...", "..."]
  }
}
```

## Heuristics (must follow)

- 图签栏位置：右下角优先 → 右侧 → 底部
- 字段关键词映射与正则：见 `references/field-mapping.md`
- 常见图签栏版式：见 `references/title-block-layouts.md`（样例到位后更新）

## Tools

- **PDF text**: pdfplumber / pypdf
- **OCR**: tesseract / paddleocr

## Resources

- `scripts/extract_title_block_pdf.py` (模板脚本)
- `references/field-mapping.md`
- `references/title-block-layouts.md`
