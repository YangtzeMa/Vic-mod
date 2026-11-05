"""Render the original, code-drawn placeholder cover. Optional dependency: Pillow."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    image = Image.new("RGB", (1024, 1024), "#132e35")
    draw = ImageDraw.Draw(image)
    gold, paper, muted = "#d9b672", "#f3eddd", "#aabdb9"
    draw.rectangle((40, 40, 984, 984), outline=gold, width=3)
    draw.rectangle((54, 54, 970, 970), outline="#52665f", width=1)
    # Abstract mechanical motif; no game art, logo or third-party image is used.
    draw.ellipse((680, 80, 1120, 520), outline="#29454a", width=52)
    draw.ellipse((-180, 600, 260, 1040), outline="#29454a", width=52)
    font_path = Path("C:/Windows/Fonts/segoeui.ttf")
    if not font_path.is_file():
        raise FileNotFoundError("Use an installed Segoe UI font to rebuild the cover.")

    def centered(text: str, y: int, size: int, fill: str) -> None:
        font = ImageFont.truetype(str(font_path), size)
        box = draw.textbbox((0, 0), text, font=font)
        draw.text(((1024 - (box[2] - box[0])) / 2, y), text, font=font, fill=fill)

    centered("VICTORIA 3", 220, 36, gold)
    draw.line((410, 310, 614, 310), fill=gold, width=3)
    centered("VIC MOD", 355, 108, paper)
    centered("TEMPLATE", 486, 56, paper)
    centered("A FOUNDATION FOR WHAT COMES NEXT", 662, 22, muted)
    centered("FRAMEWORK  /  0.1.0", 838, 24, gold)
    for path in (ROOT / "mod/thumbnail.png", ROOT / "mod/.metadata/thumbnail.png"):
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, format="PNG", optimize=True)
    print("Generated both original placeholder previews (1024x1024 RGB).")


if __name__ == "__main__":
    main()
