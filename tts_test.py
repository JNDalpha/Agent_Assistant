# DashScope SDK 版本不低于 1.23.1
import os
import dashscope
import requests
import pyaudio
import wave
import socket


text = "那我来给大家推荐一款T恤，这款呢真的是超级好看，哈哈哈哈哈哈哈哈哈，这个颜色呢很显气质"
print("正在合成语音...")
response = dashscope.audio.qwen_tts.SpeechSynthesizer.call(
    # 仅支持qwen-tts系列模型，请勿使用除此之外的其他模型
    model="qwen3-tts-flash",
    # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx"
    api_key='sk-3bec25d867714a8a86b32c62a355ed77',
    text=text,
    voice="Cherry",
)
print(response)

def save_tts_audio(tts_result: dict, save_path="tts.wav"):
    url = tts_result["output"]["audio"]["url"]

    resp = requests.get(url)
    resp.raise_for_status()

    with open(save_path, "wb") as f:
        f.write(resp.content)

    return save_path
save_tts_audio(response)


HOST = "172.22.128.1"   # ⚠️ 改成 Windows 的 IP
PORT = 50007

def send_wav(path):
    print(f"📡 正在连接 Windows 以发送 {path}...")
    wf = wave.open(path, "rb")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    print("📡 已连接 Windows，开始发送音频")

    chunk = 1024
    data = wf.readframes(chunk)

    while data:
        sock.sendall(data)
        data = wf.readframes(chunk)

    sock.close()
    wf.close()
    print("✅ 发送完成")

send_wav("tts.wav")