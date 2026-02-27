import os
import traceback
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# 输入参数模型
class CreateFolderInput(BaseModel):
    folder_path: str = Field(..., description="要创建的文件夹完整路径")

# 工具函数
@tool("create_folder")
def create_folder(folder_path: str) -> str:
    """
    在指定路径创建文件夹，如果已存在则提示，若需要再新建文件夹中添加文件，需要先调用此工具新建文件夹，再运行移动文件工具放置，注意先后顺序。
    """
    try:
        if os.path.exists(folder_path):
            return f"文件夹已存在: {folder_path}"
        os.makedirs(folder_path, exist_ok=True)
        return f"文件夹创建成功: {folder_path}"
    except Exception as e:
        return (
            f"❌ 文件夹创建失败\n"
            f"错误类型: {type(e).__name__}\n"
            f"错误信息: {str(e)}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )

