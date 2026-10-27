"""Render catalog artwork as PNG cards; configured restaurant photos take precedence."""

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def render_card(card):
    image = Image.new("RGB", (1000, 540), "#123e36")
    draw = ImageDraw.Draw(image)
    font_path = Path("C:/Windows/Fonts/segoeui.ttf")

    def font(size):
        return (
            ImageFont.truetype(str(font_path), size)
            if font_path.exists()
            else ImageFont.load_default(size=size)
        )

    draw.rounded_rectangle((28, 28, 972, 512), radius=24, fill="#f8f4e9")
    draw.text(
        (65, 55),
        "QUICKBUDDY  /  " + ("DEMO MENU" if card["demo"] else "MENU"),
        font=font(20),
        fill="#157552",
    )
    # Fallback artwork is an illustration, never a merchant product photograph.
    if card.get("kind") in ("groceries", "essentials"):
        draw.rounded_rectangle((715, 180, 925, 365), radius=14, fill="#c69c62")
        draw.arc((755, 110, 885, 235), 180, 360, fill="#705335", width=12)
        draw.rectangle((740, 165, 790, 260), fill="#6a9c68")
        draw.rounded_rectangle((805, 135, 855, 270), radius=12, fill="#f1e9d5")
        draw.ellipse((855, 200, 905, 250), fill="#df7055")
    else:
        draw.ellipse((700, 130, 925, 355), fill="#e7d9b6", outline="#c8b880", width=8)
        draw.ellipse((725, 155, 900, 330), fill="#f3b84c")
        for x, y in [(760, 195), (820, 180), (800, 250), (860, 260), (750, 280)]:
            draw.ellipse((x, y, x + 19, y + 11), fill="#69934b")
    draw.text((710, 400), "Product illustration", font=font(17), fill="#687b73")
    title = card["title"]
    lines = []
    while len(title) > 26:
        cut = title.rfind(" ", 0, 27)
        cut = cut if cut > 0 else 26
        lines.append(title[:cut])
        title = title[cut:].strip()
    lines.append(title)
    y = 115
    for line in lines[:2]:
        draw.text((65, y), line, font=font(37), fill="#173b31")
        y += 48
    for line in card["text"].splitlines():
        draw.text((65, y + 18), line[:62], font=font(21), fill="#456153")
        y += 35
    draw.rounded_rectangle((65, 430, 390, 480), radius=14, fill="#157552")
    draw.text((85, 440), card["label"], font=font(22), fill="white")
    draw.text((535, 460), "Illustration · not a product photograph", font=font(17), fill="#617469")
    output = BytesIO()
    image.save(output, "PNG")
    return output.getvalue()
