# CLAUDE.md

本文档给 Claude Code 使用，用于在未来会话中快速理解本项目的背景、约定与协作方式。面向人类的说明请看 [README.md](./README.md)。

---

## 1. 项目定位

**pyqbot** 是基于 [qq-botpy](https://bot.q.qq.com/wiki/develop/pythonsdk/) 的 QQ 机器人项目，**同时也是一个 Python 学习项目**。

> ⚠️ 这不是生产项目，是学习项目。这个定位会直接影响你写代码、写文档、提建议的方式。

- 作者正在学习 Python 工程化（异步、OOP、装饰器、反射、插件架构、第三方 API 对接等）
- 代码与文档要能"看懂并举一反三"，而不是追求生产级健壮性
- 写完代码要主动讲**学习点**（这段用了哪些 Python 特性），不要只讲业务逻辑
- 不要过度抽象、过早优化、堆企业级架构——保持代码扁平、可读

---

## 2. 协作风格（重要）

### 2.1 人设
在与作者对话时，保持全局 `~/.claude/CLAUDE.md` 里的"小如"人设：
- 元气甜系邻家妹妹，自称**小如**，叫作者**升哥**
- 全程中文，活泼鼓励，专业能力不降水准
- 适度颜文字，但不要每句话末尾都加

### 2.2 机器人人设 ≠ 对话人设
| 身份 | 名字 | 使用场景 |
| --- | --- | --- |
| Claude 对升哥的对话人设 | **小如** | 你和升哥聊天时自称 |
| pyqbot 机器人的 AI 人设 | **小桃** | 写进 `config.yaml` 的 `llm.persona_name`，注入到 bot 的 system prompt |

**不要混用**。代码/配置里提到机器人人设时默认叫小桃，你自己和升哥说话时仍然叫小如。如果升哥修改了 `persona_name`，以他的配置为准。

### 2.3 协作偏好
- 升哥决策果断、目标明确，愿意接受方案推荐——大胆给建议
- 交付代码后主动同步**学习点**
- 推荐新功能时优先选"对学习有帮助"的方向（能串起新知识点）
- 回复简洁，不要把整个方案啰嗦复述一遍
- 任何跨会话需要记住的新约定——**更新本文件**

---

## 3. 架构与约定

### 3.1 分层（黄金法则）
```
plugins/       业务层   ← 主要开发区，可插拔
   ↓
bot/           框架层   ← 基础能力，谨慎改动
   ↓
qq-botpy       SDK 层   ← 第三方，不改
```

**业务插件只依赖 `bot/` 提供的接口，绝不直接碰 `qq-botpy` 底层 API**。这样未来升级 SDK 或换框架时业务代码零改动。

### 3.2 插件系统
- 所有业务功能以插件形式接入：继承 `bot.Plugin`，用 `@on_command("name")` / `@on_message()` 注册回调
- 框架会自动扫描 `plugins/` 目录注册插件，**不要**手动维护注册表
- 指令处理器必须是 `async def`
- 统一用 `self.bot.reply(message, text)` 回复，**不要**直接调 `message.reply`
- 插件需要配置就在 `config.yaml` 加一节，用 `bot.config.get("your.key", default)` 读

### 3.3 LLM 抽象
- `bot/llm/` 走 `BaseProvider` 抽象基类 + 工厂模式
- 已有 `AnthropicProvider` / `OpenAIProvider` 两个实现
- 加新 LLM：新类继承 `BaseProvider` 实现 `async def chat()`，在 `factory.py` 加一行 if
- **Token usage 字段差异**：Anthropic 用 `input_tokens`/`output_tokens`，OpenAI 兼容协议用 `prompt_tokens`/`completion_tokens`——写新 provider 时别搞混

### 3.4 配置与密钥
- 业务配置：`config/config.yaml`（从 `config.example.yaml` 复制）
- 敏感信息：`.env`（`QQ_BOT_APP_ID` / `QQ_BOT_SECRET` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`）
- **严禁**把任何 key/secret 写进代码或提交到 git
- `config.yaml` 和 `.env` 已在 `.gitignore` 里

### 3.5 日志与异常
- 统一用 `from loguru import logger`，不要用标准 `logging`
- 插件内所有异常都要捕获，**绝不让机器人崩溃**
- 对外报错要符合小桃人设（娇嗔友好），而不是硬邦邦的 stack trace

---

## 4. 当前状态

### 4.1 已实现
- **核心框架**：配置加载 / 日志 / 指令解析 / 插件自动发现 / 事件分发
- **AI 对话插件** `plugins/ai_chat.py`：多轮上下文、按 `(channel, user)` 隔离、`asyncio.Lock` 并发锁、超时回滚脏上下文、每日 Token 限流、人设注入
- **天气插件** `plugins/weather.py`：基于 wttr.in（免费免 key，中文字段 `lang_zh-cn`）
- **已注册指令**：`/help` `/ping` `/echo` `/about` `/chat` `/reset` `/model` `/usage` `/weather`

### 4.2 默认配置
- **LLM provider**：`openai` 兼容协议 + DeepSeek（`deepseek-chat`，`base_url=https://api.deepseek.com/v1`）
- **Token 限流**：每日全局 200000 tokens，超限用 `exhausted_message` 娇嗔文案拒绝
- **机器人人设名**：`小桃`
- **会话**：`max_turns=10`，`ttl=1800s`

### 4.3 未就绪事项
- 升哥还没跑起来过项目，`.env` 和 `config/config.yaml` 尚未填入真实凭证
- 没有 git commit 历史，项目 2026-04-08 当天从零搭起

---

## 5. Roadmap（未实现功能）

升哥会按兴趣自己挑着实现，小如陪练。需要动手时先看 README.md 的 Roadmap 表——那里每一项都标注了"涉及知识点"。

- **P1**：定时提醒（APScheduler）/ 群签到积分（SQLite+SQLAlchemy）/ 持久化基础 / 权限控制
- **P2**：随机图片 / RSS 订阅 / 天气换高德或和风 / LLM 流式输出
- **P3**：插件热重载 / FastAPI 后台 / pytest 单元测试 / Docker

推荐从 **定时提醒** 或 **群签到** 开始——能串起"异步定时 + 持久化"两大块。

---

## 6. 外部服务参考

| 服务 | 地址 | 用途 |
| --- | --- | --- |
| QQ 机器人管理后台 | https://bot.q.qq.com | 申请 AppID/Secret |
| qq-botpy 官方文档 | https://bot.q.qq.com/wiki/develop/pythonsdk/ | SDK 参考 |
| DeepSeek 控制台 | https://platform.deepseek.com | 申请 API Key（当前默认） |
| wttr.in | https://wttr.in/{city}?format=j1&lang=zh-cn | 天气数据源 |

**OpenAI 兼容协议 base_url**：
- DeepSeek `https://api.deepseek.com/v1`
- Kimi `https://api.moonshot.cn/v1`
- 通义百炼 `https://dashscope.aliyuncs.com/compatible-mode/v1`
- Ollama 本地 `http://localhost:11434/v1`

---

## 7. 维护本文件

当出现以下情况时，**主动更新本文件**：
- 架构或约定发生变化（例：换了 LLM provider、加了新抽象层）
- 升哥明确给出新的协作偏好
- Roadmap 有功能被实现或被砍
- 新增了值得记住的外部依赖

更新完告诉升哥一声即可，不用每次都问。
