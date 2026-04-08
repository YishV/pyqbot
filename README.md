# pyqbot

> 📚 **这是一个 Python 学习项目**：通过从零搭建一个 QQ 机器人，循序渐进地学习 Python 工程化相关的知识点——包括异步编程（asyncio）、面向对象、装饰器、插件化架构、配置管理、HTTP 客户端、类型注解、日志、第三方 API 对接等。

基于官方 [qq-botpy](https://bot.q.qq.com/wiki/develop/pythonsdk/) SDK 的 QQ 机器人项目，采用插件化架构。

---

## 目录
- [一、项目目标](#一项目目标)
- [二、功能清单](#二功能清单)
- [三、非功能需求](#三非功能需求)
- [四、技术选型](#四技术选型)
- [五、项目结构详解](#五项目结构详解)
- [六、核心模块说明](#六核心模块说明)
- [七、快速开始](#七快速开始)
- [八、如何开发一个新插件](#八如何开发一个新插件)
- [九、学习笔记 / 知识点索引](#九学习笔记--知识点索引)

---

## 一、项目目标
打造一个**可扩展、易维护**的 QQ 频道/群机器人，同时作为 Python 学习的实战项目：
- 所有业务功能以**插件**形式接入，核心框架与业务代码完全解耦
- 每一层代码都尽量简洁、可读，方便学习阅读
- 覆盖常见 Python 工程实践：依赖管理、配置分离、日志、类型注解、异步 I/O

---

## 二、功能清单

### ✅ 2.1 已实现

| 模块 | 功能 | 所在文件 |
| --- | --- | --- |
| 消息接收 | 频道 @消息、群 @消息、私信 | `bot/core.py` |
| 指令解析 | 统一前缀（默认 `/`），支持带引号参数 | `bot/command.py` |
| 插件系统 | 自动发现 + 装饰器注册 + 生命周期钩子 | `bot/plugin.py` |
| 配置管理 | YAML 主配置 + `.env` 管理敏感信息 | `bot/config.py` |
| 日志系统 | loguru 双输出、按天切分、自动归档 | `bot/logger.py` |
| AI 对话 | 多轮上下文、会话隔离、并发锁、超时回滚 | `plugins/ai_chat.py` |
| LLM 抽象 | provider 可切换（Anthropic / OpenAI 兼容） | `bot/llm/` |
| Token 限流 | 每日全局配额，跨天自动归零 | `bot/llm/rate_limiter.py` |
| 元气人设 | 系统提示词注入 `persona_name` | `plugins/ai_chat.py` |
| 天气查询 | 基于 wttr.in，零配置免 key | `plugins/weather.py` |

**已实现指令**：
- `/help` —— 查看指令列表
- `/ping` —— 测试机器人是否在线
- `/echo <内容>` —— 复读
- `/about` —— 查看机器人信息
- `/chat <内容>` —— 与 AI 对话
- `/reset` —— 清空当前会话历史
- `/model` —— 查看当前使用的 LLM 模型
- `/usage` —— 查看今日 Token 使用情况
- `/weather <城市>` —— 查询天气

### 🚧 2.2 待实现（Roadmap）

按优先级排序，从上到下建议依次学习实现：

| 优先级 | 功能 | 说明 | 涉及知识点 |
| --- | --- | --- | --- |
| P1 | 🔔 **定时提醒 / 倒计时** | `/remind 30m 喝水`、`/countdown 2026-06-01 高考` | `APScheduler`、持久化、时区处理 |
| P1 | 📝 **群签到 & 积分系统** | 每日签到领积分、排行榜、积分商城 | SQLite、ORM（SQLAlchemy）、数据模型设计 |
| P1 | 💾 **数据持久化基础设施** | 统一的 DB 封装，供其他插件复用 | SQLite/SQLAlchemy async、迁移脚本 |
| P1 | 🛡 **权限控制** | 指令白/黑名单、管理员专属指令（如 `/reload` 热重载插件） | 装饰器进阶、配置热加载 |
| P2 | 🎲 **随机图片 / 表情包** | `/pic 猫猫`、接入二次元图库 API | 图片上传、Base64 编码、文件流 |
| P2 | 📰 **RSS 订阅推送** | `/rss add <url>`，定时拉取 + 推送新条目 | `feedparser`、定时任务、去重（set/DB） |
| P2 | 🌤 **天气插件扩展** | 加入高德 / 和风天气作为生产级 provider | Provider 抽象模式复用 |
| P2 | 📊 **LLM 流式输出** | 边生成边发送，打字机效果 | SSE、异步生成器 `async for` |
| P3 | 🧩 **插件热重载** | `/reload ai_chat` 无需重启即可更新插件 | `importlib.reload`、状态迁移 |
| P3 | 🌍 **Web 管理后台** | FastAPI + Vue 的简易后台，查看日志/配置/用量 | FastAPI、WebSocket、前后端分离 |
| P3 | 🧪 **单元测试** | 用 `pytest` + `pytest-asyncio` 覆盖核心模块 | 测试驱动开发、Mock |
| P3 | 🐳 **Docker 部署** | 一键容器化运行 | Dockerfile、compose、多阶段构建 |

### 2.3 事件订阅
- `GUILD_MESSAGES` 频道消息
- `DIRECT_MESSAGE` 私信
- `GROUP_AT_MESSAGE_CREATE` 群 @消息
- `GUILD_MEMBERS` 成员变动（欢迎 / 告别，待接入）

---

## 三、非功能需求
- **可扩展性**：新功能以插件形式提供，不修改核心代码
- **可观测性**：完整日志 + 异常捕获，避免进程崩溃
- **安全性**：AppID/Secret/API Key 严禁写入代码库，一律走 `.env`
- **跨平台**：Windows / Linux 均可运行
- **可学习性**：代码结构扁平、命名清晰、必要处有注释

---

## 四、技术选型

| 依赖 | 版本 | 用途 | 为什么选它 |
| --- | --- | --- | --- |
| Python | 3.10+ | 语言 | 支持 `match`、新版类型注解（`list[str]`） |
| `qq-botpy` | ≥1.2.1 | QQ 机器人官方 SDK | 官方维护，事件语义完整 |
| `PyYAML` | ≥6.0 | 解析 YAML 配置 | 配置文件人类友好 |
| `loguru` | ≥0.7 | 日志 | 零配置，比标准 `logging` 简单 |
| `python-dotenv` | ≥1.0 | 加载 `.env` | 敏感信息与代码分离 |
| `httpx` | ≥0.27 | 异步 HTTP 客户端 | 原生 `async/await`，比 `requests` 更适合异步项目 |
| `APScheduler` | 待引入 | 定时任务 | 未来实现 P1 功能时接入 |
| `SQLAlchemy` | 待引入 | ORM | 未来实现持久化时接入 |

---

## 五、项目结构详解

```
pyqbot/
│
├── bot/                          # 🧠 核心框架（不含业务逻辑）
│   ├── __init__.py               # 对外暴露 PyQBot / Plugin / 装饰器
│   ├── core.py                   # Bot 主类：封装 botpy.Client，负责事件分发
│   ├── config.py                 # 配置加载：YAML + .env 合并
│   ├── logger.py                 # loguru 日志初始化
│   ├── command.py                # 指令解析：shlex 分词 + 前缀剥离
│   ├── plugin.py                 # 插件基类 + 装饰器 + 自动加载器
│   └── llm/                      # 🤖 LLM 抽象层
│       ├── __init__.py
│       ├── base.py               # BaseProvider 抽象基类 + ChatMessage / ChatResult
│       ├── anthropic_provider.py # Claude API 实现
│       ├── openai_provider.py    # OpenAI 兼容协议（DeepSeek/Kimi/通义/Ollama 通用）
│       ├── factory.py            # 根据配置构建对应 provider
│       ├── session.py            # 多轮会话存储 + 过期淘汰 + 并发锁
│       └── rate_limiter.py       # 每日 Token 限流器
│
├── plugins/                      # 🔌 业务插件目录（全部可插拔）
│   ├── __init__.py
│   ├── builtin_help.py           # /help /about
│   ├── builtin_ping.py           # /ping
│   ├── builtin_echo.py           # /echo
│   ├── ai_chat.py                # AI 对话（带限流 + 人设）
│   └── weather.py                # 天气查询
│
├── config/                       # ⚙️ 配置目录
│   ├── config.example.yaml       # 配置模板（提交到 git）
│   └── config.yaml               # 实际配置（git 忽略）
│
├── logs/                         # 📋 日志输出（git 忽略，自动创建）
│
├── main.py                       # 🚪 程序入口：加载配置 → 初始化日志 → 启动 Bot
├── requirements.txt              # 📦 Python 依赖清单
├── .env.example                  # 🔐 环境变量模板
├── .env                          # 🔐 实际环境变量（git 忽略）
├── .gitignore
└── README.md                     # 📖 本文档
```

### 分层原则

```
┌─────────────────────────────────────────┐
│        plugins/        业务层            │  ← 你主要写代码的地方
│   (ai_chat / weather / ...)             │
├─────────────────────────────────────────┤
│         bot/           框架层            │  ← 提供基础能力，少改动
│   (core / plugin / config / llm)        │
├─────────────────────────────────────────┤
│       qq-botpy         SDK 层            │  ← 第三方，不改动
└─────────────────────────────────────────┘
```

**黄金法则**：业务插件只依赖 `bot/` 提供的接口，绝不直接碰 `qq-botpy` 的底层 API。这样未来换 SDK 或框架升级时，业务代码可以零改动。

---

## 六、核心模块说明

### 6.1 `main.py` —— 程序入口
三步走：**加载配置 → 初始化日志 → 启动 Bot**。捕获 `KeyboardInterrupt` 实现优雅退出。

### 6.2 `bot/config.py` —— 配置加载
- 用 `python-dotenv` 读取 `.env` 中的 `QQ_BOT_APP_ID` / `QQ_BOT_SECRET` / `OPENAI_API_KEY`
- 用 `PyYAML` 读取 `config/config.yaml`
- 提供 `BotConfig.get("bot.command_prefix", default)` 支持**点号路径**取值
- **学习点**：`dataclass`、`pathlib.Path`、YAML 嵌套结构访问

### 6.3 `bot/logger.py` —— 日志
- 基于 `loguru`，一行配置同时输出到控制台和文件
- 按天切分（`rotation="00:00"`），保留 14 天（`retention`）
- **学习点**：`loguru` 的 sink 机制、日志级别、格式化

### 6.4 `bot/command.py` —— 指令解析
- 剥离 `<@bot>` mention 前缀
- 用 `shlex.split` 分词，支持 `/echo "hello world"` 这种带空格参数
- 返回 `ParsedCommand` dataclass
- **学习点**：`shlex` 标准库、dataclass、`None` 作为"解析失败"返回

### 6.5 `bot/plugin.py` —— 插件系统（重点）
这是整个框架最核心的部分，值得细读。

- **装饰器** `@on_command("name")` / `@on_message()`：给方法打标记，把元信息存到函数对象上
- **自动发现** `PluginManager.discover()`：用 `pkgutil.iter_modules` 扫描 `plugins/` 目录，`importlib.import_module` 动态导入
- **自动注册** `_register()`：用 `inspect.getmembers` 反射出所有协程方法，读取装饰器标记，存进 `self.commands` 字典
- **学习点**：装饰器原理、反射（`inspect`）、动态导入（`importlib`）、函数是一等公民（`func.xxx = ...`）

### 6.6 `bot/core.py` —— Bot 主类
- `_InnerClient` 继承 `botpy.Client`，重写事件方法，转发给 `PyQBot.dispatch_message`
- `dispatch_message` 先执行所有 `@on_message` 钩子，再尝试解析指令调用 `@on_command`
- 异常全部捕获 + 记录日志，绝不让机器人崩掉
- **学习点**：继承、方法重写、事件驱动、`async/await` 异步编程

### 6.7 `bot/llm/` —— LLM 抽象层（优雅的小案例）
这部分展示了 **"面向接口编程"** 的威力：

```
         BaseProvider (抽象基类)
              ▲
      ┌───────┴───────┐
      │               │
AnthropicProvider   OpenAIProvider
      │               │
    Claude      DeepSeek/Kimi/通义/Ollama
```

想支持新的 LLM？只要写一个新类继承 `BaseProvider`，实现 `async def chat(...) -> ChatResult`，在 `factory.py` 里加一行 if 分支即可。**业务代码完全不用改**。

- **学习点**：抽象基类（`ABC`）、工厂模式、异步 HTTP（`httpx.AsyncClient`）、dataclass

### 6.8 `bot/llm/session.py` —— 会话管理
- 按 `(channel_id, user_id)` 存 session，每个 session 一个 `asyncio.Lock`
- 超过 `max_turns` 自动截断最老记录
- 超过 `ttl` 自动过期
- **学习点**：`asyncio.Lock` 并发控制、字典作为简易缓存、时间戳过期

### 6.9 `bot/llm/rate_limiter.py` —— Token 限流
- 用"日期对比 + 懒归零"实现，不需要后台定时任务
- 跨天自动 reset
- **学习点**：`datetime.date`、属性（`@property`）、简单状态机

---

## 七、快速开始

```bash
# 1. 克隆 & 进入目录
cd pyqbot

# 2. 创建虚拟环境（强烈建议）
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 复制配置
cp config/config.example.yaml config/config.yaml
cp .env.example .env

# 5. 编辑 .env 填入
#    QQ_BOT_APP_ID / QQ_BOT_SECRET  → https://bot.q.qq.com 申请
#    OPENAI_API_KEY                 → DeepSeek: https://platform.deepseek.com

# 6. 启动
python main.py
```

启动后去 QQ 频道 @机器人 说句话，或者发 `/ping` 试试～

---

## 八、如何开发一个新插件

以"随机色图"插件为例，三步搞定：

### 1. 新建文件 `plugins/pic.py`

```python
from bot import Plugin, on_command


class PicPlugin(Plugin):
    name = "pic"
    description = "随机图片"

    @on_command("pic", help_text="随机来一张图")
    async def handle_pic(self, message, args: list[str]) -> None:
        # TODO: 调用图片 API，拿到图片 URL 或字节流
        await self.bot.reply(message, "图片功能还没做完哦～")
```

### 2. 就没有第 2 步了

框架会自动扫描 `plugins/` 目录，发现你的 `PicPlugin` 类，自动注册 `/pic` 指令。

### 3. 重启机器人测试

```bash
python main.py
```

在 QQ 里发 `/pic`，搞定！

### 📌 插件开发备忘

- 继承 `Plugin`，类名随意，`name` 字段用来在日志里区分
- 指令方法必须是 `async def`
- 用 `self.bot.reply(message, text)` 回复，**别直接调 `message.reply`**
- 需要配置？在 `config.yaml` 加一节，在 `__init__` 里用 `bot.config.get("your.key")` 读
- 需要持久化？等 P1 的 DB 基础设施实现后会有统一方案
- 想监听所有消息？用 `@on_message()` 而不是 `@on_command(...)`

---

## 九、学习笔记 / 知识点索引

这个项目里涉及的 Python 知识点，按难度排序：

### 🟢 入门
- [x] 变量 / 函数 / 类 / 模块
- [x] `list` / `dict` / `tuple` / `set`
- [x] `if` / `for` / `while`
- [x] 文件读写、路径处理（`pathlib`）
- [x] 字符串格式化（f-string）

### 🟡 进阶
- [x] **面向对象**：继承、抽象基类（`abc.ABC`）、`@property`
- [x] **装饰器**：函数装饰器的原理（见 `bot/plugin.py`）
- [x] **类型注解**：`list[str]`、`dict[str, Any]`、`Callable`、`| None`
- [x] **Dataclass**：`@dataclass`、`field(default_factory=...)`
- [x] **异常处理**：自定义异常类、`try/except/finally`、`raise ... from exc`
- [x] **模块与包**：`__init__.py`、相对导入、`importlib`

### 🔴 高级
- [x] **异步编程**：`async/await`、`asyncio.Lock`、`asyncio.wait_for`
- [x] **反射**：`inspect.getmembers`、`inspect.iscoroutinefunction`
- [x] **动态导入**：`importlib.import_module`、`pkgutil.iter_modules`
- [x] **面向接口**：抽象基类 + 工厂模式（见 `bot/llm/`）
- [x] **上下文管理器**：`async with`（`httpx.AsyncClient`）
- [ ] **并发控制**：`asyncio.Semaphore`、`asyncio.gather`（待 RSS 插件实现时引入）
- [ ] **单元测试**：`pytest`、`pytest-asyncio`、Mock（待实现）
- [ ] **性能分析**：`cProfile`、`line_profiler`（按需）

### 📚 推荐学习路径
1. 先把 `main.py` → `bot/config.py` → `bot/logger.py` 看懂，理解启动流程
2. 再看 `bot/command.py` → `bot/plugin.py`，理解插件系统（本项目精华）
3. 然后看 `bot/core.py`，理解事件分发
4. 最后看 `bot/llm/` 整个目录，学习面向接口编程
5. 自己动手实现 [Roadmap](#🚧-22-待实现roadmap) 里的任意一个功能

---

## License

学习项目，随意使用。
