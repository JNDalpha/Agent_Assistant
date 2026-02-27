from pydantic import BaseModel, Field
from langchain_core.tools import tool
from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt


class PlotInput(BaseModel):
    file_path: str = Field(description="输入数据文件路径，支持 xml 或 txt")
    plot_type: str = Field(description="图类型: bar, line, box, scatter")
    output_path: str = Field(description="输出图片保存路径")
    title: str = Field(default="Scientific Plot")
    x_label: str = Field(default="X")
    y_label: str = Field(default="Y")


def load_xml_dataset(file_path: str) -> pd.DataFrame:
    tree = ET.parse(file_path)
    root = tree.getroot()

    rows = []

    for group in root.findall("group"):
        group_name = group.attrib["name"]

        for point in group.findall("point"):
            rows.append({
                "group": group_name,
                "x": float(point.attrib["x"]),
                "y": float(point.attrib["y"]),
            })

    return pd.DataFrame(rows)


def load_txt_dataset(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path)


def auto_load_dataset(file_path: str) -> pd.DataFrame:
    suffix = Path(file_path).suffix.lower()

    if suffix == ".xml":
        return load_xml_dataset(file_path)

    elif suffix == ".txt" or suffix == ".csv":
        return load_txt_dataset(file_path)

    else:
        raise ValueError("仅支持 xml 或 txt/csv 文件")


@tool(args_schema=PlotInput)
def scientific_plot_tool(
    file_path: str,
    plot_type: str,
    output_path: str,
    title: str = "Scientific Plot",
    x_label: str = "X",
    y_label: str = "Y",
):
    """
    绘制科研统计图，支持 bar, line, box, scatter。
    自动识别 XML 或 TXT 数据文件。
    """

    df = auto_load_dataset(file_path)

    if df.empty:
        raise ValueError("数据为空，无法绘图")

    plt.figure()

    plot_type = plot_type.lower()

    if plot_type == "line":
        for g in df["group"].unique():
            sub = df[df["group"] == g]
            plt.plot(sub["x"], sub["y"], label=g)

    elif plot_type == "bar":
        pivot = df.pivot_table(index="x", columns="group", values="y")
        pivot.plot(kind="bar")

    elif plot_type == "box":
        df.boxplot(column="y", by="group")

    elif plot_type == "scatter":
        for g in df["group"].unique():
            sub = df[df["group"] == g]
            plt.scatter(sub["x"], sub["y"], label=g)

    else:
        raise ValueError("不支持的图类型")

    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.legend()
    plt.tight_layout()

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(path)
    plt.close()

    return f"图像已生成并保存至 {output_path}"