from pydantic import BaseModel, Field
from langchain_core.tools import tool
from pathlib import Path

class SaveText(BaseModel):
    save_path: str = Field(..., description="要保存的完整路径，包含文件名，例如 './example.txt' 或 '/home/note.md'")
    content: str = Field(..., description="要保存的内容")
    overwrite: bool = Field(default=True, description="bool格式，是否覆盖已存在的文件")

@tool(args_schema=SaveText)
def save_text_file(save_path: str, content: str, overwrite: bool = True) -> str:
    """
    保存 txt 或 md 文件到本地
    参数:
        save_path: 保存路径，包含路径和文件名，例如 "./example.txt" 或 "/home/note.md"
        content: 文件内容
        overwrite: 是否覆盖已有文件
    返回:
        保存结果提示
    """
    # 只允许 txt 和 md
    file_path = Path(save_path)
    suffix = file_path.suffix.lower()
    if suffix not in [".txt", ".md"]:
        return "❌ 仅支持保存 .txt 或 .md 文件"

    # 如果不允许覆盖
    if file_path.exists() and not overwrite:
        return f"❌ 文件 {file_path.name} 已存在，未覆盖"

    # 写入文件
    file_path.write_text(content, encoding="utf-8")

    return f"✅ 文件已成功保存至: {file_path.resolve()}"