"""TTS 引擎抽象基类"""
from abc import ABC, abstractmethod
from pathlib import Path


class TTSEngine(ABC):
    """
    所有 TTS 引擎的统一接口。
    子类实现 synthesize() 即可接入主调度器。
    """

    @abstractmethod
    async def synthesize(self, text: str, speaker: str, output_path: Path) -> Path:
        """
        将文本合成为语音文件。

        Args:
            text:        要合成的文本
            speaker:     角色标识（'bunny' 或 'fox'）
            output_path: 输出文件路径（.mp3 或 .wav）

        Returns:
            实际保存的文件路径（可能与 output_path 后缀不同）
        """
        ...
