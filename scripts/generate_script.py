#!/usr/bin/env python3
import os
import sys
import json
import argparse
from pathlib import Path

try:
    from dotenv import load_dotenv
    import openai
except ImportError:
    print("❌ 请确保已安装依赖: pip install python-dotenv openai")
    sys.exit(1)

# 加载环境变量
load_dotenv()

# 读取 OpenAI 配置
# 如果没有独立设置 OPENAI_...，可以 fallback 到 DASHSCOPE 方案
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
MODEL = os.getenv("OPENAI_MODEL", "qwen-plus")

if not API_KEY:
    print("❌ 错误: 未能在 .env 中找到 OPENAI_API_KEY 或 DASHSCOPE_API_KEY")
    sys.exit(1)

client = openai.OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)

SYSTEM_PROMPT = """你是一个专业的技术科普短视频剧本作家。
用户的输入将是一篇技术文档或一段技术主题说明。
你的任务是将这些核心概念转化为一段完整的短视频剧本，包含“片头引首”、“4-5轮渐进问答”以及“片尾总结引流”三个部分。

要求：
1. 【片头 Intro】：提炼最凝练直白的主题字眼作为第一级大字视觉（theme_title），然后辅以稍微具备说明性的副标题（theme_subtitle）。并用一句话口播引出本期内容。
2. 【正片 QA】：提取文档核心概念，改为 4-5 个连续互相呼应的 Q&A 回合（Q: 问题，A: 回答）。
   - Q、A分别有 `question`（听觉口播长文本）和 `question_display`（视觉极简大字报文本）。
   - _display 文本里允许在核心词包裹 `<hl>关键</hl>` 标签（不超过5个字）。
   - Q 的角色固定为 "fox"，A 固定为 "bunny"。
3. 【片尾 Outro】：精简提炼 **2-3 条**核心知识点（不要过多）作为画面展示，并在口播文案尾部带上“关注我，获取更多面试资料和面试指导”的引流话术。片尾口播要简短，不超过 2-3 句。
4. 输出格式必须严格是含有JSON的文本，**返回一个 JSON 对象**而不是数组。直接回复纯 JSON 对象（可以使用 ```json 格式块）。

JSON 格式要求：
{
    "intro": {
        "theme_title": "极简震撼的主标题，如：今日对话 / 底层逻辑 等",
        "theme_subtitle": "带书名号或陈述的副标，如：《什么是 RSC》",
        "audio": "（fox发音用）嗨，今天咱们来聊聊... 这个热门概念！"
    },
    "qa": [
        {
            "name_q": "q1",
            "name_a": "a1",
            "question": "（TTS发音用）完整的发问原话，语气自然好奇？",
            "answer": "（TTS发音用）完整细致的解释说明原话，娓娓道来。",
            "question_display": "精简版问题？",
            "answer_display": "精简的<hl>高亮</hl>回答总结。",
            "character_q": "fox",
            "character_a": "bunny"
        }
    ],
    "outro": {
        "summary_display": "- 精简总结点一（最多2-3条，不要超过3条）\\n- 精简总结点二\\n- 精简总结点三（可选）",
        "audio": "（bunny发音用）简短1-2句总结。关注我，获取更多面试资料和面试指导！"
    }
}
"""

def generate_script(input_text: str, output_path: str):
    print(f"🔄 正在通过模型 [{MODEL}] 提取剧本...")
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"请将以下文档转化为对话剧本:\n\n{input_text}"}
        ],
        temperature=0.7,
        max_tokens=2048
    )
    
    content = response.choices[0].message.content.strip()
    
    # 清理 markdown json code blocks (如果存在)
    if content.startswith("```json"):
        content = content[7:]
    if content.endswith("```"):
        content = content[:-3]
    
    content = content.strip()
    
    try:
        data = json.loads(content)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"✅ 成功生成剧本，已保存至 {output_path}")
        print(f"   共 {len(data)} 个问答回合。")
        return data
        
    except json.JSONDecodeError as e:
        print(f"❌ 解析大模型返回的 JSON 失败:\n{e}\n\n大模型返回内容:\n{content}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="根据输入文档生成问答剧本 (JSON)")
    parser.add_argument("--input", "-i", type=str, required=True, help="输入的 markdown/txt 文件路径")
    parser.add_argument("--output", "-o", type=str, default="workspace/script.json", help="输出的 JSON 文件路径")
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"❌ 找不到输入文件: {args.input}")
        sys.exit(1)
        
    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()

    generate_script(text, args.output)
