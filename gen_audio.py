#!/usr/bin/env python3
"""
gen_audio.py — Dialogue TTS 音频生成入口

替代旧的 generate_audio.py，从 .env 读取配置，
使用 src/dialogue-tts 引擎将问答数据生成 MP3 音频。

用法:
    python gen_audio.py              # 使用 .env 中的引擎（默认 edge）
    TTS_ENGINE=edge python gen_audio.py
    TTS_ENGINE=aliyun python gen_audio.py

依赖:
    pip install python-dotenv edge-tts mutagen         # edge 引擎
    pip install python-dotenv dashscope mutagen        # aliyun 引擎
"""

import asyncio
import os
import sys
from pathlib import Path

import json
import argparse

# ── 1. 加载 .env（必须在所有 import 之前）────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    print("⚠️  python-dotenv 未安装，跳过 .env 自动加载")
    print("   安装: pip install python-dotenv\n")

# ── 2. 将 dialogue-tts 模块加入 Python 路径 ─────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src" / "dialogue-tts"))

from skill import build_engine, get_audio_duration_sec   # noqa: E402

OUTPUT_DIR = ROOT / "public" / "audio"
DATA_DIR = ROOT / "public" / "data"


# ── 核心：逐条生成（顺序执行，避免并发触发限流）───────────────────────
async def generate_one(engine, name: str, speaker: str, text: str) -> bool:
    """
    生成单条音频，成功返回 True，失败打印错误返回 False。
    最终文件统一保存为 <name>.mp3（data.ts 引用格式），
    Remotion/浏览器会根据文件头自动识别 WAV 或 MP3 内容。
    """
    tmp_path = OUTPUT_DIR / f"{name}.tmp"
    final_path = OUTPUT_DIR / f"{name}.mp3"   # data.ts 统一引用 .mp3
    try:
        actual_path = await engine.synthesize(text, speaker, tmp_path)

        # 统一重命名为 .mp3（内容可能是 WAV，浏览器会自动检测格式头）
        if actual_path.resolve() != final_path.resolve():
            actual_path.replace(final_path)

        duration = get_audio_duration_sec(str(final_path))
        fmt = actual_path.suffix.lstrip(".")        # 记录实际格式供参考
        print(f"  ✅  {name}.mp3  [{speaker:<5}]  {duration:.2f}s  ({fmt})")
        return True

    except Exception as exc:
        for leftover in [tmp_path, OUTPUT_DIR / f"{name}.wav"]:
            leftover.unlink(missing_ok=True)
        print(f"  ❌  {name} 失败: {exc}")
        return False


async def main() -> None:
    parser = argparse.ArgumentParser(description="生成对话音频并输出 Remotion props")
    parser.add_argument("--input", "-i", type=str, default="workspace/script.json", help="输入的剧本 JSON 文件")
    parser.add_argument("--output", "-o", type=str, default="public/data/render_props.json", help="输出的供 Remotion 使用的 props JSON")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ 找不到输入剧本: {args.input}")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    # 兼容旧版数组格式或新版本大字典格式
    if isinstance(script_data, list):
        qa_pairs = script_data
        intro_data = None
        outro_data = None
    else:
        qa_pairs = script_data.get("qa", [])
        intro_data = script_data.get("intro", None)
        outro_data = script_data.get("outro", None)

    engine_type = os.getenv("TTS_ENGINE", "edge")
    print(f"\n🎙️  Dialogue TTS 音频生成")
    print(f"   引擎  : {engine_type.upper()}")
    if engine_type == "aliyun":
        model = os.getenv("ALIYUN_TTS_MODEL", "qwen3-tts-flash")
        print(f"   模型  : {model}")
        voice_q = os.getenv("ALIYUN_VOICE_BUNNY", "Cherry")
        voice_a = os.getenv("ALIYUN_VOICE_FOX", "Ethan")
        print(f"   问    : bunny→ {voice_q}")
        print(f"   答    : fox  → {voice_a}")
    else:
        print(f"   问    : bunny→ {os.getenv('VOICE_BUNNY', 'zh-CN-XiaoxiaoNeural')}")
        print(f"   答    : fox  → {os.getenv('VOICE_FOX', 'zh-CN-YunxiNeural')}")
    print(f"   剧本  : {args.input}")
    print(f"   输出  : {args.output}")
    total = len(qa_pairs) * 2 + (1 if intro_data else 0) + (1 if outro_data else 0)
    print(f"   条数  : {total} 首音频")
    print("─" * 44)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        engine = build_engine(engine_type)
    except EnvironmentError as e:
        print(f"\n❌  引擎初始化失败:\n   {e}")
        sys.exit(1)

    failed: list[str] = []
    
    # 构建最终给 Remotion 的数据
    render_props = {
        "theme": intro_data,
        "outro": outro_data,
        "dataWithDurations": []
    }
    
    # -- 生成片头音频 (若存在) --
    FPS = 30
    MAX_SCENE_FRAMES = 150  # 片头/片尾最长 5 秒
    if intro_data and "audio" in intro_data:
        ok = await generate_one(engine, "intro", "fox", intro_data["audio"])
        if not ok:
            failed.append("intro")
        intro_dur = get_audio_duration_sec(str(OUTPUT_DIR / "intro.mp3"))
        intro_frames = max(30, int(intro_dur * FPS) + int(FPS * 0.5))
        render_props["theme"] = {
            **intro_data,
            "audioPath": "audio/intro.mp3",
            "durationFrames": intro_frames,
        }
        print(f"  🎥  intro: {intro_dur:.2f}s → {intro_frames} frames")
        
    # -- 生成片尾音频 (若存在) --
    if outro_data and "audio" in outro_data:
        ok = await generate_one(engine, "outro", "bunny", outro_data["audio"])
        if not ok:
            failed.append("outro")
        outro_dur = get_audio_duration_sec(str(OUTPUT_DIR / "outro.mp3"))
        outro_frames = max(30, int(outro_dur * FPS) + int(FPS * 0.5))
        render_props["outro"] = {
            **outro_data,
            "audioPath": "audio/outro.mp3",
            "durationFrames": outro_frames,
        }
        print(f"  🎥  outro: {outro_dur:.2f}s → {outro_frames} frames")

    for item in qa_pairs:
        name_q = item["name_q"]
        name_a = item["name_a"]
        
        # 提问者是 bunny，回答者是 fox
        q_ok = await generate_one(engine, name_q, "bunny", item["question"])
        a_ok = await generate_one(engine, name_a, "fox", item["answer"])

        if not q_ok: failed.append(name_q)
        if not a_ok: failed.append(name_a)
        
        # 写入 Remotion props 时，使用大字报展示文本 (_display)
        # 生成音频并计算帧数
        q_dur = get_audio_duration_sec(str(OUTPUT_DIR / f"{name_q}.mp3")) if q_ok else 0
        a_dur = get_audio_duration_sec(str(OUTPUT_DIR / f"{name_a}.mp3")) if a_ok else 0
        render_props["dataWithDurations"].append({
            "question": item.get("question_display", item["question"]),
            "answer": item.get("answer_display", item["answer"]),
            "character": "book" if item.get("character_q", "bunny") == "bunny" else "businessman",
            "qAudio": f"audio/{name_q}.mp3",
            "aAudio": f"audio/{name_a}.mp3",
            "qDur": q_dur,
            "aDur": a_dur,
            "visual_type": item.get("visual_type", "flow"),
            "visual_labels": item.get("visual_labels", []),
        })

    print("─" * 44)
    success = total - len(failed)

    if failed:
        print(f"⚠️  完成: {success}/{total}  失败项: {', '.join(failed)}")
        sys.exit(1)
    # -- 计算总帧数，供 Remotion calculateMetadata 直接使用 --
    FPS2 = 30
    total_frames = 0
    if render_props.get("theme", {}) and render_props["theme"].get("durationFrames"):
        total_frames += render_props["theme"]["durationFrames"]
    
    qa_count = len(render_props["dataWithDurations"])
    for qa in render_props["dataWithDurations"]:
        q_f = int(qa["qDur"] * FPS2)
        a_f = int(qa["aDur"] * FPS2)
        total_frames += q_f + int(FPS2 * 0.5) + a_f + int(FPS2 * 1.5)
        
    if render_props.get("outro", {}) and render_props["outro"].get("durationFrames"):
        total_frames += render_props["outro"]["durationFrames"]

    # Subtract Series overlaps (-15 offset per QA scene + Outro scene)
    overlap_count = qa_count
    if render_props.get("outro", {}) and render_props["outro"].get("durationFrames"):
        overlap_count += 1
    total_frames -= (overlap_count * 15)

    render_props["totalFrames"] = max(30, total_frames)
    print(f"  📊 总帧数: {total_frames} 帧 ({total_frames/FPS2:.1f}s)")

    # 写入最终的 render_props.json
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(render_props, f, ensure_ascii=False, indent=2)
    print(f"✅  全部完成！音频打包完毕，Props已保存至: {args.output}")

if __name__ == "__main__":
    asyncio.run(main())
