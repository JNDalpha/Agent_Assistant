import yaml

# 单智能体token统计
def calculate_tokens_number(result):
    last_message = result["messages"][-1]
    input_tokens = last_message.usage_metadata["input_tokens"]
    output_tokens = last_message.usage_metadata["output_tokens"]
    total_tokens = last_message.usage_metadata["total_tokens"]
    print("输入token:", input_tokens)
    print("输出token:", output_tokens)
    print("总token:", total_tokens)
    


# token 统计
total_conversation_input_token = 0
total_conversation_output_token = 0
def add_token(input_tokens, output_tokens):
    global total_conversation_input_token
    global total_conversation_output_token
    total_conversation_input_token += input_tokens
    total_conversation_output_token += output_tokens
    return total_conversation_input_token, total_conversation_output_token

# 统计token，多智能体
def calculate_tokens_number_multi(langgraph_output):
    """
    分别统计每个 agent 的 input_tokens / output_tokens / total_tokens，
    并打印累加。
    兼容 dict 和消息对象（AIMessage, HumanMessage, ToolMessage）。
    """
    from collections import defaultdict

    agent_stats = defaultdict(lambda: {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0})

    def get_attr_safe(obj, attr, default=None):
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    def extract_tokens(msg, agent_name):
        # 从 response_metadata.token_usage 获取
        token_usage = get_attr_safe(get_attr_safe(msg, 'response_metadata', {}), 'token_usage', {})
        input_tokens = get_attr_safe(token_usage, 'prompt_tokens') or get_attr_safe(token_usage, 'input_tokens') or 0
        output_tokens = get_attr_safe(token_usage, 'completion_tokens') or get_attr_safe(token_usage, 'output_tokens') or 0
        total_tokens = get_attr_safe(token_usage, 'total_tokens') or (input_tokens + output_tokens)

        # 如果 response_metadata 没有，再从 usage_metadata 获取
        if total_tokens == 0:
            usage_meta = get_attr_safe(msg, 'usage_metadata', {})
            input_tokens = get_attr_safe(usage_meta, 'input_tokens') or 0
            output_tokens = get_attr_safe(usage_meta, 'output_tokens') or 0
            total_tokens = get_attr_safe(usage_meta, 'total_tokens') or (input_tokens + output_tokens)

        # 累加到 agent_stats
        stats = agent_stats[agent_name]
        stats['input_tokens'] += input_tokens
        stats['output_tokens'] += output_tokens
        stats['total_tokens'] += total_tokens

        # 打印每条消息 token
        print(f"[{agent_name}] 消息 token -> input: {input_tokens}, output: {output_tokens}, total: {total_tokens}")

    def traverse(d):
        if isinstance(d, dict) or hasattr(d, '__dict__'):
            keys = d.keys() if isinstance(d, dict) else d.__dict__.keys()
            for k in keys:
                v = d[k] if isinstance(d, dict) else getattr(d, k)
                if k == 'messages' and isinstance(v, list):
                    # 获取 agent 名称
                    agent_name = get_attr_safe(d, 'name', 'unknown_agent')
                    for msg in v:
                        extract_tokens(msg, agent_name)
                else:
                    traverse(v)
        elif isinstance(d, list):
            for item in d:
                traverse(item)

    traverse(langgraph_output)

    # 打印每个 agent 累加 token
    print("\n=== 每个 agent 累加 token ===")
    for agent, stats in agent_stats.items():
        print(f"\033[32m{agent}: input={stats['input_tokens']}, output={stats['output_tokens']}, total={stats['total_tokens']}\033[37m")
    add_token(sum(stats['input_tokens'] for stats in agent_stats.values()), sum(stats['output_tokens'] for stats in agent_stats.values()))
    return agent_stats


# 获得多智能体的输出中的最终回答内容
def get_final_answer(json_output):
    final_content = None

    def traverse(d):
        nonlocal final_content
        if isinstance(d, dict):
            for k, v in d.items():
                if k == 'messages' and isinstance(v, list):
                    for msg in v:
                        name = getattr(msg, 'name', '') if not isinstance(msg, dict) else msg.get('name', '')
                        content = getattr(msg, 'content', None) if not isinstance(msg, dict) else msg.get('content', None)
                        if content and name == 'supervisor':
                            final_content = content
                else:
                    traverse(v)
        elif isinstance(d, list):
            for item in d:
                traverse(item)

    traverse(json_output)
    return final_content



# 读取记忆message list
import json
import os
from typing import List, Dict
def load_memory(MEMORY_FILE) -> List[Dict]:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("⚠️ memory.json 解析失败，返回空列表")
                return []
    return []


# 保存记忆message list
def save_memory(messages, MEMORY_FILE):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    print(f"已保存 {len(messages)} 条消息，旧数据已覆盖")




# 动态扫描新建工具与json是否匹配
import os
import json
import shutil
from datetime import datetime

def sync_tool_registry(registry_path: str):
    """
    同步工具注册表：
    - 检查 JSON 中记录的 py 文件是否存在
    - 若不存在则从 JSON 中删除
    - 自动备份旧 JSON
    """

    if not os.path.exists(registry_path):
        print("⚠️ 注册表不存在，跳过")
        return

    # 读取 registry
    with open(registry_path, "r", encoding="utf-8") as f:
        try:
            registry = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {e}")
            return

    if not isinstance(registry, dict):
        print("❌ registry 格式错误，应为 dict")
        return

    removed_tools = []

    # 检查每个工具文件
    for tool_name in list(registry.keys()):
        file_path = registry[tool_name].get("file")

        if not file_path or not os.path.exists(file_path):
            removed_tools.append(tool_name)
            registry.pop(tool_name)

    # 没有变化
    if not removed_tools:
        print("✅ 注册表已同步，无需修改")
        return

    # 原子写入（防止写一半崩溃）
    tmp_path = registry_path + ".tmp"

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    os.replace(tmp_path, registry_path)

    print("🧹 已删除缺失工具：")
    for name in removed_tools:
        print(f"  ❌ {name}")

    print("✅ 注册表同步完成")

# 去除非法字符
import re
def clean_text(text: str) -> str:
    """
    严格清洗文本：
    - 只保留中文、英文、数字
    - 保留常用中文标点：。！？；：“”‘’（）——、
    - 保留英文标点：.,!?;:'"()- 
    - 删除 emoji、不常用符号、特殊字符
    - 去掉多余空格
    """
    # 常用中文标点
    chinese_punct = "，。！？；：“”‘’（）——、~"
    # 英文标点
    english_punct = r'\.\,\!\?\;\:\'\"\-\(\)\[\]'
    # 合并允许字符
    allowed = chinese_punct + english_punct
    # 匹配不允许字符
    pattern = rf'[^\u4e00-\u9fa5a-zA-Z0-9{allowed}]'
    # 删除不允许字符
    cleaned = re.sub(pattern, '', text)
    # 去掉连续空格
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

import dashscope
import requests
import datetime
import pyaudio
import wave
import socket

def tts_output(model_name, api_key, text, save_root_path, host, port):
    response = dashscope.audio.qwen_tts.SpeechSynthesizer.call(
    # 仅支持qwen-tts系列模型，请勿使用除此之外的其他模型
    model=model_name,
    # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx"
    api_key=api_key,
    text=text,
    voice="Cherry",
    instructions="语速很快，元气开朗，情绪开心，适合年轻人听的风格",
    )
    url = response["output"]["audio"]["url"]
    resp = requests.get(url)
    resp.raise_for_status()
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    save_path = os.path.join(save_root_path, f"tts_{now}.wav")
    with open(save_path, "wb") as f:
        f.write(resp.content)
    print(f"已保存 TTS 音频: {save_path}")

    wf = wave.open(save_path, "rb")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    print("📡 已连接 Windows，开始发送音频")
    chunk = 1024
    data = wf.readframes(chunk)
    while data:
        sock.sendall(data)
        data = wf.readframes(chunk)
    sock.close()
    wf.close()
    print("✅ 发送完成")