from typing import List, Dict
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class BarChartData(BaseModel):
    data: Dict[str, float] = Field(description="条形图的数据，键为标签，值为数值")
    title: str = Field(default="条形图", description="图表标题")
    xlabel: str = Field(default="类别", description="X轴标签")
    ylabel: str = Field(default="数值", description="Y轴标签")
    width: float = Field(default=0.8, description="条形图的宽度")
    color: str = Field(default="skyblue", description="条形图的颜色")

@tool(args_schema=BarChartData)
def draw_bar_chart(data: Dict[str, float], title: str = "条形图", xlabel: str = "类别", ylabel: str = "数值", width: float = 0.8, color: str = "skyblue") -> None:
    """
    绘制条形统计图。
    
    Args:
        data: Dict[str, float], 条形图的数据，键为标签，值为数值。
        title: str, 图表标题，默认为"条形图"。
        xlabel: str, X轴标签，默认为"类别"。
        ylabel: str, Y轴标签，默认为"数值"。
        width: float, 条形图的宽度，默认为0.8。
        color: str, 条形图的颜色，默认为"skyblue"。
    
    Returns:
        None, 仅绘制图表，不返回任何值。
    """
    import matplotlib.pyplot as plt

    # 提取标签和数值
    labels = list(data.keys())
    values = list(data.values())

    # 绘制条形图
    plt.figure(figsize=(10, 6))
    plt.bar(labels, values, width=width, color=color)
    
    # 设置标题和坐标轴标签
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    
    # 旋转X轴标签以避免重叠（可选）
    plt.xticks(rotation=45)
    
    # 显示图表（注意：此处不会实际显示，因为环境限制）
    # plt.show()
    
    # 保存图表到文件（用于后续查看）
    plt.savefig("bar_chart_example.png")
    plt.close()
    
    print("条形图已成功绘制并保存为 'bar_chart_example.png'。")
    
    # 返回一个提示信息，说明图表已生成
    return "条形图已成功绘制并保存为 'bar_chart_example.png'。"