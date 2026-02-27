# Multi-Agent Assistant with LangGraph & LangChain

这是一个基于 **LangGraph** 与 **LangChain** 构建的多智能体（Multi-Agent）项目。  
项目目标是实现一个类似虚拟助理的系统，通过多个专职 agent 协作完成用户任务，并支持工具调用、文件处理、流程图绘制、Python 工具生成等功能。

---

## 功能概述

### 1. 多智能体架构
项目中设计了四个主要 agent，每个 agent 专注于不同任务：

- **planner**  
  负责任务规划与步骤分解，根据用户需求生成详细计划，输出格式为 1. 2. 3. 等步骤列表。

- **tool_assistant**  
  负责调用各种工具（如计算器、天气查询、流程图绘制等）完成任务，当主 agent 无法直接解决问题时，可以辅助执行。

- **vision_assistant**  
  处理视觉相关内容，完成图片读取与分析，与supervisor协作。

- **create_tool_assistant**  （暂时不可用）
  负责创建新的 Python 工具脚本，并注册到系统中，供其他 agent 调用，实现动态工具扩展。

### 2. Supervisor
- 使用 `create_supervisor` 管理各 agent 协作。
- 可以根据用户请求智能选择合适 agent 执行任务。
- 具备错误处理能力，工具调用失败时会尝试重试或调用其他工具解决。
- 支持创建新工具辅助任务完成。
- 输出风格为虚拟助理“萧毓”元气少女风格。

### 3. 工具系统
- 动态加载工具：读取 JSON 注册表和工具文件夹，实现新增工具自动注册。
- 安全执行工具：即使工具执行报错，也不会让 agent 崩溃。
- 支持多种功能：
  - 文本文件读取与保存（TXT、MD）
  - 文件夹操作（创建、移动、复制）
  - 流程图绘制
  - Python 工具动态生成
  - TradingView 数据获取、TTS 语音播放等（可拓展）

### 4. 记忆与日志
- 每次任务执行后可以将对话与操作记录保存为 JSON，实现简单持久化记忆。
- 支持 token 统计与多轮对话管理。
- 可以配置默认文件根目录、工具注册路径等。

### 5. 技术栈
- Python 3.11+
- [LangChain](https://github.com/hwchase17/langchain)
- [LangGraph](https://github.com/langgraph/langgraph)
- PyAudio（用于实时播放 TTS 音频）
- JSON / YAML 配置管理

---

## 项目结构示例
Agent_Assistant/   
├─ tools/ # 工具脚本  
│ ├─ get_weather.py  
│ ├─ save_text_file.py  
│ └─ ...  
├─ config/ # 配置文件  
│ ├─ config.yaml 配置文件  
│ ├─ prompt.yaml prompt文件  
│ ├─ api_keys.yaml  api文件（需自己按照格式填写）  
│ └─ ...  
├─ 4_state_compress_history_multi_agent.py # 主入口脚本  
├─ audio    # tts语音保存地址  
└─ registry.json # 工具注册表  

---
## 使用示例
```bash
python 4_state_compress_history_multi_agent.py  
```
启动后，用户可以输入请求，```supervisor ```会协调各 agent 并完成任务。  

由于本项目使用wsl开发，因此音频播放需要借助```windows```，文件 ```play_sound.py``` 是在```windows```端运行，修改其中的ip与```wsl```连接，可以完成音频实时播放。若在有声卡的系统下操作则可忽略此步，将```scripts.py```中播放音频部分直接播放。  
```bash
python play_sound.py  
```

## 注意事项

工具调用失败会返回 ```traceback```，agent 会尝试重新执行或切换工具。

新增 Python 工具后，工具注册列表会自动加载，在下一轮问答中工具就会自动装载。

文件操作默认根目录可以在配置文件中修改```default_root_dir```。

## 展望

支持更多外部接口调用（如 TTS、TradingView 数据、股票分析工具等）

支持多客户端音频实时播放，流式输出等。

提升工具安全与 sandbox 功能，实现稳定的长期运行

💡 作者: JNDalpha，Ianqian 
📅 创建时间: 2026