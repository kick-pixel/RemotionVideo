#!/usr/bin/env python3
"""
agent.py - 视频生成大管家
串联流程：
1. 读取 Markdown 文档
2. 调用 generate_script.py (LLM生成剧本)
3. 调用 gen_audio.py (TTS音频生成)
4. 调用 npm run build:dynamic (Remotion渲染)
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.resolve()

def run_command(cmd_list: list[str], cwd: Path = ROOT) -> bool:
    print(f"🚀 执行: {' '.join(cmd_list)}")
    try:
        result = subprocess.run(cmd_list, cwd=cwd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令失败: {' '.join(cmd_list)}\n   返回码: {e.returncode}")
        return False

def main():
    parser = argparse.ArgumentParser(description="自动化技术视频生成管线")
    parser.add_argument("--input", "-i", type=str, required=True, help="输入的 markdown/txt 文档文件路径")
    parser.add_argument("--output", "-o", type=str, default="out/video.mp4", help="最终视频输出路径")
    parser.add_argument("--script-out", type=str, default="workspace/script.json", help="中间剧本 JSON")
    parser.add_argument("--props-out", type=str, default="public/data/render_props.json", help="中间 Remotion props JSON")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 找不到输入文件: {input_path}")
        sys.exit(1)

    print("=" * 50)
    print(f"📽️  开始自动化视频生成管线")
    print(f"📄  输入文档: {input_path}")
    print(f"🎬  最终目标: {args.output}")
    print("=" * 50)

    # 1. 生成剧本
    print("\n[阶段 1/3] LLM 内容解析与剧本生成...")
    script_cmd = [
        sys.executable, str(ROOT / "scripts" / "generate_script.py"),
        "--input", str(input_path),
        "--output", args.script_out
    ]
    if not run_command(script_cmd): sys.exit(1)

    # 2. 生成音频
    print("\n[阶段 2/3] TTS 语音合成...")
    audio_cmd = [
        sys.executable, str(ROOT / "gen_audio.py"),
        "--input", args.script_out,
        "--output", args.props_out
    ]
    if not run_command(audio_cmd): sys.exit(1)

    # 3. 渲染视频
    print("\n[阶段 3/3] Remotion 视频渲染...")
    # Remotion --props 需要绝对路径
    props_path = ROOT / args.props_out
    render_cmd = [
        "npx", "remotion", "render", 
        "src/index.ts", "ArkFAQ", 
        str(ROOT / args.output),
        "--props", str(props_path)
    ]
    if os.name == 'nt':
        # Windows npx 需要 shell=True 或者使用 npx.cmd
        render_cmd[0] = "npx.cmd"

    if not run_command(render_cmd): sys.exit(1)

    print("\n" + "=" * 50)
    print(f"🎉 全部完成！")
    print(f"🎥 最终视频已保存至: {args.output}")
    print("=" * 50)

if __name__ == "__main__": 
    main()
