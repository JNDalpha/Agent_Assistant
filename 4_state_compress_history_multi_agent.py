from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool
from langgraph_supervisor import create_supervisor
from langchain.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from pprint import pprint
import os
import json
import importlib.util
from langchain_core.tools import BaseTool, StructuredTool
import traceback
import yaml
from datetime import datetime
from typing import TypedDict

# scripts脚本函数
from scripts import calculate_tokens_number_multi, get_final_answer, add_token, save_memory, load_memory, sync_tool_registry, clean_text, tts_output

# 工具函数
from tools.get_weather import get_weather
from tools.save_text_file import save_text_file
from tools.draw_flowchat import draw_flowchart
from tools.calculator import calculator
from tools.list_files import file_manager
from tools.read_txt_md import read_text_file
from tools.create_tools import create_python_tool
from tools.mkdir import create_folder
from tools.file_move_copy import file_move_copy_batch
from tools.tradingview import get_tradingview_analysis
from tools.vision_analyze import vision_analyze
from tools.create_xml import xml_dataset_writer_tool
from tools.scientific_plot_tool import scientific_plot_tool

# 读取配置
with open("config/config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

with open("config/api_keys.yaml", "r", encoding="utf-8") as f:
    api_config = yaml.safe_load(f)

# agent 配置
agent_config = config['agent_config']
MAX_AGENT_TURNS = agent_config["max_agent_turns"]
default_root_dir = agent_config["default_root_dir"]

# 模型配置
llm_config = config['llm_config']
base_url = llm_config["base_url"]
model_name = llm_config["model_name"]

api_key = api_config["llm_config"]["api_key"]
# 自定义工具配置
dynamic_tools_config = config['dynamic_tools_config']
REGISTRY_PATH = dynamic_tools_config["registry_path"]
TOOLS_DIR = dynamic_tools_config["tools_dir"]
os.makedirs(TOOLS_DIR, exist_ok=True)

# message 配置
message_config = config['message_config']
OUTPUT_MESSAGE_MAX_LENGTH = message_config["output_message_max_length"]
MESSAGE_SAVE_PATH = message_config["message_save_path"]

# tts 配置
tts_config = config['tts_config']
TTS_MODEL = tts_config["model"]
TTS_SAVE_ROOT_PATH = tts_config["save_root_path"]
TTS_HOST = tts_config["host"]
TTS_PORT = tts_config["port"]

with open("config/prompt.yaml", "r", encoding="utf-8") as f:
    prompt_config = yaml.safe_load(f)

# prompt 配置
supervisor_prompt = prompt_config['supervisor_prompt']['supervisor_prompt_v4'].format(default_root_dir=default_root_dir, current_time=datetime.now().strftime("%Y-%m-%d %H:%M"))
tool_assistant_prompt = prompt_config['tool_assistant_prompt']['tool_assistant_prompt_v1'].format(default_root_dir=default_root_dir)
create_tool_assistant_prompt = prompt_config['create_tool_assistant_prompt']['create_tool_assistant_prompt_v1']
output_prompt = prompt_config['output_prompt']['output_prompt_v1']


# 初始化检查点保存器
checkpointer = InMemorySaver()

class AgentState(TypedDict):
    # 最近对话（只保留 N 条，用于生成 prompt）
    recent_messages: list[dict]  # 每条 dict: {"role": "user/agent", "content": "...", "tokens": int}
    # 历史总结（压缩后的长期记忆，用于 supervisor 做全局决策）
    summary: list[str]
    # 各 agent 的独立长期记忆，不进 prompt
    agent_memory: dict  # key=agent_name, value=list[历史信息]
    # 工具调用缓存
    tool_cache: dict  # key=tool_name, value=最近调用结果
    # 可选：存储 checkpoint 版本号、时间戳等元信息
    meta: dict









# 安全包装工具
def make_safe_tool(obj, max_retries=3):
    def safe_run(func, kwargs=None):
        kwargs = kwargs or {}
        for attempt in range(max_retries):
            try:
                if isinstance(func, (BaseTool, StructuredTool)):
                    return func._run(**kwargs)
                else:
                    return func(**kwargs)
            except Exception as e:
                print(f"工具执行出错，尝试 {attempt+1}/{max_retries}: {type(e).__name__} {e}")
                # traceback.print_exc()
        return f"工具执行失败，已尝试 {max_retries} 次"

    # 已经是 BaseTool/StructuredTool
    if isinstance(obj, (BaseTool, StructuredTool)):
        class SafeToolWrapper(BaseTool):
            name = getattr(obj, "name", obj.__class__.__name__)
            description = getattr(obj, "description", "安全包装工具")
            def _run(self, **kwargs):
                return safe_run(obj, kwargs)
        return SafeToolWrapper() # type:ignore

    # 普通函数
    elif callable(obj):
        func_name = getattr(obj, "__name__", "anonymous_tool")
        @tool(func_name)
        def safe_func(**kwargs):
            return safe_run(obj, kwargs)
        return safe_func

    else:
        print(f"⚠️ {obj} 既不是函数也不是 BaseTool/StructuredTool")
        return None

# 动态加载生成的工具
def load_generated_tools(registry_path="tools_registry.json"):
    tools = []

    if not os.path.exists(registry_path):
        return tools

    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    for tool_name, meta in registry.items():
        file_path = meta.get("file")
        if not os.path.exists(file_path):
            print(f"⚠️ 工具文件不存在: {file_path}")
            continue

        spec = importlib.util.spec_from_file_location(tool_name, file_path)
        module = importlib.util.module_from_spec(spec)  #type: ignore
        spec.loader.exec_module(module)

        obj = getattr(module, tool_name, None)
        if obj is None:
            print(f"⚠️ 未找到函数/工具: {tool_name}")
            continue

        safe_tool = make_safe_tool(obj)
        if safe_tool:
            tools.append(safe_tool)
            print(f"✅ 已加载安全工具: {tool_name}")

    return tools

llm = ChatOpenAI(
    api_key=api_key, # type: ignore
    base_url=base_url,
    model=model_name, 
    temperature=0.5,
)

xy_llm = ChatOpenAI(
    api_key=api_key, # type: ignore
    base_url=base_url,
    model=model_name, 
    temperature=0.98,
)

# 输出语气调整 Agent，专门负责将智能体的原始回答润色成更符合人类表达习惯的内容。
output_agent = create_agent(
    model=xy_llm,
    tools=[],
    system_prompt =output_prompt,
    name="output_agent",
)

history_compress_agent = create_agent(
    model=llm,
    tools=[],
    system_prompt ="你是一个历史压缩专家，负责将智能体的对话历史进行总结和压缩，提取出关键信息和重要事件，生成一个简洁的历史总结，帮助 supervisor 更好地理解智能体的长期记忆和历史。"
)

# 计划制定 Agent，负责根据用户的需求制定详细的行动计划，输出格式为 1. 2. 3. 的形式，便于后续工具执行 Agent 理解和执行。
planner = create_agent(
    model=llm,
    tools=[],
    system_prompt ="你是一个擅长做计划的小助手，你需要按照输入要求定制计划，按照1. 2. 3. 的格式输出计划内容。",
    name="planner",
)

# 调用基础工具agent
base_tools = [get_weather, draw_flowchart, calculator, file_manager, read_text_file, save_text_file, create_folder, xml_dataset_writer_tool, scientific_plot_tool]
tool_assistant = create_agent(
    model=llm,
    tools = base_tools + load_generated_tools(),
    system_prompt =tool_assistant_prompt,
    name="tool_assistant"
)

vision_assistant = create_agent(
    model=llm,
    tools=[vision_analyze],
    system_prompt ="你是一个视觉分析专家，擅长分析图片内容并回答相关问题。你需要调用工具来分析用户输入的图片，并根据用户的问题给出详细的解释和回答。在传输图片路径时应为完整路径，包含根目录和文件名称，确保工具能够正确读取到图片文件。",
    name="vision_assistant"
)

create_tool_assistant = create_agent(
    model=llm,
    tools=[create_python_tool],
    system_prompt =create_tool_assistant_prompt,
    name="create_tool_assistant"
)

# 有bug
# financial_assistant = create_agent(
#     model=llm,
#     tools=[get_tradingview_analysis],
#     system_prompt ="你是一个金融领域的专家，擅长分析股票、基金等投资品种的基本面和技术面信息，并给出投资建议。你需要调用工具进行市场调研，得到真实数据后进行分析，最后输出投资建议。",
#     name="financial_assistant"
# )

def build_supervisor():
    return create_supervisor(
        agents=[tool_assistant, planner, vision_assistant],
        model=llm,
        prompt=(
            SystemMessage(content=supervisor_prompt)
    ),
    ).compile()

supervisor = build_supervisor()


# =========================
# 主运行逻辑（带热加载）
# =========================
memory_config = {
    "configurable": {
        "thread_id": "research_session_1"
    }
}
    
def output_agent_invoke(query, messages):
    input_message = f"""
用户输入: {query}
原始回答: {messages}
"""
    
    if len(output_message) > OUTPUT_MESSAGE_MAX_LENGTH:
        output_message.pop(0)
        output_message.pop(0)

    styled_result = output_agent.invoke({
    "messages": [
        *output_message,
        HumanMessage(content=input_message)
        ]
    })
    output_message.append(HumanMessage(content=input_message))    # type: ignore
    answer = styled_result["messages"][-1].content
    output_message.append(AIMessage(content=answer))    # type: ignore
    return answer

def init_state() -> AgentState:
    return {
        "recent_messages": [],
        "summary": [],
        "agent_memory": {},
        "tool_cache": {},
        "meta": {}
    }

def compress_history(state: AgentState, max_recent, save_recent):
    if len(state["recent_messages"]) > max_recent:
        print("***************************************")
        print("触发历史压缩，当前 recent_messages 数量:", len(state["recent_messages"]))
        summary = history_compress_agent.invoke({
            "messages": [
                * state['recent_messages'][:-save_recent],   #type:ignore
            ]
        })
        state["summary"].append(summary["messages"][-1].content)
        print("***************************************")
        state["recent_messages"] = state["recent_messages"][-save_recent:]

def construct_supervisor_prompt(state: AgentState, query):
    # 这里可以根据 state 构造更复杂的 prompt，目前先返回固定的 supervisor_prompt
    if state["summary"]:
        summary_prompt = f"\n\n历史总结:\n" + "".join(state["summary"])   
        print(summary_prompt)
        state["recent_messages"].append({"role": "system", "content": summary_prompt})
        state["recent_messages"].append({"role": "user", "content": query})
    else:
        state["recent_messages"].append({"role": "user", "content": query})

    return state["recent_messages"]

def run():
    global supervisor
    query = input("输入：")
    final_output = ""
    last_tool_count = len(load_generated_tools())
    
    compress_history(message_state, max_recent=8, save_recent=4)  # 压缩历史对话，更新 message_state["summary"] 和 message_state["recent_messages"]
    for turn, chunk in enumerate(
        supervisor.stream(
            {
                "messages": construct_supervisor_prompt(message_state, query)
            },
            debug=True,
            config = memory_config, # type: ignore
        )
    ): 
        print(f"\n🧩 Turn {turn}")
        print(chunk)
        print("*" * 50)
        if turn == MAX_AGENT_TURNS - 1:
            print("⚠️⚠️⚠️ 已达到最大循环次数，强制结束")
            break
        final_output = chunk

        # 检测新工具
        try:
            current_tools = load_generated_tools()
            if len(current_tools) != last_tool_count:
                print("检测到新工具，正在热加载...")
                last_tool_count = len(current_tools)
                # 更新工具池
                tool_assistant.tools = base_tools + current_tools #type: ignore
                # 重建 supervisor
                supervisor = build_supervisor()

                print("✅ 新工具已注入系统")
        except Exception as e:
            print(f"⚠️ 热加载工具时出错: {type(e).__name__} {e}")

    # Token 统计
    calculate_tokens_number_multi(final_output)
    print(f"\n✳️ 用户输入：{query}")
    # 原始回答
    print("\n🧑‍🦲 智能体的原始回答：")
    answer = get_final_answer(final_output)
    print(answer)

    message_state["recent_messages"].append({"role": "assistant", "content": answer})

    print("\n🌸 萧毓的回答：")
    answer = output_agent_invoke(query, answer)
    print(answer)
    # supervisor_message.append(AIMessage(content=answer))    # type: ignore
    return answer

if __name__ == "__main__":
    # supervisor_message = load_memory(MESSAGE_SAVE_PATH) # type: ignore
    tts_flag = input("是否开启 TTS 功能？(y/n): ").strip().lower() == 'y'
    message_state = init_state()
    output_message = []
    sync_tool_registry(REGISTRY_PATH)
    while True:
        answer = run()
        total_conversation_input_token, total_conversation_output_token = add_token(0, 0) # 获取当前总 token 数
        print(f"total input tokens: {total_conversation_input_token}, total output tokens so far: {total_conversation_output_token}，这是错的，别看，欧内该")
        if tts_flag:
            print("正在合成语音并发送到 Windows...")
            tts_output(TTS_MODEL, api_key, answer, TTS_SAVE_ROOT_PATH, TTS_HOST, TTS_PORT)
        # save_memory(message_json, MESSAGE_SAVE_PATH)