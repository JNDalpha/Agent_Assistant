from pathlib import Path
from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class CreateNumberedFoldersInput(BaseModel):
    """
    输入参数：要创建的文件夹数量（1~10）
    """
    folder_count: int = Field(default=10, description="要创建的文件夹数量，范围为1到10")

@tool(args_schema=CreateNumberedFoldersInput)
def create_numbered_folders(folder_count: int) -> List[str]:
    """
    创建指定数量的文件夹，名称从1到folder_count。
    
    Args:
        folder_count: int, 要创建的文件夹数量，必须在1到10之间。
    
    Returns:
        List[str]: 成功创建的文件夹名称列表。
    
    Raises:
        ValueError: 如果folder_count不在1到10之间。
    """
    if not 1 <= folder_count <= 10:
        raise ValueError("folder_count 必须在1到10之间。")

    created_folders = []
    for i in range(1, folder_count + 1):
        folder_path = Path(str(i))
        folder_path.mkdir(exist_ok=True)
        created_folders.append(str(i))

    return created_folders
