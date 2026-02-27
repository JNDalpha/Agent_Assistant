from pathlib import Path
from pydantic import BaseModel,Field
from langchain_core.tools import tool


class ReadTextFile(BaseModel):
    file_path: str = Field(description="要读取的 txt 或 md 文件的路径")
@tool(args_schema=ReadTextFile)
def read_text_file(file_path: str) -> str:
    """
    读取 txt 或 md 文件内容
    args:
        file_path: 文件路径
    return:
        文件内容字符串
    """
    path = Path(file_path)

    if not path.exists():
        return f"文件不存在: {file_path}"

    if path.suffix.lower() not in [".txt", ".md"]:
        return "只支持 .txt 和 .md 文件"

    # 尝试 utf-8 读取
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # fallback 兼容 Windows
        return path.read_text(encoding="gbk")