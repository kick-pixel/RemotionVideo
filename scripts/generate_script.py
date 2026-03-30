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

# ── Step 1 Prompt：忠实于文章主旨，提炼选题 ─────────────────────────────────
#
# 核心策略：
#   文章标题 + 引言 = 作者最想表达的核心主旨，必须优先尊重。
#   3~4轮QA的叙事结构要求：
#     Q1 → 建立"为什么会有这个问题"的认知（痛点 + 根因）
#     Q2 → 揭示"核心解法框架是什么"（文章主旨的核心技术方案全貌）
#     Q3 → 深挖"最值得面试官追问的技术细节"（有具体的对比/因果/数字）
#     Q4 → (可选) 补充的高阶思辨或扩展细节
#
ANALYSIS_PROMPT = """你是一个技术短视频选题专家。请对以下技术文档进行分析，输出一份"剧本选题规划"。

━━━━━━━━━━━━━━━━【分析规则 - 必须严格遵守】━━━━━━━━━━━━━━━━

**第一原则：忠实于文章主旨**
文章的标题和引言明确告诉你这篇文章在讲什么——这是作者认为最重要的内容，必须作为剧本核心主题。
不要用"找最硬核技术细节"的思路来绕过或替换文章的显式主题。

**叙事结构（规划 3 到 4 轮，视文档深度而定）**：

【Q1 - 建立问题认知】
  目标：让观众理解"为什么会有这个问题？根因是什么？"
  内容来源：文章的问题描述章节（通常是第2章前半段）
  要求：说清楚痛点场景 + 根因诊断，不要只说"这题考架构思维"这种泛话

【Q2 - 核心解法框架】
  目标：让观众看清"文章的核心解法体系全貌"——这是文章价值最高的部分
  内容来源：文章的核心方案章节（通常是提出"X大套件/Y层架构"的总览章节）
  要求：必须说出解法体系的"结构感"，让人清楚有几个层次、分别解决什么问题

【Q3 - 深入技术细节】
  目标：深挖具体的对比关系或因果逻辑
  内容来源：架构中的某个重要组件/机制
  要求：必须有具体的技术名词、有对比关系（A vs B）或因果关系（因为X所以Y）

【Q4 - 最佳面试追问（可选）】
  目标：如果前3轮不足以讲透，补充最反直觉的技术考察点或收尾总结
  要求：用充满压迫感的追问或进阶场景收尾，制造深度感

━━━━━━━━━━━━━━━━【输出格式】━━━━━━━━━━━━━━━━

请输出以下项，纯文字，无需JSON：

**核心主题**：（一句话，直接描述文章最想传达的知识点，忠实于标题表述）

**Q1 选题**
- 问题：bunny 如何提问（口语化，带好奇/困惑感）
- 要点：fox 用1-2句话的核心回答
- 来源章节：

**Q2 选题**
- ...以此类推

（如果有必要，可输出 Q4 选题）
"""

# ── Step 2 Prompt：基于选题规划生成最终剧本 ───────────────────────────────
SCRIPT_PROMPT = """你是一个专业的技术科普短视频剧本作家。

【任务】
根据提供的"技术文档"和"选题规划"，生成完整的短视频对话剧本。
剧本必须严格按照选题规划的3-4轮主题展开，严禁自行替换或注水。
**最高指令**：单轮问答的总时长必须控制在20秒以内！所以文案必须极其精炼，短平快！

【格式要求】

1. 片头 Intro
- theme_title：3-5字的极简主标题（直接提炼文章核心关键词，如"七大套件"、"架构三件套"）
- theme_subtitle：带书名号的补充说明（如《1000万订单查询优化》）
- audio：≤15字的打招呼开场，必须先问候再点题，例如："哈喽大家好，今天聊聊xxx" / "hello大家好，面试官问你xxx怎么破？"

2. 正片 QA（3 到 4 轮，严格按选题规划）
- question（bunny口播）：必须严格控制在 20 个字以内！一句话，单刀直入抛出痛点或反常识疑问
- question_display：极简大字报，核心词用 <hl>关键词</hl>（≤5字）
- answer（fox口播）：必须严格控制在 50 个字以内！务必精炼惜字如金！只讲干货，不能展开！
  - 口语节奏：每≤10字加标点，多用"，"制造短停顿，增强网感
  - 常用语气："其实啊"、"简单来说"、"核心在于"
- answer_display：一句结论，核心词用 <hl>关键词</hl>
- visual_type + visual_labels（必须精准匹配，见下方决策树）

【visual_type 决策树】

▸ "flow" → 数据/请求从A流向B的传递链路（如：请求→服务→DB）
  labels: 3个节点名（按流向顺序）

▸ "database" → 存储结构/缓存层级/多存储协同
  labels: 2个存储对象（如：["Redis", "MySQL"]）

▸ "speed" → 性能对比（延迟/吞吐量/QPS数字级别的差异）
  labels: 2个对比项，左=慢，右=快

▸ "code" → 具体API/配置语法/命令
  labels: [指令名(≤10字符), 简短说明]

▸ "compare" → 两套方案的优劣/取舍/新旧对比
  labels: [左=旧/差, 右=新/好]

▸ "layers" → 分层架构（从上到下有明确层次的体系）
  labels: 3个层名（从上到下）

▸ "tree" → 父子/依赖/分类/体系树
  labels: [根节点, 左子, 右子]

▸ "timeline" → 必须按顺序发生的步骤/时序
  labels: 3个顺序步骤

▸ "lock" → 鉴权/加密/安全/Token
  labels: [机制名, 简短说明]

labels 规范：每个词严格不超过4个字（宁可缩写也不写长词）
❌ 错误: ["HBase行存点查", "ClickHouse列存分析"]  → 太长
✅ 正确: ["HBase", "ClickHouse"] 或 ["行存点查", "列存分析"]

3. 片尾 Outro
- summary_display：2-3条核心知识点（高度概括）
- audio：1-2句总结 + "关注我，获取更多面试资料和面试指导！"

【输出格式】：纯 JSON 对象，可用 ```json 代码块。
注意：所有字符串的 value 必须用双引号 `"` 包裹，不能因为中文字符缺失外层双引号。
{
  "intro": {
    "theme_title": "极简3-5字标题",
    "theme_subtitle": "《补充说明》",
    "audio": "≤15字打招呼开场"
  },
  "qa": [
    {
      "name_q": "q1", "question": "≤20字单刀直入提问",
      "question_display": "极简大字 <hl>核心词</hl>",
      "character_q": "bunny",
      "name_a": "a1", "answer": "≤50字极简回答，必须克制字数",
      "answer_display": "一句结论 <hl>关键词</hl>",
      "character_a": "fox",
      "visual_type": "layers",
      "visual_labels": ["层A", "层B", "层C"]
    }
  ],
  "outro": {
    "summary_display": "- 总结点一\\n- 总结点二\\n- 总结点三",
    "audio": "简短总结。关注我，获取更多面试资料和面试指导！"
  }
}
"""


def analyze_document(input_text: str) -> str:
    """Step 1：忠实于文章主旨，规划3轮QA选题。"""
    print(f"  🔍 [Step 1/2] 分析文章主旨，规划剧本选题...")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": ANALYSIS_PROMPT},
            {"role": "user", "content": f"请分析以下技术文档并规划剧本选题：\n\n{input_text}"}
        ],
        temperature=0.2,   # 分析任务用低温，确保忠实于文章主旨
        max_tokens=1500
    )
    analysis = response.choices[0].message.content.strip()
    print(f"  ✅ 选题规划完成")
    return analysis


def generate_script(input_text: str, output_path: str):
    print(f"🔄 正在通过模型 [{MODEL}] 生成剧本...")

    # ── Step 1：分析文章主旨，确定选题 ─────────────────────────────────────
    analysis_report = analyze_document(input_text)

    # ── Step 2：按选题规划生成剧本 ──────────────────────────────────────────
    print(f"  ✍️  [Step 2/2] 按选题规划生成对话剧本...")
    user_message = f"""请将以下技术文档转化为对话剧本。

━━━━【文档内容】━━━━
{input_text}

━━━━【选题规划（必须严格遵守，禁止替换主题）】━━━━
{analysis_report}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
约束：
- QA的主题轮次（3到4轮） = 严格跟随选题规划，不得更换
- Q2 必须呈现出解法体系的"结构感"
- 直接输出 JSON，不输出分析过程
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SCRIPT_PROMPT},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        max_tokens=2048
    )

    content = response.choices[0].message.content.strip()

    # 清理 markdown json code blocks（支持多种包裹方式）
    import re as _re
    # 先尝试提取 ```json ... ``` 块
    json_block = _re.search(r'```json\s*([\s\S]*?)```', content)
    if json_block:
        content = json_block.group(1).strip()
    else:
        # fallback：逐行去掉 ``` 围栏
        for prefix in ("```json", "```"):
            if content.startswith(prefix):
                content = content[len(prefix):]
        if content.endswith("```"):
            content = content[:-3]
    content = content.strip()

    # 尝试修复《...》导致的 JSON 双引号缺失
    content = _re.sub(r'"theme_subtitle":\s*《(.*?)》', r'"theme_subtitle": "《\1》"', content)
    # 也可能出现在其它地方，泛型修复缺引号的《...》
    content = _re.sub(r'(:\s*)《(.*?)》', r'\1"《\2》"', content)

    try:
        data = json.loads(content)

        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        qa_count = len(data.get("qa", []))
        print(f"✅ 成功生成剧本，已保存至 {output_path}")
        print(f"   共 {qa_count} 个问答回合。")
        return data

    except json.JSONDecodeError as e:
        print(f"❌ 解析大模型返回的 JSON 失败:\n{e}")
        debug_path = os.path.join(os.path.dirname(output_path) or ".", "debug_raw.txt")
        with open(debug_path, "w", encoding="utf-8") as df:
            df.write(content)
        print(f"大模型返回内容已保存至: {debug_path}")
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
