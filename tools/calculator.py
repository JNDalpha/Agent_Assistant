from pydantic import BaseModel,Field
from langchain_core.tools import tool
import numexpr
import math

class calculator_tools(BaseModel):
    expression: str = Field(description="The input single line math functions")
@tool(args_schema=calculator_tools)
def calculator(expression: str) -> str:
    """Calculate expression using Python's numexpr library.
    使用python的numexpr库计算数学公式
    Args:
        expression: 输入的单行数学表达式
    Returns:
        str: 返回的计算结果
    Examples:
        "37593 * 67" for "37593 times 67"
        "37593**(1/5)" for "37593^(1/5)"
    """
    local_dict = {"pi": math.pi, "e": math.e}
    return str(
        numexpr.evaluate(
            expression.strip(),
            global_dict={},
            local_dict=local_dict
        )
    )