"""
Skill 2: dialogue-tts v2
多引擎 TTS，通过环境变量 TTS_ENGINE 选择引擎（edge | aliyun）。
音频路径改为相对路径，便于跨机器复用。
"""
import asyncio
import math
import os
from pathlib import Path

from mutagen.mp3 import MP3
from mutagen.wave import WAVE


# 视频帧率
FPS = 30


def get_audio_duration_sec(filepath: str) -> float:
    """读取 MP3/WAV 时长（秒）"""
    p = Path(filepath)
    try:
        if p.suffix.lower() == ".mp3":
            return MP3(filepath).info.length
        elif p.suffix.lower() in (".wav", ".wave"):
            return WAVE(filepath).info.length
    except Exception:
        pass
    # Fallback: 按文件大小估算（128kbps MP3）
    size = os.path.getsize(filepath)
    return size / (128 * 1024 / 8)


def _ensure_engines_package() -> str:
    """
    将 engines/ 目录注册为 Python 包（sys.modules），
    使其内部的相对导入（from .base import TTSEngine）在 importlib 动态加载场景下正常工作。
    返回包名称。
    """
    import sys, importlib.util as ilu

    pkg_name = "dialogue_tts_engines"
    engines_dir = Path(__file__).parent / "engines"

    if pkg_name not in sys.modules:
        # 注册包本身
        spec = ilu.spec_from_file_location(
            pkg_name,
            engines_dir / "__init__.py",
            submodule_search_locations=[str(engines_dir)],
        )
        pkg = ilu.module_from_spec(spec)
        pkg.__path__ = [str(engines_dir)]
        pkg.__package__ = pkg_name
        sys.modules[pkg_name] = pkg
        if spec.loader:
            spec.loader.exec_module(pkg)

        # 注册 base 子模块
        base_spec = ilu.spec_from_file_location(f"{pkg_name}.base", engines_dir / "base.py")
        base_mod = ilu.module_from_spec(base_spec)
        base_mod.__package__ = pkg_name
        sys.modules[f"{pkg_name}.base"] = base_mod
        base_spec.loader.exec_module(base_mod)

    return pkg_name


def _load_engine_module(name: str):
    """动态加载 engines/<name>.py，确保包上下文已注册。"""
    import sys, importlib.util as ilu

    pkg_name = _ensure_engines_package()
    full_name = f"{pkg_name}.{name}"
    engines_dir = Path(__file__).parent / "engines"

    if full_name not in sys.modules:
        spec = ilu.spec_from_file_location(full_name, engines_dir / f"{name}.py")
        mod = ilu.module_from_spec(spec)
        mod.__package__ = pkg_name
        sys.modules[full_name] = mod
        spec.loader.exec_module(mod)

    return sys.modules[full_name]


def build_engine(engine_type: str):
    """根据引擎类型实例化对应的 TTS 引擎"""
    t = engine_type.lower().strip()
    if t == "aliyun":
        mod = _load_engine_module("aliyun")
        return mod.AliyunTTSEngine()
    elif t == "edge":
        mod = _load_engine_module("edge")
        return mod.EdgeTTSEngine()
    else:
        raise ValueError(
            f"不支持的 TTS 引擎: '{t}'。\n"
            f"可选值: edge | aliyun\n"
            f"配置示例: TTS_ENGINE=aliyun"
        )


class DialogueTTSSkill:
    """
    为每条 exchange 生成配音，并测量时长。
    
    引擎选择优先级：
      1. 构造函数传入的 engine_type 参数
      2. 环境变量 TTS_ENGINE
      3. 默认: edge（免费，无需 API Key）
    """

    def __init__(
        self,
        audio_dir: str = "output/audio",
        engine_type: str | None = None,
    ):
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(parents=True, exist_ok=True)

        # 引擎选择
        _type = engine_type or os.getenv("TTS_ENGINE", "edge")
        self.engine = build_engine(_type)
        self._engine_type = _type
        print(f"    🔊 TTS 引擎: {_type.upper()}")

    async def _synthesize_one(self, exchange: dict) -> dict:
        """为单条 exchange 生成音频，返回带 audio 字段的 exchange"""
        ex_id = exchange["id"]
        speaker = exchange.get("speaker", "fox")
        text = exchange["text"]

        # 引擎输出（后缀由引擎决定，阿里云→WAV，Edge→MP3）
        raw_path = self.audio_dir / f"{ex_id}.tmp"
        actual_path = await self.engine.synthesize(text, speaker, raw_path)

        # 测量时长，加 10 帧缓冲避免音频被截断
        duration_sec = get_audio_duration_sec(str(actual_path))
        duration_frames = math.ceil(duration_sec * FPS) + 10

        # ── 关键修复：存储相对路径（相对于 audio_dir 父目录，即 output/）────
        # 这样 JSON 文件可以跨机器复用，不依赖绝对路径
        rel_path = f"audio/{actual_path.name}"

        print(f"    [{ex_id}] {speaker}: {text[:20]}... → {duration_sec:.2f}s ({duration_frames}f)")

        return {
            **exchange,
            "audio": {
                "file": rel_path,          # 相对路径（相对于 output/ 目录）
                "duration_sec": round(duration_sec, 3),
                "duration_frames": duration_frames,
            },
        }

    async def run(self, dialogue: dict) -> dict:
        """
        为所有 exchanges 生成配音。
        返回带 audio 字段的完整 dialogue dict。
        """
        exchanges = dialogue.get("exchanges", [])

        # 并发生成所有配音
        tasks = [self._synthesize_one(ex) for ex in exchanges]
        enriched_exchanges = await asyncio.gather(*tasks)

        # 计算总帧数（含结尾卡）
        total_frames = sum(ex["audio"]["duration_frames"] for ex in enriched_exchanges)
        total_sec    = sum(ex["audio"]["duration_sec"]    for ex in enriched_exchanges)
        ending_frames = dialogue.get("ending", {}).get("duration_frames", 90)
        total_frames  += ending_frames

        return {
            **dialogue,
            "meta": {
                **dialogue.get("meta", {}),
                "total_frames": total_frames,
                "total_duration_sec": round(total_sec, 2),
                "tts_engine": self._engine_type,
            },
            "exchanges": list(enriched_exchanges),
        }
