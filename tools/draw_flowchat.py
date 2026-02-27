import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from graphviz import Digraph
from pydantic import BaseModel,Field
from langchain_core.tools import tool


class flowchart(BaseModel):
    node_info: list = Field(description="The flowchart node and name in a list,constructed as the format[[name,node],[name,node]], name must be a English letter, such as A, B etc.",
                           examples=[["A","node1"],["B","noded2"],["C","node3"]])
    connection: list = Field(description="The relationship between the nodes in this flowchart",
                            examples=["AB","AC"])
    save_path: str = Field(description="The output path of the flowchart, with the flowchat name",
                            examples=["./flowchart.png"])
@tool(args_schema=flowchart)
def draw_flowchart(node_info, connection, save_path):
    """
    绘制流程图函数
    Args:
        node_info:list,节点信息，为一个二维list数据。其中每个节点包含两个参数，第一个是节点名称，按照A，B，C等依次命名，第二个是节点的显示内容，为在流程图上展示的内容。所有的节点信息list保存在一个总的list中，总的list就是node_info
        connection:list，节点关系list，用于储存节点之间的联系关系。将相关联的两个节点的名称拼接为一个str，例如节点A和节点B，则拼接为AB，代表由A指向B。将所有关系存储在一个list中，这个总的list就是connection。
        save_path:str，表示本流程图的保存路径，包含文件名
    Return: 
        str:返回绘图结果
    """
    # 使用 Graphviz 创建流程图
    dot = Digraph(comment='Flowchart',encoding='utf-8')
    dot.attr('graph', fontname='SimSun')  # 例如，设置为宋体
    dot.attr('node', fontname='SimSun')
    dot.attr('edge', fontname='SimSun')

    for node in node_info:
        dot.node(node[0],node[1])

    dot.edges(connection)

    # 保存为图片
    dot.render(save_path, format='png', cleanup=True)
    return f"流程图绘制成功，已保存为 {save_path}"

