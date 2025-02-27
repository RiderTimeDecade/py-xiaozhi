import socket
from src.utils import get_device_id
# 🔹 创建全局 UDP 套接字
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 🔹 OTA 服务地址
OTA_VERSION_URL = 'https://api.tenclass.net/xiaozhi/ota/'

# 🔹 设备 MAC 地址
MAC_ADDR = get_device_id()

# 🔹 MQTT 服务器信息
mqtt_info = {}

# 🔹 监听状态
listen_state = None

# 🔹 本地数据
local_sequence = 0

# 🔹 音频传输配置
aes_opus_info = {
    "type": "hello",
    "version": 3,
    "transport": "udp",
    "udp": {
        "server": "120.24.160.13",
        "port": 8884,
        "encryption": "aes-128-ctr",
        "key": "263094c3aa28cb42f3965a1020cb21a7",
        "nonce": "01000000ccba9720b4bc268100000000"
    },
    "audio_params": {
        "format": "opus",
        "sample_rate": 24000,
        "channels": 1,
        "frame_duration": 60
    },
    "session_id": "b23ebfe9"
}
