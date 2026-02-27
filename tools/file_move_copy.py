import os
import shutil
import traceback
from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# 输入参数模型
class FileMoveCopyBatchInput(BaseModel):
    source_paths: List[str] = Field(..., description="要操作的源文件路径列表")
    target_dir: str = Field(..., description="目标文件夹路径")
    operation: str = Field(
        "copy",
        description="操作类型: 'copy' 表示复制, 'move' 表示剪切/移动",
    )

# 工具函数
@tool("file_move_copy_batch")
def file_move_copy_batch(source_paths: List[str], target_dir: str, operation: str = "copy") -> str:
    """
    用于移动文件或者剪切文件到新的目录，支持批量复制或剪切文件到指定目录
    当不需要对文件内容进行读取，只需要修改文件位置时候使用此工具
    """
    results = []
    try:
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        for src in source_paths:
            try:
                if not os.path.exists(src):
                    results.append(f"❌ 源文件不存在: {src}")
                    continue

                filename = os.path.basename(src)
                target_path = os.path.join(target_dir, filename)

                if operation == "copy":
                    shutil.copy2(src, target_path)
                    results.append(f"✅ 文件已复制: {src} → {target_path}")
                elif operation == "move":
                    shutil.move(src, target_path)
                    results.append(f"✅ 文件已移动: {src} → {target_path}")
                else:
                    results.append(f"❌ 不支持的操作类型: {operation}")

            except Exception as e:
                results.append(
                    f"❌ 文件操作失败: {src}\n"
                    f"错误类型: {type(e).__name__}\n"
                    f"错误信息: {str(e)}\n"
                    f"Traceback:\n{traceback.format_exc()}"
                )
        return "\n".join(results)

    except Exception as e:
        return (
            f"❌ 批量操作初始化失败\n"
            f"错误类型: {type(e).__name__}\n"
            f"错误信息: {str(e)}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )

