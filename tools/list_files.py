from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
import shutil

SAFE_ROOT = '/home/Agent_Assistant/meterials'  # 定义安全根目录

def is_safe(path: Path):
    return SAFE_ROOT in path.resolve().parents or path.resolve() == SAFE_ROOT


class FileManagerInput(BaseModel):
    action: str = Field(description="操作类型: list / copy / move / delete / rename")
    directory: Optional[str] = Field(default=None, description="目录路径（list 操作需要）")
    max_depth: Optional[int] = Field(default=0, description="遍历子目录层数（list 时使用，0 表示仅当前目录）")

    source: Optional[str] = Field(default=None, description="源文件路径（copy/move/delete/rename 使用）")
    destination: Optional[str] = Field(default=None, description="目标路径（copy/move 使用）")

    new_name: Optional[str] = Field(default=None, description="新文件名（rename 使用，包含后缀）")


@tool(args_schema=FileManagerInput)
def file_manager(
    action: str,
    directory: Optional[str] = None,
    max_depth: int = 1,
    source: Optional[str] = None,
    destination: Optional[str] = None,
    new_name: Optional[str] = None,
) -> List[str] | str:
    """
    文件管理工具：
    - list: 列出目录下文件（支持遍历深度）
    - copy: 复制文件
    - move: 剪切文件
    - delete: 删除文件
    - rename: 重命名文件
    """

    action = action.lower()

    # ========= LIST =========
    if action == "list":
        if not directory:
            return "list 操作需要 directory 参数"

        base_path = Path(directory)
        # if not is_safe(base_path):
        #     return "路径超出安全工作目录"

        if not base_path.exists():
            return f"目录不存在: {directory}"

        if not base_path.is_dir():
            return f"不是目录: {directory}"

        results = []

        def walk(path: Path, depth: int):
            if depth < 0:
                return
            for p in path.iterdir():
                if p.is_file():
                    results.append(str(p.relative_to(base_path)))
                elif p.is_dir():
                    walk(p, depth - 1)

        walk(base_path, max_depth)

        return results

    # ========= COPY =========
    elif action == "copy":
        if not source or not destination:
            return "copy 操作需要 source 和 destination"

        src = Path(source)
        dst = Path(destination)

        if not src.exists():
            return f"源文件不存在: {source}"

        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        return f"复制完成: {source} → {destination}"

    # ========= MOVE =========
    elif action == "move":
        if not source or not destination:
            return "move 操作需要 source 和 destination"

        src = Path(source)
        dst = Path(destination)

        if not src.exists():
            return f"源文件不存在: {source}"

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

        return f"移动完成: {source} → {destination}"

    # ========= DELETE =========
    elif action == "delete":
        if not source:
            raise ValueError("delete 操作需要 source")

        src = Path(source)

        if not src.exists():
            raise ValueError(f"文件不存在: {source}")

        if src.is_dir():
            shutil.rmtree(src)
            return f"目录已删除: {source}"
        else:
            src.unlink()
            return f"文件已删除: {source}"

    # ========= RENAME =========
    elif action == "rename":
        if not source or not new_name:
            raise ValueError("rename 操作需要 source 和 new_name")

        src = Path(source)

        if not src.exists():
            raise ValueError(f"文件不存在: {source}")

        new_path = src.with_name(new_name)
        src.rename(new_path)

        return f"重命名完成: {src.name} → {new_name}"

    else:
        raise ValueError(f"不支持的操作类型: {action}")