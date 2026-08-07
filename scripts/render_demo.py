#!/usr/bin/env python3
"""Regenerate the bilingual README GIFs from one real forward-test result.

This development-only renderer requires Pillow. The feature-retcon runtime
remains Python-standard-library only.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1200
HEIGHT = 720
BACKGROUND = "#070b14"
TERMINAL = "#0d1117"
PANEL = "#161b22"
BORDER = "#30363d"
TEXT = "#e6edf3"
MUTED = "#8b949e"
CYAN = "#58d6ff"
GREEN = "#3fb950"
PURPLE = "#bc8cff"
AMBER = "#d29922"
RED = "#ff7b72"

FONT_CANDIDATES = (
    Path.home() / "Library/Fonts/MapleMono-NF-CN-Regular.ttf",
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("C:/Windows/Fonts/msyh.ttc"),
)

COPY: dict[str, dict[str, object]] = {
    "zh": {
        "window_title": "feature-retcon · 后悔药",
        "badge": "中文演示 · 真实运行",
        "steps": ("1 需求变了", "2 先只读评估", "3 写入前确认"),
        "prompt_short": "❯ 使用 $feature-retcon",
        "prompt": "❯ 使用 $feature-retcon：固定 PDF → PDF / CSV 可选",
        "change_title": "功能做到一半，需求变了",
        "old_label": "旧答案",
        "old_value": "固定导出 PDF",
        "new_label": "新目标",
        "new_value": "PDF 或 CSV\n未选择时默认 PDF",
        "progress": "这个功能已经推进到：任务阶段",
        "scan": "正在读取权威需求、Git 基线和下游引用",
        "assess_title": "先评估，不修改文件",
        "facts": (
            "找到权威需求：specs/export.md",
            "当前已推进到：任务阶段",
            "建议本轮先改：需求",
            "设计、任务：标记为“待追平”",
        ),
        "reason": "CSV 细节尚未定义，不替用户猜实现。",
        "confirm_title": "评估完成，停在第一次写入之前",
        "metrics": (("3", "预计修改文件"), ("5", "旧结论替换"), ("0", "文件删除"), ("0", "评估期写入")),
        "success": "没有修改任何文件",
        "waiting": "等待你确认：变更内容 · 目标阶段 · 可写范围",
        "tagline": "先看清，再动手。",
        "footer": "真实 forward-test 摘录 · 临时合成仓库",
    },
    "en": {
        "window_title": "feature-retcon",
        "badge": "ENGLISH · REAL RUN",
        "steps": ("1 Requirement changed", "2 Read-only assessment", "3 Confirm before writes"),
        "prompt_short": "❯ Use $feature-retcon",
        "prompt": "❯ Use $feature-retcon: PDF only → PDF or CSV",
        "change_title": "The requirement changed halfway through",
        "old_label": "OLD ANSWER",
        "old_value": "Always export PDF",
        "new_label": "NEW TARGET",
        "new_value": "PDF or CSV\nDefault to PDF",
        "progress": "This feature has already reached: tasks",
        "scan": "Reading authority, Git baseline, and downstream references",
        "assess_title": "Assess first. Change nothing.",
        "facts": (
            "Authority found: specs/export.md",
            "Current progress: tasks",
            "Recommended scope: requirements first",
            "Design and tasks: mark as stale",
        ),
        "reason": "CSV details are undefined — do not invent implementation decisions.",
        "confirm_title": "Assessment complete. Stop before the first write.",
        "metrics": (("3", "files to edit"), ("5", "old claims\nto replace"), ("0", "file deletions"), ("0", "assessment\nwrites")),
        "success": "No files were changed",
        "waiting": "Waiting for: assertions · target stage · writable roots",
        "tagline": "Understand first. Then change.",
        "footer": "Real forward-test excerpt · temporary synthetic repository",
    },
}


def choose_font(explicit: str | None) -> Path:
    candidates = (Path(explicit).expanduser(),) if explicit else FONT_CANDIDATES
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise SystemExit("找不到支持中文的字体；请通过 --font 指定字体文件")


def font(font_path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(font_path), size)


def centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    text_font: ImageFont.FreeTypeFont,
    color: str,
) -> None:
    bounds = draw.multiline_textbbox((0, 0), text, font=text_font, align="center", spacing=8)
    text_width = bounds[2] - bounds[0]
    text_height = bounds[3] - bounds[1]
    x = box[0] + (box[2] - box[0] - text_width) / 2
    y = box[1] + (box[3] - box[1] - text_height) / 2 - bounds[1]
    draw.multiline_text((x, y), text, font=text_font, fill=color, align="center", spacing=8)


def draw_shell(draw: ImageDraw.ImageDraw, font_path: Path, copy: dict[str, object], active_step: int) -> None:
    draw.rounded_rectangle(
        (45, 35, WIDTH - 45, HEIGHT - 35),
        radius=22,
        fill=TERMINAL,
        outline=BORDER,
        width=2,
    )
    draw.line((45, 91, WIDTH - 45, 91), fill=BORDER, width=2)
    for x, color in ((75, "#ff5f56"), (103, "#ffbd2e"), (131, "#27c93f")):
        draw.ellipse((x - 7, 63 - 7, x + 7, 63 + 7), fill=color)
    draw.text((168, 51), str(copy["window_title"]), font=font(font_path, 21), fill=MUTED)

    badge = str(copy["badge"])
    badge_font = font(font_path, 16)
    badge_bounds = draw.textbbox((0, 0), badge, font=badge_font)
    badge_width = badge_bounds[2] - badge_bounds[0] + 34
    badge_box = (WIDTH - 80 - badge_width, 50, WIDTH - 80, 78)
    draw.rounded_rectangle(badge_box, radius=14, fill="#172033", outline="#2f81f7")
    draw.text((badge_box[0] + 17, 53), badge, font=badge_font, fill=CYAN)

    steps = tuple(copy["steps"])
    gap = 18
    total_width = 1010
    step_width = (total_width - gap * 2) // 3
    for index, label in enumerate(steps):
        left = 95 + index * (step_width + gap)
        box = (left, 108, left + step_width, 149)
        active = index == active_step
        draw.rounded_rectangle(
            box,
            radius=14,
            fill="#172033" if active else TERMINAL,
            outline=PURPLE if active else BORDER,
            width=2 if active else 1,
        )
        centered_text(draw, box, str(label), font(font_path, 18), PURPLE if active else MUTED)


def draw_change(draw: ImageDraw.ImageDraw, font_path: Path, copy: dict[str, object]) -> None:
    draw.text((84, 178), str(copy["prompt"]), font=font(font_path, 24), fill=CYAN)
    draw.text((84, 230), str(copy["change_title"]), font=font(font_path, 34), fill=TEXT)

    left_box = (84, 300, 498, 455)
    right_box = (702, 300, 1116, 455)
    draw.rounded_rectangle(left_box, radius=18, fill=PANEL, outline=RED, width=2)
    draw.rounded_rectangle(right_box, radius=18, fill=PANEL, outline=GREEN, width=2)
    draw.text((112, 325), str(copy["old_label"]), font=font(font_path, 18), fill=RED)
    draw.text((730, 325), str(copy["new_label"]), font=font(font_path, 18), fill=GREEN)
    centered_text(draw, (100, 348, 482, 438), str(copy["old_value"]), font(font_path, 29), TEXT)
    centered_text(draw, (718, 348, 1100, 438), str(copy["new_value"]), font(font_path, 29), TEXT)
    draw.line((535, 377, 656, 377), fill=PURPLE, width=4)
    draw.polygon(((656, 377), (634, 364), (634, 390)), fill=PURPLE)

    progress_box = (245, 500, 955, 564)
    draw.rounded_rectangle(progress_box, radius=18, fill="#201a32", outline=PURPLE)
    centered_text(draw, progress_box, str(copy["progress"]), font(font_path, 24), PURPLE)


def draw_scan(draw: ImageDraw.ImageDraw, font_path: Path, copy: dict[str, object], phase: int) -> None:
    draw.text((84, 178), str(copy["prompt"]), font=font(font_path, 24), fill=CYAN)
    dots = "." * (phase + 1)
    centered_text(
        draw,
        (120, 260, 1080, 460),
        f"{copy['scan']}{dots}",
        font(font_path, 28),
        MUTED,
    )
    draw.rounded_rectangle((260, 475, 940, 489), radius=7, fill="#21262d")
    progress_width = (phase + 1) * 170
    draw.rounded_rectangle((260, 475, 260 + progress_width, 489), radius=7, fill=PURPLE)


def draw_assessment(draw: ImageDraw.ImageDraw, font_path: Path, copy: dict[str, object], show_reason: bool) -> None:
    draw.text((84, 178), str(copy["prompt"]), font=font(font_path, 24), fill=CYAN)
    draw.text((84, 230), str(copy["assess_title"]), font=font(font_path, 34), fill=TEXT)
    facts = tuple(copy["facts"])
    for index, fact in enumerate(facts):
        y = 304 + index * 58
        draw.rounded_rectangle((88, y, 1112, y + 44), radius=12, fill=PANEL)
        draw.ellipse((108, y + 13, 126, y + 31), fill=GREEN)
        draw.text((145, y + 6), str(fact), font=font(font_path, 23), fill=TEXT)
    if show_reason:
        reason_box = (88, 552, 1112, 607)
        draw.rounded_rectangle(reason_box, radius=14, fill="#2a2112", outline=AMBER)
        centered_text(draw, reason_box, str(copy["reason"]), font(font_path, 21), AMBER)


def draw_confirmation(draw: ImageDraw.ImageDraw, font_path: Path, copy: dict[str, object], tagline: bool) -> None:
    draw.text((84, 178), str(copy["confirm_title"]), font=font(font_path, 32), fill=TEXT)
    metrics = tuple(copy["metrics"])
    for index, metric in enumerate(metrics):
        value, label = metric
        left = 84 + index * 258
        box = (left, 255, left + 230, 390)
        draw.rounded_rectangle(box, radius=18, fill=PANEL, outline=GREEN if str(value) == "0" else BORDER)
        centered_text(draw, (left, 268, left + 230, 330), str(value), font(font_path, 46), GREEN if str(value) == "0" else CYAN)
        centered_text(draw, (left + 8, 332, left + 222, 380), str(label), font(font_path, 18), MUTED)

    success_box = (220, 430, 980, 486)
    draw.rounded_rectangle(success_box, radius=16, fill="#13251b", outline=GREEN)
    centered_text(draw, success_box, f"✓ {copy['success']}", font(font_path, 24), GREEN)
    centered_text(draw, (80, 506, 1120, 560), str(copy["waiting"]), font(font_path, 22), AMBER)
    if tagline:
        centered_text(draw, (80, 570, 1120, 625), str(copy["tagline"]), font(font_path, 28), PURPLE)


def draw_frame(
    font_path: Path,
    copy: dict[str, object],
    active_step: int,
    scene: str,
    phase: int,
) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw_shell(draw, font_path, copy, active_step)
    if scene == "intro":
        prompt = copy["prompt_short"] if phase == 0 else copy["prompt"]
        centered_text(draw, (90, 220, 1110, 520), str(prompt), font(font_path, 30), CYAN)
    elif scene == "change":
        draw_change(draw, font_path, copy)
    elif scene == "scan":
        draw_scan(draw, font_path, copy, phase)
    elif scene == "assessment":
        draw_assessment(draw, font_path, copy, show_reason=bool(phase))
    elif scene == "confirmation":
        draw_confirmation(draw, font_path, copy, tagline=bool(phase))
    draw.text((82, 654), str(copy["footer"]), font=font(font_path, 18), fill=MUTED)
    return image


def timeline() -> list[tuple[int, int, str, int]]:
    return [
        (1000, 0, "intro", 0),
        (1000, 0, "intro", 1),
        (3000, 0, "change", 0),
        (1000, 1, "scan", 0),
        (1000, 1, "scan", 1),
        (2800, 1, "assessment", 0),
        (2600, 1, "assessment", 1),
        (3500, 2, "confirmation", 0),
        (3500, 2, "confirmation", 1),
    ]


def render(language: str, font_path: Path, output: Path) -> None:
    copy = COPY[language]
    events = timeline()
    frames = [
        draw_frame(font_path, copy, active_step, scene, phase)
        for _, active_step, scene, phase in events
    ]
    palette = frames[0].convert("P", palette=Image.Palette.ADAPTIVE, colors=128)
    optimized = [
        palette,
        *[
            frame.quantize(palette=palette, dither=Image.Dither.NONE)
            for frame in frames[1:]
        ],
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    optimized[0].save(
        output,
        save_all=True,
        append_images=optimized[1:],
        duration=[duration for duration, _, _, _ in events],
        loop=0,
        optimize=True,
        disposal=2,
    )
    duration = sum(value for value, _, _, _ in events) / 1000
    print(f"rendered {language}: {output} ({duration:.1f}s)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", help="支持中文的 TTF/TTC 字体路径")
    parser.add_argument("--language", choices=("all", "zh", "en"), default="all")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "assets",
    )
    args = parser.parse_args()

    font_path = choose_font(args.font)
    languages = COPY if args.language == "all" else (args.language,)
    for language in languages:
        render(language, font_path, args.output_dir / f"feature-retcon-demo-{language}.gif")


if __name__ == "__main__":
    main()
