"""Printable task sheets for Step 1 (one 6x6 number grid per trial). Print the PDF once per group (6x).
usage: python3 materials/make_task_sheets.py  ->  materials/task_sheets_trials_1-4.pdf"""
import os
import random
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "task_sheets_trials_1-4.pdf")
DPI = 150
W, H = int(8.27 * DPI), int(11.69 * DPI)          # A4 portrait
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
INK, MUTED, LINE, ACCENT = (28, 27, 46), (95, 97, 120), (28, 27, 46), (226, 85, 59)


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def page(trial, numbers):
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.text((90, 80), "PROXEMICS × FLOW · STEP 1 · FEEL IT", font=font(BOLD, 26), fill=ACCENT)
    d.text((90, 125), f"Trial {trial}", font=font(BOLD, 96), fill=INK)
    d.text((W - 90, 160), "Group: ______", font=font(FONT, 36), fill=INK, anchor="ra")
    instr = ("Find the numbers 1, 2, 3 … 36 in order and cross each one out.\n"
             "Stop when the timer ends. Then enter the last number you crossed out in the app.")
    d.multiline_text((90, 270), instr, font=font(FONT, 30), fill=MUTED, spacing=10)
    cell, n = 166, 6
    gx = (W - cell * n) // 2
    gy = 420
    f_num = font(BOLD, 70)
    for i, num in enumerate(numbers):
        r, c = divmod(i, n)
        x0, y0 = gx + c * cell, gy + r * cell
        d.rectangle([x0, y0, x0 + cell, y0 + cell], outline=LINE, width=4)
        d.text((x0 + cell / 2, y0 + cell / 2), str(num), font=f_num, fill=INK, anchor="mm")
    d.text((90, H - 120), "Anyone may skip a distance: tick 'skipped' in the app. No touching.",
           font=font(FONT, 24), fill=MUTED)
    return im


def main():
    rng = random.Random(2026)
    n_cells = 36
    pages = []
    for trial in range(1, 5):
        nums = list(range(1, n_cells + 1))
        rng.shuffle(nums)
        pages.append(page(trial, nums))
    pages[0].save(OUT, save_all=True, append_images=pages[1:], resolution=DPI)
    print("saved", OUT)


if __name__ == "__main__":
    main()
