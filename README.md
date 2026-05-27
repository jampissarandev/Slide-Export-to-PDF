# Slide Export to PDF

Export slide decks (e.g. Slidev) to a single PDF using Playwright.

## Requirements

- Python 3.8+
- [Playwright](https://playwright.dev/python/)
- [pypdf](https://pypi.org/project/pypdf/)

## Installation

```bash
pip install playwright pypdf
playwright install chromium
```

## Usage

```bash
python export_slides.py <URL> <SLIDE_COUNT> [options]
```

### Example

```bash
python export_slides.py https://example.com/slides 20 -o my-slides.pdf
```

### Options

| Argument | Description | Default |
|----------|-------------|---------|
| `url` | Main URL of slides (without page number) | — |
| `count` | Total number of slides | — |
| `-o, --output` | Output PDF filename | `output-slides.pdf` |
| `-w, --width` | Screen width in pixels | `1920` |
| `-H, --height` | Screen height in pixels | `1080` |
| `-s, --scale` | Device scale factor | `2` |
| `-c, --concurrency` | Slides to process concurrently | `3` |
