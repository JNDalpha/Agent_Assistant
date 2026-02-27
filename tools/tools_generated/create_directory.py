from pathlib import Path
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class CreateDirectoryInput(BaseModel):
    directory_path: str = Field(description="要创建的目录路径")
    
@tool(args_schema=CreateDirectoryInput)
def create_directory(directory_path: str) -> str:
    """
    创建一个新目录
    Args:
        directory_path: str, 要创建的目录路径
    Returns:
        str: 创建结果信息
    """
    path = Path(directory_path)
    
    if path.exists():
        return f"目录已存在: {directory_path}"
    
    try:
        path.mkdir(parents=True, exist_ok=True)
        return f"成功创建目录: {directory_path}"
    except Exception as e:
        return f"创建目录失败: {str(e)}"