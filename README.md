# SimpleAIHelper

简单而强大的AI接口助手，让与大语言模型的交互变得优雅简洁。

## 📚 简介

SimpleAIHelper 是一个轻量级Python包，设计用于简化与各种大语言模型API的交互过程。它提供了统一、优雅的接口，支持多种模型服务，包括OpenAI官方API、百炼(QwQ)、豆包模型、硅谷模型等兼容OpenAI接口的服务。

**重要说明**：SimpleAIHelper完全兼容OpenAI的Python包（`openai`），使用相同的底层API结构，但提供了更简洁、更强大的接口。您无需学习新的API结构，只需要掌握更简单的调用方式。

### 🌟 主要特点

- **简洁优雅的API**：使用最少的代码实现强大功能
- **多模型支持**：适配多种AI服务提供商
- **流式输出**：支持实时、流畅的响应显示
- **思考过程分离**：独特的思考过程和最终答案分离功能
- **会话管理**：灵活的对话历史保存和恢复
- **JSON输出**：支持结构化数据返回
- **完全兼容OpenAI**：基于官方openai包构建，支持所有OpenAI参数

## 🔧 安装

使用pip安装最新版本：

```bash
pip install simpleaihelper
```

**依赖说明**：SimpleAIHelper依赖于`openai`包，安装时会自动安装此依赖。

## 🚀 快速开始

### 基本使用

```python
from simpleaihelper import AI
import os

# 初始化客户端
api_key = os.environ.get("OPENAI_API_KEY")
client = AI(api_key=api_key)

# 简单问答
response = client.ask("Python中如何实现多线程编程？")
print(response)

# 流式输出
for chunk in client.stream_ask("解释一下量子计算的基本原理"):
    print(chunk, end="", flush=True)
```

### 思考过程分离

```python
# 获取带思考过程的回答
result = client.think("如何设计一个高性能的分布式系统？")
print(f"思考过程:\n{result['reasoning']}")
print(f"最终答案:\n{result['answer']}")

# 优雅的思考过程API
result = client.thinking_display("什么是CAP定理？")
print(f"思考: {result['reasoning'][:100]}...")
print(f"答案: {result['answer'][:100]}...")
```

### 使用会话

```python
# 创建会话
session = client.session(system_prompt="你是一位计算机科学教授")

# 进行多轮对话
response1 = session.ask("什么是设计模式？")
print(response1)

response2 = session.ask("请详细介绍一下单例模式")  # 保持上下文
print(response2)

# 流式思考
for chunk in session.stream_think("工厂模式和策略模式有什么区别？"):
    if chunk["type"] == "reasoning":
        print(f"[思考] {chunk['content']}", end="", flush=True)
    elif chunk["type"] == "answer":
        print(f"[回答] {chunk['content']}", end="", flush=True)
```

### 保存和恢复会话

```python
# 保存会话到SQLite数据库
db = client.load_db("conversations.db")
db.save_session(session)

# 查看保存的会话
sessions = db.view_sessions()
for s in sessions:
    print(f"会话ID: {s['session_id']}, 消息数: {s['message_count']}")

# 加载已有会话
loaded_session = db.load_session(sessions[0]['session_id'])

# 使用JSON格式保存
js = client.load_json("conversations.json")
js.save_session(session)
```

## 📘 核心功能详解

### 1. 客户端初始化

```python
client = AI(
    api_key="your_api_key",
    base_url="https://api.example.com/v1",  # 可选，支持自定义API端点
    default_model="gpt-3.5-turbo",  # 可选，默认使用的模型
    # 其他可选参数
)
```

**初始化参数完全兼容OpenAI**：

| 参数 | 描述 | 默认值 |
|-----|------|-------|
| `api_key` | API密钥，用于认证 | 必填 |
| `base_url` | API基础URL，用于非OpenAI服务 | `"https://api.openai.com/v1"` |
| `default_model` | 默认使用的模型名称 | `"gpt-3.5-turbo"` |
| `timeout` | 请求超时时间(秒) | OpenAI默认 |
| `max_retries` | 最大重试次数 | OpenAI默认 |
| `organization` | 组织ID(OpenAI多组织用户) | 无 |
| `api_version` | API版本 | 无 |
| `http_client` | 自定义HTTP客户端 | 无 |

支持的服务示例：

```python
# OpenAI官方
client = AI(api_key=os.environ.get("OPENAI_API_KEY"))

# 百炼(QwQ)
client = AI(
    api_key=os.environ.get("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    default_model="qwq-32b"
)

# 豆包
client = AI(
    api_key=os.environ.get("DOUBAO_API_KEY"),
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    default_model="doubao-lite-128k-240828"
)

# 硅谷
client = AI(
    api_key=os.environ.get("SILICON_API_KEY"), 
    base_url="https://api.siliconflow.cn/v1",
    default_model="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
)
```

### 2. 基本API

所有API都支持传递额外参数到底层模型：

```python
# 基本问答
response = client.ask(
    prompt="写一首关于AI的诗",
    messages=None,  # 可选，历史消息
    model="gpt-4",  # 覆盖默认模型
    temperature=0.7,  # 控制创造性
    # 支持其他OpenAI兼容参数
)

# 流式响应
for chunk in client.stream_ask(
    prompt="介绍一下Python的异步编程",
    temperature=0.5
):
    print(chunk, end="", flush=True)

# 结构化JSON响应
json_response = client.ask_json(
    prompt="列出5种编程语言及其特点",
    model="gpt-3.5-turbo-1106"
)
```

## ⚙️ 支持的OpenAI参数

SimpleAIHelper的所有方法（`ask`, `stream_ask`, `think`, `stream_think`, `ask_json`等）都支持以下OpenAI兼容参数：

| 参数 | 描述 | 默认值 |
|-----|------|-------|
| `model` | 使用的模型名称 | 客户端初始化时设定的默认模型 |
| `temperature` | 温度/随机性 (0-2) | `1.0` |
| `top_p` | 核采样阈值 (0-1) | `1.0` |
| `n` | 生成的回答数量 | `1` |
| `max_tokens` | 最大标记数 | 无限制 |
| `presence_penalty` | 存在惩罚 (-2.0-2.0) | `0.0` |
| `frequency_penalty` | 频率惩罚 (-2.0-2.0) | `0.0` |
| `logit_bias` | 标记的对数几率偏差 | `{}` |
| `stop` | 生成停止序列 | 无 |
| `user` | 用户标识符 | 无 |
| `response_format` | 响应格式 (如`{"type": "json_object"}`) | 无 |
| `seed` | 随机数种子 | 无 |
| `tools` | 可用的工具列表 | 无 |
| `tool_choice` | 工具选择规则 | 无 |

**使用示例**：

```python
# 设置多种参数，针对创意写作
response = client.ask(
    prompt="创作一个科幻小说开头",
    model="gpt-4",
    temperature=0.8,  # 较高的创造性
    max_tokens=500,   # 限制回答长度
    presence_penalty=0.5,  # 鼓励话题多样性
    stop=["\n\n", "第二章"]  # 在这些文本出现时停止生成
)

# 在流式会话中使用参数
for chunk in session.stream_ask(
    prompt="解释量子纠缠",
    temperature=0.2,  # 低温度，更确定性的回答
    top_p=0.8,        # 更聚焦的分布
    frequency_penalty=0.5  # 减少重复
):
    print(chunk, end="", flush=True)

# JSON输出配置
structured_result = client.ask_json(
    prompt="列出5个世界上最高的建筑及其高度",
    response_format={"type": "json_object"},  # 强制JSON格式
    temperature=0.1  # 保持结果一致性
)
```

### 🔄 会话参数传递

在会话中，可以在创建会话时设置默认参数，也可以在每次调用时覆盖这些参数：

```python
# 创建会话时设置默认参数
session = client.session(
    system_prompt="你是一位科学教授",
    model="gpt-4-turbo",
    temperature=0.3,
    max_tokens=1000
)

# 第一个问题使用会话默认参数
response1 = session.ask("什么是黑洞？")

# 第二个问题覆盖某些参数
response2 = session.ask(
    "黑洞会蒸发吗？",
    temperature=0.7,  # 覆盖会话默认值0.3
    max_tokens=300    # 覆盖会话默认值1000
)
```

### 3. 思考过程功能

SimpleAIHelper提供独特的思考过程分离功能，支持两种模式：

1. **原生思考过程**：针对支持reasoning_content的模型(如QwQ)
2. **模拟思考过程**：为普通模型添加系统提示，引导模型显示思考过程

```python
# 获取完整思考结果
result = client.think("如何优化数据库查询性能？")
print(f"思考过程: {result['reasoning']}")
print(f"最终答案: {result['answer']}")

# 流式思考过程
for chunk in client.stream_think("如何实现一个分布式锁？"):
    chunk_type = chunk["type"]  # "reasoning", "transition", "answer"
    content = chunk["content"]
    
    if chunk_type == "reasoning":
        print(f"[思考中] {content}", end="", flush=True)
    elif chunk_type == "answer":
        print(f"[最终答案] {content}", end="", flush=True)
```

### 4. 会话管理

```python
# 创建会话
session = client.session(
    system_prompt="你是一位经验丰富的软件架构师",
    model="gpt-4",  # 可选，会话默认模型
    # 其他可选参数
)

# 会话方法
response = session.ask("什么是微服务架构？")
stream_response = session.stream_ask("微服务架构的优缺点是什么？")
think_result = session.think("如何设计微服务之间的通信？")
json_result = session.ask_json("列出5种常见的微服务设计模式")

# 获取会话历史
history = session.get_history()
```

### 5. 会话持久化

#### SQLite存储

```python
# 初始化数据库管理器
db = client.load_db(
    db_path="conversations.db",  # 数据库文件路径
    table="ai_messages"  # 可选，表名
)

# 保存会话
db.save_session(session)

# 查看所有会话
sessions = db.view_sessions()

# 查看特定会话的消息
messages = db.view_session_messages(session_id)

# 加载会话
loaded_session = db.load_session(
    session_id,
    update=False  # 是否创建新会话ID
)
```

#### JSON存储

```python
# 初始化JSON管理器
js = client.load_json("conversations.json")

# 与SQLite接口相同
js.save_session(session)
sessions = js.view_sessions()
loaded_session = js.load_session(session_id)
```

## 🧩 高级用法

### 1. 自定义消息历史

```python
# 准备自定义消息历史
messages = [
    {"role": "system", "content": "你是一位数学教授"},
    {"role": "user", "content": "什么是黎曼猜想？"},
    {"role": "assistant", "content": "黎曼猜想是..."}
]

# 在现有历史基础上继续对话
response = client.ask("这与素数分布有什么关系？", messages=messages)
```

### 2. 流式思考处理

```python
# 更精细的流式思考处理
reasoning_parts = []
answer_parts = []

for chunk in client.stream_think("如何实现一个无锁队列？"):
    chunk_type = chunk["type"]
    content = chunk["content"]
    
    if chunk_type == "reasoning":
        reasoning_parts.append(content)
        print(content, end="", flush=True)
    elif chunk_type == "transition":
        print("\n--- 思考结束，开始回答 ---\n")
    elif chunk_type == "answer":
        answer_parts.append(content)
        print(content, end="", flush=True)

# 获取完整内容
full_reasoning = "".join(reasoning_parts)
full_answer = "".join(answer_parts)
```

## 📝 API参考

### AI 类

基本客户端实例，提供与AI模型交互的主要接口。

| 方法                | 描述                             | 返回类型              |
|--------------------|----------------------------------|---------------------|
| `__init__`         | 初始化客户端                      | -                   |
| `ask`              | 发送请求并获取普通响应             | str                 |
| `stream_ask`       | 流式获取响应                      | Generator[str]      |
| `think`            | 获取带思考过程的响应               | Dict[str, str]      |
| `stream_think`     | 流式获取思考过程和回答             | Generator[Dict]     |
| `thinking_display` | 优雅获取思考过程和回答             | Dict[str, str]      |
| `ask_json`         | 获取JSON格式响应                  | Dict/List           |
| `session`          | 创建会话实例                      | Session             |
| `load_db`          | 初始化SQLite会话管理              | SQLiteManager       |
| `load_json`        | 初始化JSON会话管理                | JSONManager         |

### Session 类

管理多轮对话的会话实例。

| 方法                | 描述                             | 返回类型              |
|--------------------|----------------------------------|---------------------|
| `ask`              | 在会话中发送请求                   | str                 |
| `stream_ask`       | 会话中流式获取响应                 | Generator[str]      |
| `think`            | 会话中获取带思考过程的响应          | Dict[str, str]      |
| `stream_think`     | 会话中流式获取思考过程和回答        | Generator[Dict]     |
| `thinking_display` | 会话中优雅获取思考过程和回答        | Dict[str, str]      |
| `ask_json`         | 会话中获取JSON格式响应             | Dict/List           |
| `get_history`      | 获取会话历史                      | List[Dict]          |
| `add_message`      | 添加消息到历史                    | -                   |

## ⚙️ 配置选项

所有方法都支持以下通用参数：

- `model` - 指定要使用的模型
- `temperature` - 控制结果的随机性 (0-2)
- `top_p` - 控制结果的多样性
- `max_tokens` - 限制响应的最大长度
- 支持所有OpenAI API兼容的参数

## ❓ 常见问题

**Q: 如何设置API密钥？**

A: 建议使用环境变量存储API密钥：

```python
import os
os.environ["OPENAI_API_KEY"] = "your-api-key"
```

**Q: 支持哪些模型？**

A: 支持所有OpenAI兼容接口的API服务和模型，包括但不限于：
- OpenAI的GPT系列模型
- 百炼的QwQ系列模型
- 豆包模型
- 硅谷模型
- Claude模型(通过兼容接口)

**Q: 如何处理请求错误？**

A: 使用标准的Python异常处理：

```python
try:
    response = client.ask("你的问题")
except Exception as e:
    print(f"发生错误: {e}")
```

## 🤝 贡献

欢迎贡献代码、报告问题或提出改进建议！请查看[贡献指南](CONTRIBUTING.md)了解更多信息。

## 📄 许可证

本项目采用MIT许可证 - 详见[LICENSE](LICENSE)文件。

## 📞 联系方式

如有任何问题或建议，请通过[GitHub问题](https://github.com/yourusername/simpleaihelper/issues)与我们联系。 