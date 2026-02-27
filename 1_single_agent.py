# 已作废

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.agents.middleware import (
    before_model,
    wrap_model_call,
    AgentState,
    ModelRequest,
    ModelResponse,
)
from langgraph.runtime import Runtime
from typing_extensions import NotRequired, TypedDict
from typing import Any

# 脚本函数
from scripts import calculate_tokens_number

# 工具
from tools.save_txt import save_txt
from tools.get_weather import get_weather


llm = ChatOpenAI(
    api_key="your api key", # type: ignore
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-flash", 
)
class MyState(TypedDict):
    messages: list
    summary: str
    user_profile: dict


@before_model
def log_before_model(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    print(f" 当前message长度: {len(state['messages'])}")


agent = create_agent(
    model=llm,
    middleware=[log_before_model],
    tools=[save_txt, get_weather],
    state_schema= MyState # type: ignore
)

def main():
    message_state = {
            "messages": [SystemMessage(content="你是一个人工智能私人助手，名字叫萧毓，协助用户完成各种任务。你需要尽可能完成用户要去，如果出现未知情况可以选择调用工具来辅助完成任务。如果工具无法完成任务，你需要向用户说明原因并提供建议。")],
            "summary": "",
            "user_profile": {}
        }
    while 1:
        query = input("输入：")
        message_state["messages"].append(HumanMessage(content=query))
        result = agent.invoke(message_state) # type: ignore
        # print(result)
        calculate_tokens_number(result)
        message_state["messages"].append(AIMessage(content=result["messages"][-1].content)) # type: ignore
        print("输出：", result["messages"][-1].content) # type: ignore
        print("*" * 20)
            
if __name__ == "__main__":
    main()
