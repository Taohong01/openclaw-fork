---
name: oda-dwg-dxf
description: Convert DWG files to DXF using ODA File Converter on macOS. Use when asked to batch-convert DWG/DXF, run ODAFileConverter CLI, or produce 2018 ASCII DXF outputs.
---

# ODA DWG → DXF (macOS)

## Quick workflow

1. Confirm input/output directories and desired output (default: 2018 ASCII DXF).
2. Run the converter via CLI.
3. Optionally list or spot-check output files.

## CLI command (manual)

```bash
/Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter \
  <input_dir> <output_dir> ACAD2018 DXF 1 0
```

- `ACAD2018` + `DXF` + `1 0` yields **2018 ASCII DXF**.
- Ensure output directory exists (or create it).

## Helper script

Use the bundled script for the standard conversion:

```bash
scripts/convert_dwg_to_dxf.sh <input_dir> <output_dir>
```

The script:

- Validates inputs
- Ensures the ODA binary exists at `/Applications/ODAFileConverter.app`
- Creates the output dir if needed
- Runs the conversion with ACAD2018 DXF 1 0
