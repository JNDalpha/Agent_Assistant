from pydantic import BaseModel, Field
from langchain_core.tools import tool
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any


class Point(BaseModel):
    x: float
    y: float


class Group(BaseModel):
    name: str
    points: List[Point]


class XMLDatasetInput(BaseModel):
    file_path: str = Field(description="XML 文件保存路径")
    dataset_name: str = Field(description="数据集名称")
    meta: Dict[str, Any] = Field(default_factory=dict, description="元数据，例如模型名、数据集名等")
    groups: List[Group] = Field(description="实验分组数据")


@tool(args_schema=XMLDatasetInput)
def xml_dataset_writer_tool(
    file_path: str,
    dataset_name: str,
    meta: Dict[str, Any],
    groups: List[Group],
):
    """
    创建 XML 数据文件，用于科研绘图。
    支持多实验组、多点数据、元数据存储。
    """

    root = ET.Element("dataset", name=dataset_name)

    # 写入 meta 信息
    if meta:
        meta_elem = ET.SubElement(root, "meta")
        for k, v in meta.items():
            item = ET.SubElement(meta_elem, k)
            item.text = str(v)

    # 写入 group 数据
    for group in groups:
        group_elem = ET.SubElement(root, "group", name=group.name)

        for point in group.points:
            ET.SubElement(
                group_elem,
                "point",
                x=str(point.x),
                y=str(point.y),
            )

    # 保存文件
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    tree = ET.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)

    return f"XML 数据集已创建：{file_path}"