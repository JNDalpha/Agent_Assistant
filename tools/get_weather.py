
from pydantic import BaseModel
import requests
from langchain_core.tools import tool
import yaml

with open("config/api_keys.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
tool_config = config.get("tool_config", {})
api_key = tool_config.get("weather_api_key", "")

class GetWeather(BaseModel):
    city: str
@tool(args_schema=GetWeather)
def get_weather(city):
    """
    查询实时天气函数
    Args:
        city:必要参数，字符串类型，用于表示被查询天气的城市名称，注意中国城市名字要用对应的英文名称代替
    Return: 
        str:天气查询结果，字符串类型
    """
    # 替换为你自己的 API 密钥
    WEATHER_API_KEY = api_key
    # API 请求的 URL
    URL = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric'
    # 发送 HTTP 请求
    response = requests.get(URL)
    # 检查请求是否成功
    if response.status_code == 200:
        # 获取 JSON 数据
        data = response.json()
        # 提取天气信息
        weather = data['weather'][0]['description']
        temperature = data['main']['temp']
        return {"weather": weather, "temperature": temperature}
    else:
        return {"error": "查询失败"}