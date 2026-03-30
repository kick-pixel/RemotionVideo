#!/usr/bin/env python3
"""
make_video.py — 一键技术视频生成入口
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
用法：
  python make_video.py <文档路径>                    # 一键生成
  python make_video.py <文档路径> -o out/my.mp4      # 自定义输出路径
  python make_video.py <文档路径> --skip-script       # 跳过 LLM，复用已有 script.json
  python make_video.py <文档路径> --skip-audio        # 跳过 TTS，复用已有音频
  python make_video.py <文档路径> --skip-render       # 仅生成音频，不渲染
  python make_video.py <文档路径> --open              # 完成后自动打开视频

流程：
  [1/3] LLM 剧本生成   →  workspace/script.json
  [2/3] TTS 语音合成   →  public/audio/*.mp3  +  public/data/render_props.json
  [3/3] Remotion 渲染  →  out/<name>.mp4
"""

import argparse
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

# ── 项目根目录 ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.resolve()

# ── ANSI 颜色（Windows 10+ 终端支持） ─────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
DIM    = "\033[2m"


def c(color: str, text: str) -> str:
    """包装 ANSI 颜色，Windows 下自动启用 VT 模式。"""
    return f"{color}{text}{RESET}"


def banner(stage: int, total: int, title: str) -> None:
    line = "─" * 50
    print(f"\n{c(CYAN, line)}")
    print(f"{c(BOLD, f'  [{stage}/{total}]')}  {c(CYAN, title)}")
    print(c(CYAN, line))


def ok(msg: str) -> None:
    print(f"  {c(GREEN, '✅')}  {msg}")


def warn(msg: str) -> None:
    print(f"  {c(YELLOW, '⚠️ ')}  {msg}")


def fail(msg: str) -> None:
    print(f"  {c(RED, '❌')}  {msg}")


def info(msg: str) -> None:
    print(f"  {c(DIM, '·')}  {msg}")


# ── 工具函数 ────────────────────────────────────────────────────────────────

def slugify(name: str) -> str:
    """文件名 → 安全 slug（去除扩展名，中文转拼音不处理，只替换非法字符）。"""
    stem = Path(name).stem
    slug = re.sub(r"[^\w\u4e00-\u9fff\-]", "_", stem)
    return slug or "output"


def run(cmd: list[str], cwd: Path = ROOT) -> bool:
    """执行子命令，实时打印输出，返回是否成功。"""
    cmd_str = " ".join(str(c) for c in cmd)
    info(f"$ {cmd_str}")
    print()
    try:
        result = subprocess.run(cmd, cwd=cwd)
        return result.returncode == 0
    except FileNotFoundError as e:
        fail(f"命令未找到: {e}")
        return False


def open_file(path: Path) -> None:
    """跨平台打开文件。"""
    try:
        if platform.system() == "Windows":
            os.startfile(str(path))
        elif platform.system() == "Darwin":
            subprocess.run(["open", str(path)])
        else:
            subprocess.run(["xdg-open", str(path)])
    except Exception as e:
        warn(f"无法自动打开视频: {e}")


# ── 主流程 ──────────────────────────────────────────────────────────────────

def main() -> None:
    # 启用 Windows VT100 ANSI 支持
    if platform.system() == "Windows":
        os.system("")

    parser = argparse.ArgumentParser(
        description="一键技术视频生成管线",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "input",
        metavar="INPUT",
        help="技术文档路径（.md / .txt）",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="OUT",
        default=None,
        help="最终视频输出路径（默认：out/<文件名>.mp4）",
    )
    parser.add_argument(
        "--script-json",
        metavar="PATH",
        default="workspace/script.json",
        help="LLM 剧本 JSON 路径（默认：workspace/script.json）",
    )
    parser.add_argument(
        "--props-json",
        metavar="PATH",
        default="public/data/render_props.json",
        help="Remotion props JSON 路径（默认：public/data/render_props.json）",
    )
    parser.add_argument(
        "--skip-script",
        action="store_true",
        help="跳过 LLM 剧本生成，直接使用已有 script.json",
    )
    parser.add_argument(
        "--skip-audio",
        action="store_true",
        help="跳过 TTS 音频生成，直接使用已有音频文件",
    )
    parser.add_argument(
        "--skip-render",
        action="store_true",
        help="跳过 Remotion 渲染（仅生成音频与 props）",
    )
    parser.add_argument(
        "--open",
        dest="auto_open",
        action="store_true",
        help="渲染完成后自动打开视频",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        fail(f"找不到输入文件: {input_path}")
        sys.exit(1)
    if not input_path.is_file():
        fail(f"输入路径不是文件: {input_path}")
        sys.exit(1)

    # 输出路径：默认从输入文件名派生
    if args.output:
        video_out = Path(args.output)
    else:
        slug = slugify(input_path.name)
        video_out = ROOT / "out" / f"{slug}.mp4"

    script_json = args.script_json
    props_json  = args.props_json
    total_steps = 3 - int(args.skip_render)  # 跳过渲染时只显示 2 步
    step = 0

    # ── 打印欢迎头 ──────────────────────────────────────────────────────────
    width = 54
    print(f"\n{'━' * width}")
    print(f"  {c(BOLD + CYAN, '🎬  Tech Video Pipeline')}")
    print(f"{'━' * width}")
    info(f"输入文档 : {input_path}")
    info(f"剧本 JSON: {ROOT / script_json}")
    info(f"Props    : {ROOT / props_json}")
    if not args.skip_render:
        info(f"输出视频 : {video_out}")
    print()
    if args.skip_script:
        warn("--skip-script : 跳过 LLM 剧本生成")
    if args.skip_audio:
        warn("--skip-audio  : 跳过 TTS 音频合成")
    if args.skip_render:
        warn("--skip-render : 跳过 Remotion 渲染")

    t_start = time.time()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 阶段 1：LLM 剧本生成
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    step += 1
    banner(step, total_steps, "LLM 剧本生成")

    if args.skip_script:
        script_path = ROOT / script_json
        if not script_path.exists():
            fail(f"--skip-script 模式下找不到剧本文件: {script_path}")
            sys.exit(1)
        ok(f"复用已有剧本: {script_path}")
    else:
        # 确保输出目录存在
        (ROOT / script_json).parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "generate_script.py"),
            "--input",  str(input_path),
            "--output", script_json,
        ]
        if not run(cmd):
            fail("LLM 剧本生成失败，终止。")
            sys.exit(1)
        ok(f"剧本已保存: {ROOT / script_json}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 阶段 2：TTS 音频合成
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    step += 1
    banner(step, total_steps, "TTS 语音合成")

    if args.skip_audio:
        props_path = ROOT / props_json
        if not props_path.exists():
            fail(f"--skip-audio 模式下找不到 props 文件: {props_path}")
            sys.exit(1)
        ok(f"复用已有音频与 Props: {props_path}")
    else:
        (ROOT / props_json).parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            str(ROOT / "gen_audio.py"),
            "--input",  script_json,
            "--output", props_json,
        ]
        if not run(cmd):
            fail("TTS 音频合成失败，终止。")
            sys.exit(1)
        ok(f"Props 已保存: {ROOT / props_json}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 阶段 3：Remotion 视频渲染
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if not args.skip_render:
        step += 1
        banner(step, total_steps, "Remotion 视频渲染")

        video_out.parent.mkdir(parents=True, exist_ok=True)
        props_abs = str((ROOT / props_json).resolve())

        npx_cmd = "npx.cmd" if platform.system() == "Windows" else "npx"
        cmd = [
            npx_cmd, "remotion", "render",
            "src/index.ts",
            "ArkFAQ",
            str(video_out.resolve()),
            "--props", props_abs,
        ]
        if not run(cmd):
            fail("Remotion 渲染失败，终止。")
            sys.exit(1)
        ok(f"视频已输出: {video_out.resolve()}")

    # ── 完成汇总 ────────────────────────────────────────────────────────────
    elapsed = time.time() - t_start
    print(f"\n{'━' * width}")
    print(f"  {c(GREEN + BOLD, '🎉  全部完成！')}  {c(DIM, f'耗时 {elapsed:.1f}s')}")
    print(f"{'━' * width}")
    if not args.skip_render:
        print(f"  {c(BOLD, '🎥  视频路径')}  {video_out.resolve()}")
    print()

    if args.auto_open and not args.skip_render:
        info("正在打开视频...")
        open_file(video_out.resolve())


if __name__ == "__main__":
    main()
