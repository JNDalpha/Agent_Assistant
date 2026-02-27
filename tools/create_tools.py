from pydantic import BaseModel, Field
from langchain.tools import tool
import os
import json
from datetime import datetime

TOOLS_DIR = "/home/Agent_Assistant/tools/tools_generated"
REGISTRY_PATH = os.path.join(TOOLS_DIR, "tool_registry.json")

os.makedirs(TOOLS_DIR, exist_ok=True)


class CreatePyToolInput(BaseModel):
    tool_name: str = Field(..., description="工具函数名，必须是合法的Python函数名")
    code: str = Field(
        ...,
        description=(
            "完整的Python函数代码，必须："
            "1. 只有一个函数 "
            "2. 函数名必须与tool_name一致 "
            "3. 必须包含docstring和pydantic的参数类型定义 "
            "4. 不要包含涉及系统文件操作、网络请求、子进程等危险操作的代码"
        ),
    )


FORBIDDEN_KEYWORDS = [
    "import os",
    "import sys",
    "subprocess",
    "eval(",
    "exec(",
    "open(",
    "__import__",
]


def is_safe_code(code: str) -> bool:
    return not any(bad in code for bad in FORBIDDEN_KEYWORDS)


@tool("create_python_tool", args_schema=CreatePyToolInput)
def create_python_tool(tool_name: str, code: str) -> str:
    """
    创建一个新的Python工具脚本并保存到本地tools_generated目录，
    同时注册到tool_registry.json中，供后续动态加载使用。
    以下为一个示例：
from pathlib import Path
from pydantic import BaseModel,Field
from langchain_core.tools import tool
class GetFileName(BaseModel):
    directory: str = Field(description="要列出文件的目录路径")
@tool(args_schema=GetFileName)
def list_files(directory: str) -> list[str]:
    \"""
    获取指定目录下的所有文件名（不包含子目录）
    Args:
        directory: str, 目录路径
    Return: 
        list[str]: 目录下的所有文件名列表
    \"""
    path = Path(directory)

    if not path.exists():
        raise ValueError(f"Directory does not exist: {directory}")

    if not path.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    return [
        p.name
        for p in path.iterdir()
        if p.is_file()
    ]
    """

    # 🔒 安全检查
    if not is_safe_code(code):
        return "❌ 代码包含危险操作，已拒绝创建工具"

    if f"def {tool_name}" not in code:
        return "❌ 函数名与tool_name不一致"

    file_path = os.path.join(TOOLS_DIR, f"{tool_name}.py")

    # 💾 写入文件
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)

    # 🗂 更新注册表
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            registry = json.load(f)
    else:
        registry = {}

    registry[tool_name] = {
        "file": file_path,
        "created_at": datetime.now().isoformat(),
    }

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    return f"✅ 工具 {tool_name} 已创建并注册成功"
