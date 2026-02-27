from pydantic import BaseModel, Field
from langchain_core.tools import tool

class GetMdTitle(BaseModel):
    file_content: str = Field(description="Markdown文件的文本内容，不包含路径")

@tool(args_schema=GetMdTitle)
def get_md_title(file_content: str) -> list[str]:
    """
    从提供的Markdown文件内容中提取标题（以#开头的行），并返回包含标题的字符串列表。
    Args:
        file_content: str, Markdown文件的完整文本内容
    Returns:
        list[str]: 包含所有标题行的字符串列表，如果没有标题则返回空列表
    """
    titles = []
    lines = file_content.splitlines()
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith('#'):
            title_text = stripped_line.lstrip('#').strip()
            if title_text:
                titles.append(title_text)
    return titles