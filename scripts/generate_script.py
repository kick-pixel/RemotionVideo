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
1. 【片头 Intro】：提炼最凝练直白的主题字眼作为第一级大字视觉（theme_title），然后辅以稍微具备说明性的副标题（theme_subtitle）。配上一句**极度简短（控制在10-15个字左右，3秒内能说完）的口播引出本期内容。必须先打招呼再引出主题**，例如使用这种口语化句式：“哈喽大家好，今天咱们一起聊聊xxx” 或者 “hello大家好，面试官问你xxx，怎么破？”。
2. 【正片 QA】：提取文档核心概念，改为 4-5 个连续互相呼应的 Q&A 回合（Q: 问题，A: 回答）。
   - Q、A分别有 `question`（听觉口播长文本）和 `question_display`（视觉极简大字报文本）。
   - _display 文本里允许在核心词包裹 `<hl>关键</hl>` 标签（不超过5个字）。
   - Q 的角色固定为 "bunny"（提问者），A 固定为 "fox"（解答专家）。
   - **极其重要（自然流利口语化）**：口播文本（`question` 和 `answer`）**绝对不要**像在读死板的课文或说明书！必须使用**极为自然的聊天播客语气**交谈！
     - 多用真实对话场景的语气词和口语连接词（例如：“哎，那是不是说……”、“哇，那可太方便了”、“其实啊”、“对对对”、“简单来说就是……”、“这就有意思了”、“哦~ 原来是这样”等）。
     - 把长句拆解成日常说话的短句，带一点人情味和互动感，让两者的对话自然、生动、不干瘪。
     - 避免过分生硬严肃的学术背书感，想象是两个极客日常边喝咖啡边热烈探讨问题的状态。
   - **动态图解参数（极其重要，必须严格按照以下决策规则选择）**：视频右下角会根据你的参数自动渲染一个科技感动图。请根据本回合**回答的核心语义**，从以下9种类型中精准选择一种：

      **【type 选择决策树 - 必须严格对号入座，禁止随意猜测】**:
      
      ▸ 选 `"flow"` → 回答涉及：**请求/数据从A到B的传递过程**、**系统组件间的调用链**、**渲染/工作流程**、**架构拓扑**
        渲染效果：3个方框节点从左到右用连线连起来，节点上显示labels中的词
        适用例：RSC渲染流程、API调用链路、Nginx→后端→DB、事件从发出到消费
        labels：3个流程节点，顺序即流程顺序。例：`["浏览器", "服务端", "DB"]`

      ▸ 选 `"database"` → 回答涉及：**缓存/存储方式**、**数据库结构**、**存储层级**、**连接池/Buffer/Cache**
        渲染效果：磁盘圆柱堆叠图，旁边贴两个浮动标签
        适用例：Redis缓存穿透、MySQL索引、连接池复用、多级缓存
        labels：2个核心存储对象名。例：`["Redis", "MySQL"]` 或 `["热数据", "冷数据"]`

      ▸ 选 `"speed"` → 回答涉及：**性能快慢对比**、**延迟/耗时减少**、**吞吐量提升**、**具体数字化性能差距**
        渲染效果：圆形仪表盘+摆动指针，左右各一个对比标签
        适用例：首屏从3s到0.3s、接口从200ms到20ms、QPS翻10倍
        labels：2个对比项，左=慢/旧，右=快/新。例：`["传统SSR", "RSC"]`

      ▸ 选 `"code"` → 回答涉及：**具体API/指令语法**、**函数调用方式**、**协议/格式规范**、**配置项写法**
        渲染效果：大字体 `<label />` 代码括号样式，下方贴一个术语标签
        适用例：use client指令、async/await用法、Dockerfile语法、HTTP头规范
        labels：index 0=API/指令名（不超过10字符），index 1=简短说明。例：`["use client", "客户端"]`

      ▸ 选 `"compare"` → 回答涉及：**两种方案的优劣对比**、**有/无某功能的差异**、**新旧技术的取舍**
        渲染效果：左右两块卡片并排，中间有VS分割线，左=旧/坏，右=新/好
        适用例：有缓存vs无缓存、CSR vs SSR、monolith vs 微服务、加锁vs无锁
        labels：index 0=左侧（旧/差），index 1=右侧（新/好）。例：`["CSR", "SSR"]`

      ▸ 选 `"layers"` → 回答涉及：**技术分层架构**、**抽象层级**、**OSI模型/协议栈**、**前端/后端/基础设施的层次关系**
        渲染效果：3层堆叠的矩形，从上到下颜色渐深，每层显示一个名称
        适用例：前端→后端→DB三层架构、React组件树、容器层/运行时层/内核层
        labels：3个层名，从上到下排列。例：`["前端", "后端", "数据库"]`

      ▸ 选 `"tree"` → 回答涉及：**父子关系/继承**、**组件树/依赖图**、**分类/分支结构**、**递归拆解**
        渲染效果：1个根节点在上，下方用弧线分连2个子节点
        适用例：React组件树、类继承关系、目录结构、算法分治
        labels：index 0=根节点，index 1=左子节点，index 2=右子节点。例：`["App", "Header", "Body"]`

      ▸ 选 `"timeline"` → 回答涉及：**事件执行顺序**、**生命周期钩子先后**、**异步操作时序**、**步骤必须按顺序发生**
        渲染效果：横向时间轴，3个步骤点依次弹出，标签交替上下显示
        适用例：async/await执行顺序、React生命周期、Webpack打包流程、请求→响应→渲染
        labels：3个按顺序的步骤名。例：`["请求", "处理", "响应"]`

      ▸ 选 `"lock"` → 回答涉及：**身份验证/鉴权**、**加密/解密**、**Token/密钥**、**权限控制**、**安全协议**
        渲染效果：锁形图标居中，两条椭圆轨道持续旋转，代表加密保护
        适用例：JWT签名、OAuth2授权、HTTPS握手、RBAC权限、密码Hash
        labels：index 0=核心安全机制名，index 1=作用说明。例：`["JWT", "鉴权"]`

      **【labels 统一规范 - 每个词严格不超过5个字，不要写长句】**：
      ❌ 错误：`["首屏极速加载体验", "服务端渲染无JS"]`  
      ✅ 正确：`["传统SSR", "RSC"]` 或 `["浏览器", "服务端", "DB"]`
3. 【片尾 Outro】：精简提炼 **2-3 条**核心知识点（不要过多）作为画面展示，并在口播文案尾部带上“关注我，获取更多面试资料和面试指导”的引流话术。片尾口播要简短，不超过 2-3 句。
4. 输出格式必须严格是含有JSON的文本，**返回一个 JSON 对象**而不是数组。直接回复纯 JSON 对象（可以使用 ```json 格式块）。

JSON 格式要求：
{
    "intro": {
        "theme_title": "极简震撼的主标题，如：今日对话 / 底层逻辑",
        "theme_subtitle": "带书名号或陈述的副标，如：《什么是 RSC》",
        "audio": "（fox发音用）自然的打招呼开场，如：hello大家好，今天咱们彻底把 RSC 盘明白！"
    },
    "qa": [
        {
            "name_q": "q1",
            "question": "（bunny发音用满怀好奇的口吻）哎，我听说最近有个...",
            "question_display": "听说的这个 <hl>新技术</hl> 是啥？",
            "character_q": "bunny",
            "name_a": "a1",
            "answer": "（fox发音用轻松解答的口吻）哈哈，这个其实不复杂，简单来说就是...",
            "answer_display": "就是前段渲染在 <hl>服务端</hl>",
            "character_a": "fox",
            "visual_type": "flow",
            "visual_labels": ["客户端", "服务端", "DB"]
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
