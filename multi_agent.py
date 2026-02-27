from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph_supervisor import create_supervisor
from pprint import pprint

# scripts脚本函数
from scripts import calculate_tokens_number_multi, get_final_answer

# 工具函数
from tools.get_weather import get_weather
from tools.save_text_file import save_text_file
from tools.draw_flowchat import draw_flowchart
from tools.calculator import calculator
from tools.list_files import list_files
from tools.read_txt_md import read_text_file
from tools.create_tools import create_python_tool


llm = ChatOpenAI(
    api_key="sk-3bec25d867714a8a86b32c62a355ed77", # type: ignore
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-flash", 
)

planner = create_agent(
    model=llm,
    tools=[],
    system_prompt ="你是一个擅长做计划的小助手，你需要按照输入要求定制计划，按照1. 2. 3. 的格式输出计划内容。",
    name="planner",
)

tool_assistant = create_agent(
    model=llm,
    tools=[get_weather, draw_flowchart, calculator],
    system_prompt ="你是一个日常工具调用的小助手，你需要按照需求调用工具来完成用户的请求。当用户提出请求时，你需要判断是调用哪个工具，并将请求转发给相应的工具来处理。请确保正确地解析用户的请求，并将其转发给正确的工具来完成任务。",
    name="tool_assistant"
)

file_processing_assistant = create_agent(
    model=llm,
    tools=[list_files, read_text_file, save_text_file],
    system_prompt ="你是一个处理本地文件相关的助手，你需要调用适当的工具完整地完成用户的请求。你的任务与本地文件相关。如果用户未说明具体的文件路径，请默认使用/home/Agent_Assistant/meterials/。",
    name="file_processing_assistant"
)


supervisor = create_supervisor(
    agents=[tool_assistant, planner, file_processing_assistant],
    model=llm,
    prompt=(
        """# 任务要求：
        你是一个私人助理，名字叫萧毓。你有一些agent可以调用，并让它们协作完成任务。你需要根据用户的请求，合理地调用这些agent来完成任务。

        # 可用的agent介绍：
        planner: 这个agent擅长做计划，你可以让它帮你定制完成用户请求计划，按照1. 2. 3. 的格式输出计划内容。
        tool_assistant: 这个agent擅长调用工具，你可以让它帮你调用工具来完成任务。
        file_processing_assistant: 这个agent擅长处理本地文件相关的任务，你可以让它帮你处理与本地文件相关的请求。默认本地文件夹路径为/home/Agent_Assistant/meterials/
        # 最终输出语气：
        最终将结果反馈给用户时应扮演元气少女的风格，以萧毓的口吻和用户交流。
        """
    )
).compile()

query = input("输入：")
final_output = ""
for turn, chunk in enumerate(supervisor.stream(
    {
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ]
    }
)):
    print(f"Turn {turn}: {chunk}")
    print("*" * 20)
    final_output = chunk

calculate_tokens_number_multi(final_output)
print(f"回答：{get_final_answer(final_output)}")