# windows_audio_server.py
import socket
import pyaudio

HOST = "0.0.0.0"
PORT = 50007
CHUNK = 1024

p = pyaudio.PyAudio()

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000

stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    output=True,
    frames_per_buffer=CHUNK,
)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(5)

print("Windows 音频服务器已启动，等待连接...")

try:
    while True:
        conn, addr = server.accept()
        print(f"🔗 新连接: {addr}")

        try:
            while True:
                data = conn.recv(CHUNK)
                if not data:
                    print("客户端断开")
                    break
                stream.write(data)

        except Exception as e:
            print("播放异常:", e)

        finally:
            conn.close()
            print("等待下一个连接...")

except KeyboardInterrupt:
    print("服务器关闭")

finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    server.close()