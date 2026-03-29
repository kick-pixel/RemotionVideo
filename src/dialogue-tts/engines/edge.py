"""Edge TTS 引擎（免费，无需 API Key）— 带重试逻辑"""
import asyncio
import os
from pathlib import Path

import edge_tts

from .base import TTSEngine

DEFAULT_VOICES = {
    "bunny": "zh-CN-XiaoxiaoNeural",   # 小白：甜美女声
    "fox":   "zh-CN-YunxiNeural",       # 大橘：清晰男声
}

MAX_RETRIES = 3


class EdgeTTSEngine(TTSEngine):
    """使用 Microsoft Edge TTS（免费）的引擎，内置重试逻辑。"""

    def __init__(self):
        self.voices = {
            "bunny": os.getenv("VOICE_BUNNY", DEFAULT_VOICES["bunny"]),
            "fox":   os.getenv("VOICE_FOX",   DEFAULT_VOICES["fox"]),
        }

    async def synthesize(self, text: str, speaker: str, output_path: Path) -> Path:
        voice = self.voices.get(speaker, DEFAULT_VOICES["fox"])
        mp3_path = output_path.with_suffix(".mp3")

        last_err: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                # 增加 '+15%' 的语速，让语气更连贯、更有播客的活力感
                communicate = edge_tts.Communicate(text, voice, rate="+15%")
                await communicate.save(str(mp3_path))
                return mp3_path
            except Exception as e:
                last_err = e
                if attempt < MAX_RETRIES - 1:
                    wait = 1.5 * (attempt + 1)   # 1.5s → 3s
                    print(f"      ⚠️  重试 {attempt + 1}/{MAX_RETRIES}（等待 {wait:.1f}s）: {e}")
                    await asyncio.sleep(wait)

        raise RuntimeError(f"Edge TTS 失败（已重试 {MAX_RETRIES} 次）: {last_err}")
