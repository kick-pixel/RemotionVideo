# 🎬 Tech Video Pipeline

> 输入一篇技术文档，自动输出一条科普对话短视频。

```
技术文档 (.md/.txt)
    │
    ▼
[LLM] scripts/generate_script.py
    │  提取 3 轮渐进问答 + 片头片尾 → workspace/script.json
    ▼
[TTS] gen_audio.py
    │  Edge / 阿里云 TTS 合成语音 → public/audio/*.mp3
    │  计算帧数 → public/data/render_props.json
    ▼
[Remotion] npm run build:dynamic
    │  React 动画渲染 + 音频合帧
    ▼
  out/<名称>.mp4
```

---

## 快速开始

### 1. 安装依赖

```bash
# Node 依赖（Remotion 渲染）
npm install

# Python 依赖（LLM + TTS）
pip install python-dotenv openai edge-tts mutagen
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，至少填写 OPENAI_API_KEY（或 DASHSCOPE_API_KEY）
```

`.env` 关键配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | LLM API Key（必填） | — |
| `OPENAI_BASE_URL` | 自定义 API Base URL | OpenAI 官方 |
| `OPENAI_MODEL` | 使用的模型名 | `gpt-4o-mini` |
| `TTS_ENGINE` | TTS 引擎：`edge` / `aliyun` | `edge` |
| `DASHSCOPE_API_KEY` | 阿里云 Key（TTS_ENGINE=aliyun 时必填） | — |

### 3. 一键生成

```bash
python make_video.py docs/my_article.md
```

视频自动输出到 `out/my_article.mp4`。

---

## `make_video.py` 完整用法

```
用法: python make_video.py <INPUT> [选项]

位置参数:
  INPUT                   技术文档路径（.md 或 .txt）

选项:
  -o, --output OUT        最终视频输出路径（默认：out/<文件名>.mp4）
  --script-json PATH      LLM 剧本 JSON 路径（默认：workspace/script.json）
  --props-json PATH       Remotion props JSON（默认：public/data/render_props.json）
  --skip-script           跳过 LLM 生成，复用已有 workspace/script.json
  --skip-audio            跳过 TTS 合成，复用已有音频文件
  --skip-render           仅生成音频，不执行 Remotion 渲染
  --open                  渲染完成后自动打开视频
  -h, --help              显示帮助
```

### 常用场景示例

```bash
# 完整流程：一键从文档到视频
python make_video.py docs/rsc.md

# 自定义输出路径
python make_video.py docs/rsc.md -o out/rsc_video.mp4

# 只改了文档，重新走完整流程
python make_video.py docs/rsc_v2.md

# 剧本已满意，只重新合成音频和渲染
python make_video.py docs/rsc.md --skip-script

# 音频已满意，只重新渲染（最快）
python make_video.py docs/rsc.md --skip-script --skip-audio

# 只生成剧本和音频，暂不渲染（测试用）
python make_video.py docs/rsc.md --skip-render

# 完成后自动打开
python make_video.py docs/rsc.md --open
```

---

## 单步手动运行

如需单独运行某个阶段：

```bash
# 阶段 1：LLM 剧本生成
python scripts/generate_script.py --input docs/my_article.md --output workspace/script.json

# 阶段 2：TTS 音频合成
python gen_audio.py --input workspace/script.json --output public/data/render_props.json

# 阶段 3：Remotion 渲染
npm run build:dynamic
# 等价于：
npx remotion render src/index.ts ArkFAQ out/video.mp4 --props public/data/render_props.json
```

---

## 项目结构

```
RemotionVideo/
├── make_video.py          # 🚀 一键入口（从这里开始）
├── gen_audio.py           # TTS 音频合成引擎
├── agent.py               # 旧版管线（已由 make_video.py 替代）
│
├── scripts/
│   └── generate_script.py # LLM 剧本生成
│
├── src/                   # Remotion React 源码
│   ├── index.ts
│   ├── Root.tsx
│   ├── ArkFAQVideo.tsx
│   └── components/
│       ├── FAQScene.tsx
│       ├── IntroScene.tsx
│       ├── OutroScene.tsx
│       ├── DynamicVisual.tsx
│       └── AnimatedText.tsx
│
├── public/
│   ├── audio/             # TTS 生成的 mp3 文件
│   └── data/
│       └── render_props.json  # Remotion 渲染用 props
│
├── workspace/
│   └── script.json        # LLM 生成的剧本（中间产物）
│
├── out/                   # 最终视频输出
├── .env                   # 环境配置（不提交 Git）
└── .env.example           # 配置模板
```

---

## 视觉类型参考

视频右下角的动态图解由 `visual_type` + `visual_labels` 控制，共 9 种：

| 类型 | 适用场景 | labels 数量 |
|------|----------|-------------|
| `flow` | 数据流/请求链路 | 3（节点顺序） |
| `database` | 缓存/存储结构 | 2（存储对象名） |
| `speed` | 性能对比 | 2（慢→快） |
| `code` | API/语法说明 | 2（指令名, 说明） |
| `compare` | 方案对比 | 2（旧/坏, 新/好） |
| `layers` | 分层架构 | 3（上→下） |
| `tree` | 父子/依赖关系 | 3（根, 左子, 右子） |
| `timeline` | 时序/生命周期 | 3（按顺序步骤） |
| `lock` | 鉴权/安全/加密 | 2（机制名, 说明） |

---

## Remotion Studio（实时预览）

```bash
npm run dev
# 打开浏览器 http://localhost:3000
```

---

## 常见问题

**Q: 渲染时报 `TypeError: Cannot read properties of undefined (reading 'length')`**
A: Node.js v22 的 Webpack wasm-hash 已知 bug，已在 `remotion.config.ts` 中通过 `hashFunction: "xxhash64"` 修复。

**Q: LLM 返回非 JSON 内容**
A: 检查 `.env` 中的 `OPENAI_MODEL`，部分低版本模型 JSON 输出不稳定，推荐使用 `qwen-plus` 或 `gpt-4o-mini`。

**Q: Edge TTS 超时**
A: 网络问题，重新运行 `--skip-script` 跳过已完成的剧本生成阶段，只重跑音频。
