from pydantic import BaseModel, Field
from langchain_core.tools import tool
from openai import OpenAI
from pathlib import Path
import base64
import cv2
import yaml
MAX_SIZE = 500
with open("config/api_keys.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
llm_config = config['llm_config']
api_key = llm_config["api_key"]


def image_to_data_url(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists():
        return "图片不存在"
    # 读取图片
    img = cv2.imread(str(path))
    if img is None:
        return "OpenCV 无法读取图片"
    h, w = img.shape[:2]
    # 👉 超过 500x500 才缩放（等比）
    if max(h, w) > MAX_SIZE:
        scale = MAX_SIZE / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # 👉 编码为 PNG（避免多次有损压缩）
    success, buffer = cv2.imencode(".png", img)
    if not success:
        return "图片在转换png时编码失败"

    b64 = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/png;base64,{b64}"

class VisionInput(BaseModel):
    image_path: str = Field(description="本地图片路径，要求是完整的路径，包含根目录和文件名称，可以直接读取到图片文件，例如/home/Agent_Assistant/meterials/xxx.jpg",
                            examples=["/home/Agent_Assistant/meterials/xxx.jpg"])
    question: str = Field(description="关于图片的问题")

@tool(args_schema=VisionInput)
def vision_analyze(image_path: str, question: str) -> str:
    """
    分析本地图片内容并回答问题。本工具会识别用户输入的图片，并根据用户问题给出相应解释。
    """
    client = OpenAI(
        # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
        # 各地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
        api_key = api_key,
        # 以下为北京地域的 base_url，若使用弗吉尼亚地域模型，需要将base_url换成https://dashscope-us.aliyuncs.com/compatible-mode/v1
        # 若使用新加坡地域的模型，需将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    try:
        completion = client.chat.completions.create(
            model="qwen3-vl-flash", # 此处以qwen3.5-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/models
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_to_data_url(image_path),
                            },
                        },
                        {"type": "text", "text": question},
                    ],
                },
            ],
        )
        return str(completion.choices[0].message.content)
    except Exception as e:
        return f"调用视觉分析模型出错: {str(e)}"