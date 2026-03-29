"""
阿里云千问 TTS 引擎（基于官方文档）

正确 API：dashscope.MultiModalConversation.call()
  - 非流式：返回 response.output.audio.url，下载 WAV 文件
  - 必须设置 dashscope.base_http_api_url（北京地域）

参考：src/dialogue-tts/阿里千问tts.md  §"非流式输出 Python"
"""
import asyncio
import os
import urllib.request
from pathlib import Path

from .base import TTSEngine

# 官方北京地域 API 地址（必填，否则请求会打到错误节点）
ALIYUN_BASE_HTTP_API_URL = "https://dashscope.aliyuncs.com/api/v1"

DEFAULT_VOICES = {
    "bunny": "Cherry",   # 芊悦：阳光积极小姐姐
    "fox":   "Ethan",    # 晨煦：阳光温暖男生
}

MAX_RETRIES = 3


class AliyunTTSEngine(TTSEngine):
    """
    阿里云千问 TTS 引擎。
    使用 dashscope.MultiModalConversation.call() 非流式合成，
    从返回 URL 下载 WAV 文件到本地，自动重试最多 3 次。
    """

    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise EnvironmentError(
                "使用阿里云 TTS 需要设置环境变量 DASHSCOPE_API_KEY。\n"
                "获取 API Key: https://bailian.console.aliyun.com/"
            )

        self.model = os.getenv("ALIYUN_TTS_MODEL", "qwen3-tts-flash")
        self.voices = {
            "bunny": os.getenv("ALIYUN_VOICE_BUNNY", DEFAULT_VOICES["bunny"]),
            "fox":   os.getenv("ALIYUN_VOICE_FOX",   DEFAULT_VOICES["fox"]),
        }
        # 仅 instruct 模型支持 instructions 参数
        self.instructions = os.getenv("ALIYUN_TTS_PROMPT", None)

    async def synthesize(self, text: str, speaker: str, output_path: Path) -> Path:
        voice = self.voices.get(speaker, DEFAULT_VOICES["fox"])
        wav_path = output_path.with_suffix(".wav")

        last_err: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                audio_url = await asyncio.get_event_loop().run_in_executor(
                    None, self._call_api, text, voice
                )
                await asyncio.get_event_loop().run_in_executor(
                    None, urllib.request.urlretrieve, audio_url, str(wav_path)
                )
                return wav_path

            except Exception as e:
                last_err = e
                if attempt < MAX_RETRIES - 1:
                    wait = 2 ** attempt        # 1s → 2s → 4s
                    print(f"      ⚠️  重试 {attempt + 1}/{MAX_RETRIES}（等待 {wait}s）: {e}")
                    await asyncio.sleep(wait)

        raise RuntimeError(
            f"Aliyun TTS 失败（已重试 {MAX_RETRIES} 次）: {last_err}"
        )

    def _call_api(self, text: str, voice: str) -> str:
        """
        同步调用 MultiModalConversation.call()，返回音频下载 URL。
        URL 24小时内有效，格式为 WAV。
        """
        import dashscope

        # 必须设置北京地域接入点（文档要求）
        dashscope.base_http_api_url = ALIYUN_BASE_HTTP_API_URL

        # 组装参数（instruct 模型额外支持 instructions）
        call_kwargs: dict = dict(
            model=self.model,
            api_key=self.api_key,
            text=text,
            voice=voice,
            language_type="Chinese",   # 与文本语种一致，获得正确发音和语调
            stream=False,
        )
        if self.instructions and "instruct" in self.model:
            call_kwargs["instructions"] = self.instructions
            call_kwargs["optimize_instructions"] = True

        response = dashscope.MultiModalConversation.call(**call_kwargs)

        # 提取音频 URL
        try:
            audio_url = response.output.audio.url
        except AttributeError:
            raise RuntimeError(
                f"API 响应格式异常，无法提取音频 URL。\n"
                f"响应内容: {response}\n"
                f"请检查 DASHSCOPE_API_KEY 与 ALIYUN_TTS_MODEL 是否匹配。"
            )

        if not audio_url:
            raise RuntimeError(
                f"API 返回了空的音频 URL。\n"
                f"响应内容: {response}"
            )

        return audio_url
