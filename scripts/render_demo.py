"""Render a looping terminal demo GIF for the README."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from llm_sizer.catalog import parse_context, resolve_model, resolve_quant
from llm_sizer.report import COUNSELNODE_BLURB, build_result
from llm_sizer.sizing import estimate_vram

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
FONTS = Path(r"C:\Windows\Fonts")

BG = (9, 12, 16)
PANEL = (16, 20, 26)
BORDER = (62, 70, 82)
CYAN = (57, 210, 255)
YELLOW = (240, 192, 64)
GREEN = (74, 222, 128)
BLUE = (96, 165, 250)
MAGENTA = (216, 180, 254)
WHITE = (241, 245, 249)
DIM = (156, 163, 175)
MUTED = (100, 110, 125)
PROMPT = (74, 222, 128)

W, H = 1100, 640


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def load_fonts() -> dict[str, ImageFont.FreeTypeFont]:
    return {
        "mono": font("consola.ttf", 22),
        "mono_sm": font("consola.ttf", 18),
        "mono_b": font("consolab.ttf", 22),
        "mono_title": font("consolab.ttf", 24),
        "ui": font("segoeuib.ttf", 18),
        "emoji": font("seguiemj.ttf", 22),
    }


def rounded(draw: ImageDraw.ImageDraw, box, radius: int, fill, outline=None, width: int = 2) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def new_frame(fonts: dict[str, ImageFont.FreeTypeFont]) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    rounded(draw, (18, 18, W - 18, H - 18), 20, PANEL, BORDER, 2)
    draw.rectangle((18, 18, W - 18, 70), fill=(22, 27, 34))
    draw.line((18, 70, W - 18, 70), fill=BORDER, width=2)
    for i, color in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        draw.ellipse((40 + i * 26, 34, 56 + i * 26, 50), fill=color)
    draw.text((128, 32), "llm-sizer   -   AWS GPU VRAM calculator", font=fonts["ui"], fill=WHITE)
    return img, draw


def draw_prompt(draw: ImageDraw.ImageDraw, fonts: dict[str, ImageFont.FreeTypeFont], typed: str, caret: bool) -> None:
    y = 92
    draw.text((44, y), "$", font=fonts["mono_b"], fill=PROMPT)
    draw.text((72, y), typed, font=fonts["mono"], fill=WHITE)
    if caret:
        bbox = draw.textbbox((72, y), typed, font=fonts["mono"])
        cx = (bbox[2] + 4) if typed else 76
        draw.rectangle((cx, y + 3, cx + 12, y + 24), fill=CYAN)


def wrap_text(text: str, font_obj: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    scratch = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    for word in words:
        trial = word if not current else f"{current} {word}"
        if scratch.textlength(trial, font=font_obj) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_output(draw: ImageDraw.ImageDraw, fonts: dict[str, ImageFont.FreeTypeFont], result: dict, stage: int) -> None:
    if stage < 1:
        return

    y = 146
    header = (
        f"LLM SIZER  |  {result['model_name']}  |  {result['quant'].upper()}  |  "
        f"{result['context']}  |  {result['concurrent_users']} users"
    )
    rounded(draw, (40, y, W - 40, y + 56), 12, (10, 32, 40), CYAN, 2)
    draw.text((58, y + 16), header, font=fonts["mono_b"], fill=CYAN)
    y += 78

    if stage < 2:
        return

    draw.text((44, y), "VRAM  &  Instance Recommendation", font=fonts["mono_title"], fill=YELLOW)
    y += 40
    rec = result["recommendation"]
    cols = [
        ("Weights VRAM", f"{result['vram_gb']['weights']:.2f} GB", GREEN),
        ("KV Cache VRAM", f"{result['vram_gb']['kv_cache']:.2f} GB", BLUE),
        ("Total VRAM", f"{result['vram_gb']['total']:.2f} GB", WHITE),
        ("AWS Instance", str(rec["instance"]), CYAN),
        ("Monthly Cost", f"${rec['usd_per_month']:,.0f}/mo", YELLOW),
    ]
    gap = 14
    col_w = (W - 80 - gap * (len(cols) - 1)) // len(cols)
    x = 40
    for title, value, color in cols:
        rounded(draw, (x, y, x + col_w, y + 100), 12, (12, 16, 22), MAGENTA, 2)
        draw.text((x + 14, y + 14), title, font=fonts["mono_sm"], fill=DIM)
        draw.text((x + 14, y + 54), value, font=fonts["mono_b"], fill=color)
        x += col_w + gap
    y += 118

    meta = (
        f"{rec['gpu']}   |   {rec['vram_gb']:g} GB VRAM   |   "
        f"{result['params_billions']:.0f}B params   |   {result['context_tokens']:,} tokens"
    )
    draw.text((48, y), meta, font=fonts["mono_sm"], fill=MUTED)
    y += 42

    if stage < 3:
        return

    body = COUNSELNODE_BLURB.lstrip("💡 ").strip()
    lines = wrap_text(body, fonts["mono_sm"], W - 150)
    box_h = 36 + len(lines) * 26
    rounded(draw, (40, y, W - 40, y + box_h), 12, (36, 28, 8), YELLOW, 2)
    draw.text((58, y + 14), "💡", font=fonts["emoji"], embedded_color=True)
    text_y = y + 18
    draw.text((92, text_y), lines[0], font=fonts["mono_sm"], fill=CYAN)
    for line in lines[1:]:
        text_y += 26
        draw.text((58, text_y), line, font=fonts["mono_sm"], fill=CYAN)


def demo_result() -> dict:
    spec = resolve_model("deepseek-r1")
    quant = "q4"
    context = "32k"
    users = 8
    breakdown = estimate_vram(spec, resolve_quant(quant), parse_context(context), users)
    return build_result(
        model_id="deepseek-r1",
        spec=spec,
        quant=quant,
        bytes_per_param=resolve_quant(quant),
        context_label=context,
        context_tokens=parse_context(context),
        concurrent_users=users,
        breakdown=breakdown,
    )


def build_frames(fonts: dict[str, ImageFont.FreeTypeFont], result: dict) -> list[Image.Image]:
    command = "llm-sizer --model deepseek-r1 --quant q4 --concurrent-users 8 --context 32k"
    frames: list[Image.Image] = []

    def snap(typed: str, caret: bool, stage: int) -> Image.Image:
        img, draw = new_frame(fonts)
        draw_prompt(draw, fonts, typed, caret)
        draw_output(draw, fonts, result, stage)
        frames.append(img)
        return img

    # Poster frames already show the command so GitHub's still preview is useful.
    for _ in range(4):
        snap(command, True, 3)
    for _ in range(3):
        snap("", True, 0)
    step = 3
    for i in range(0, len(command) + 1, step):
        snap(command[:i], True, 0)
    snap(command, False, 0)
    for _ in range(3):
        snap(command, False, 1)
    for _ in range(3):
        snap(command, False, 2)
    for _ in range(16):
        snap(command, False, 3)
    return frames


def write_gif(frames: list[Image.Image], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    frames[-1].save(DOCS / "demo.png")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for i, frame in enumerate(frames):
            frame.save(tmp_path / f"frame_{i:03d}.png")
        palette = tmp_path / "palette.png"
        gif_tmp = tmp_path / "demo.gif"
        subprocess.run(
            [
                "ffmpeg", "-y", "-framerate", "12",
                "-i", str(tmp_path / "frame_%03d.png"),
                "-vf", "palettegen=max_colors=192:stats_mode=full",
                str(palette),
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "ffmpeg", "-y", "-framerate", "12",
                "-i", str(tmp_path / "frame_%03d.png"),
                "-i", str(palette),
                "-lavfi", "paletteuse=dither=sierra2_4a",
                "-loop", "0",
                str(gif_tmp),
            ],
            check=True,
            capture_output=True,
        )
        dest.write_bytes(gif_tmp.read_bytes())


def main() -> None:
    fonts = load_fonts()
    result = demo_result()
    frames = build_frames(fonts, result)
    dest = DOCS / "demo.gif"
    write_gif(frames, dest)
    png = DOCS / "demo.png"
    print(
        f"wrote {dest} ({dest.stat().st_size / 1024:.0f} KB), "
        f"{png} ({png.stat().st_size / 1024:.0f} KB), {len(frames)} frames"
    )


if __name__ == "__main__":
    main()
