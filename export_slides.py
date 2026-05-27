import asyncio
import os
import tempfile
import argparse
import logging
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from pypdf import PdfWriter

logger = logging.getLogger(__name__)

async def capture_slide(context, i, base_url, width, height, scale_factor, semaphore):
    async with semaphore:
        url = f"{base_url}/{i}"
        logger.info("[%d] Loading: %s", i, url)

        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)

            try:
                await page.wait_for_selector(
                    ".slidev-slide, .slide",
                    state="attached",
                    timeout=8000,
                )
            except Exception as e:
                logger.warning("[%d] Slide selector not found within 8 seconds: %s", i, e)

            await asyncio.sleep(0.2)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp_path = tmp.name

            await page.pdf(
                path=tmp_path,
                width=f"{width}px",
                height=f"{height}px",
                print_background=True,
                margin={
                    "top": "0px",
                    "bottom": "0px",
                    "left": "0px",
                    "right": "0px",
                },
            )

            logger.info("[%d] Slide saved successfully", i)
            return tmp_path

        except Exception as e:
            logger.error("[%d] Error: %s", i, e)
            raise

        finally:
            await page.close()


async def capture_slides_to_pdf(
    base_url: str,
    slide_count: int,
    output_pdf: str,
    width: int = 1920,
    height: int = 1080,
    scale_factor: int = 2,
    concurrency: int = 3,
):
    temp_files = []
    writer = PdfWriter()

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=scale_factor,
            )

            semaphore = asyncio.Semaphore(concurrency)
            tasks = [
                capture_slide(
                    context, i, base_url, width, height, scale_factor, semaphore
                )
                for i in range(1, slide_count + 1)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for index, result in enumerate(results):
                slide_num = index + 1
                if isinstance(result, Exception):
                    logger.error(
                        "Slide %d has an issue, skipping merge: %s",
                        slide_num,
                        result,
                    )
                else:
                    temp_files.append(result)

            await browser.close()

        if not temp_files:
            logger.error("No PDF files captured")
            return

        logger.info("Merging %d PDF files...", len(temp_files))
        for f in temp_files:
            writer.append(f)

        writer.write(output_pdf)
        logger.info(
            "Done! Saved as: %s (%d slides)", output_pdf, len(temp_files)
        )

    except Exception as e:
        logger.exception("Error during execution: %s", e)

    finally:
        writer.close()
        for f in temp_files:
            if os.path.exists(f):
                try:
                    os.unlink(f)
                except OSError:
                    pass


def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="Load slides from website (e.g., Slidev) as PDF"
    )
    parser.add_argument(
        "url",
        help="Main URL of slides (no page number needed, e.g. https://website.com/slides/)",
    )
    parser.add_argument("count", type=int, help="Total number of slides")
    parser.add_argument(
        "-o",
        "--output",
        default="output-slides.pdf",
        help="Output PDF filename (default: output-slides.pdf)",
    )
    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=1920,
        help="Screen width in pixels (default: 1920)",
    )
    parser.add_argument(
        "-H",
        "--height",
        type=int,
        default=1080,
        help="Screen height in pixels (default: 1080)",
    )
    parser.add_argument(
        "-s",
        "--scale",
        type=int,
        default=2,
        help="device scale factor (default: 2)",
    )
    parser.add_argument(
        "-c",
        "--concurrency",
        type=int,
        default=3,
        help="Number of slides to process concurrently (default: 3)",
    )

    args = parser.parse_args()

    if not is_valid_url(args.url):
        logger.error("Invalid URL: %s", args.url)
        exit(1)

    asyncio.run(
        capture_slides_to_pdf(
            args.url,
            args.count,
            args.output,
            args.width,
            args.height,
            args.scale,
            args.concurrency,
        )
    )
