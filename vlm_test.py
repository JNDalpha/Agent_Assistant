import os
from openai import OpenAI
from flask import Flask, request, jsonify
import cv2
import base64
from pathlib import Path
MAX_SIZE = 500

def image_to_data_url(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists():
        raise ValueError("图片不存在")
    # 读取图片
    img = cv2.imread(str(path))
    if img is None:
        raise ValueError("OpenCV 无法读取图片")
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
        raise ValueError("图片编码失败")

    b64 = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/png;base64,{b64}"
 
 
# 需要传给大模型的图片
image_path = "/home/Agent_Assistant/meterials/anno.jpg"
 
# 将图片转为Base64编码
base64_image = image_to_data_url(image_path)


client = OpenAI(
    # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
    # 各地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    api_key='sk-3bec25d867714a8a86b32c62a355ed77',
    # 以下为北京地域的 base_url，若使用弗吉尼亚地域模型，需要将base_url换成https://dashscope-us.aliyuncs.com/compatible-mode/v1
    # 若使用新加坡地域的模型，需将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

completion = client.chat.completions.create(
    model="qwen3.5-plus", # 此处以qwen3.5-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/models
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": base64_image,
                    },
                },
                {"type": "text", "text": "图中描绘的是什么景象?"},
            ],
        },
    ],
)
print(completion.choices[0].message.content)