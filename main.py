import os
import sys

# 确保 src/ 目录可以被 Python 识别
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.ota import get_ota_version
from src.mqtt_client import MQTTClient
from src.gui import GUI
import logging
# ✅ 配置全局 logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler("app.log", encoding="utf-8")  # 记录到日志文件
    ]
)

def main():
    # 测试日志
    logging.info("✅ 日志系统已初始化")
    """程序入口"""
    # 获取 OTA 版本 & MQTT 服务器信息
    get_ota_version()

    # 启动 MQTT
    mqtt_client = MQTTClient()

    # # 启动 GUI
    gui = GUI(mqtt_client=mqtt_client)
    mqtt_client.gui = gui


if __name__ == "__main__":
    main()
