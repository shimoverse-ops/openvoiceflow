from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
# The website lives in the private openvoiceflow-web repo; point OVF_WEB_ROOT at
# a checkout of it to refresh the site's copy of the icon too.
WEB_ROOT = Path(os.environ["OVF_WEB_ROOT"]) if os.environ.get("OVF_WEB_ROOT") else None
DOC_ASSETS = (WEB_ROOT / "docs" / "assets") if WEB_ROOT else None
ICONSET = ASSETS / "OpenVoiceFlow.iconset"
PNG_1024 = ASSETS / "openvoiceflow-icon-1024.png"
PNG_512 = (DOC_ASSETS / "openvoiceflow-icon-512.png") if DOC_ASSETS else None
ICNS = ASSETS / "OpenVoiceFlow.icns"


def rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size, size), radius=radius, fill=255)
    return mask


def draw_icon(size: int = 1024) -> Image.Image:
    scale = size / 1024
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)
    for y in range(size):
        t = y / max(size - 1, 1)
        r = int(18 + 82 * (1 - t))
        g = int(18 + 54 * t)
        b = int(34 + 126 * (1 - t))
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse(
        tuple(int(v * scale) for v in (78, 38, 830, 760)),
        fill=(124, 92, 252, 95),
    )
    glow_draw.ellipse(
        tuple(int(v * scale) for v in (290, 360, 1010, 1110)),
        fill=(0, 212, 170, 82),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(int(64 * scale)))
    base.alpha_composite(glow)

    mask = rounded_mask(size, int(220 * scale))
    base.putalpha(mask)
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        tuple(int(v * scale) for v in (46, 62, 978, 1006)),
        radius=int(210 * scale),
        fill=(0, 0, 0, 112),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(int(24 * scale)))
    image.alpha_composite(shadow)
    image.alpha_composite(base)

    draw = ImageDraw.Draw(image)
    border = int(22 * scale)
    draw.rounded_rectangle(
        (border, border, size - border, size - border),
        radius=int(196 * scale),
        outline=(255, 255, 255, 42),
        width=max(2, int(3 * scale)),
    )

    # Microphone body.
    mic = tuple(int(v * scale) for v in (392, 202, 632, 648))
    draw.rounded_rectangle(
        mic,
        radius=int(114 * scale),
        fill=(248, 250, 255, 244),
    )
    draw.rounded_rectangle(
        tuple(int(v * scale) for v in (420, 232, 604, 616)),
        radius=int(88 * scale),
        fill=(21, 22, 38, 255),
    )

    # Subtle inner grille.
    for y in (300, 366, 432, 498):
        draw.rounded_rectangle(
            tuple(int(v * scale) for v in (452, y, 572, y + 18)),
            radius=int(9 * scale),
            fill=(124, 92, 252, 170),
        )

    # Stand and ring.
    stroke = max(8, int(36 * scale))
    draw.arc(
        tuple(int(v * scale) for v in (310, 456, 714, 808)),
        22,
        158,
        fill=(248, 250, 255, 230),
        width=stroke,
    )
    draw.rounded_rectangle(
        tuple(int(v * scale) for v in (486, 666, 538, 804)),
        radius=int(24 * scale),
        fill=(248, 250, 255, 238),
    )
    draw.rounded_rectangle(
        tuple(int(v * scale) for v in (378, 790, 646, 850)),
        radius=int(30 * scale),
        fill=(248, 250, 255, 238),
    )

    # Voice waveform.
    wave_color = (0, 212, 170, 238)
    for x, top, bottom in [
        (218, 442, 590),
        (270, 398, 634),
        (322, 472, 560),
        (702, 472, 560),
        (754, 398, 634),
        (806, 442, 590),
    ]:
        draw.rounded_rectangle(
            tuple(int(v * scale) for v in (x, top, x + 28, bottom)),
            radius=int(14 * scale),
            fill=wave_color,
        )

    return image


def write_iconset(source: Image.Image) -> None:
    sizes = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]
    if ICONSET.exists():
        shutil.rmtree(ICONSET)
    ICONSET.mkdir(parents=True)
    for px, name in sizes:
        resized = source.resize((px, px), Image.Resampling.LANCZOS)
        resized.save(ICONSET / name)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    icon = draw_icon()
    icon.save(PNG_1024)
    if DOC_ASSETS is not None:
        DOC_ASSETS.mkdir(parents=True, exist_ok=True)
        icon.resize((512, 512), Image.Resampling.LANCZOS).save(PNG_512)
    else:
        print("OVF_WEB_ROOT unset — skipping the website's 512px icon copy")
    write_iconset(icon)
    subprocess.run(["iconutil", "-c", "icns", str(ICONSET), "-o", str(ICNS)], check=True)
    shutil.rmtree(ICONSET)


if __name__ == "__main__":
    main()
