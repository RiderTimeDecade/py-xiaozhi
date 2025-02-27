import pyaudio
import opuslib
import socket
import time
import logging
import src.config
from src.utils import aes_ctr_encrypt, aes_ctr_decrypt

# 初始化 PyAudio
audio = pyaudio.PyAudio()


def send_audio():
    """音频采集和发送线程函数
    1. 采集麦克风音频数据
    2. 使用 Opus 进行音频编码
    3. 使用 AES-CTR 进行加密
    4. 通过 UDP 发送音频数据
    """

    key = src.config.aes_opus_info['udp']['key']
    nonce = src.config.aes_opus_info['udp']['nonce']
    server_ip = src.config.aes_opus_info['udp']['server']
    server_port = src.config.aes_opus_info['udp']['port']

    # 初始化 Opus 编码器
    encoder = opuslib.Encoder(16000, 1, opuslib.APPLICATION_AUDIO)

    if audio is None:
        raise RuntimeError("❌ PyAudio 未初始化！")
    if src.config.udp_socket is None:
        raise RuntimeError("❌ UDP 套接字未初始化！")

    # 打开麦克风流 (帧大小应与 Opus 编码器匹配)
    mic = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=960)

    try:
        while src.config.udp_socket:
            # 如果监听状态是 "stop"，则暂停发送
            if src.config.listen_state is not None and src.config.listen_state == "stop":
                time.sleep(0.1)
                continue

            # 读取 960 采样点的音频数据
            data = mic.read(960, exception_on_overflow=False)

            # Opus 编码（将 PCM 音频数据压缩）
            encoded_data = encoder.encode(data, 960)
            src.config.local_sequence += 1  # 更新音频数据的序列号

            # 🔹 生成新的 nonce（加密 IV）
            # **nonce 结构**
            # - 前 4 字节: 固定前缀
            # - 5-8 字节: 当前数据长度
            # - 9-24 字节: 原始 nonce
            # - 25-32 字节: 递增的 sequence (防止重放攻击)
            new_nonce = nonce[:4] + format(len(encoded_data), '04x') + nonce[8:24] + format(src.config.local_sequence, '08x')

            # 🔹 AES 加密 Opus 编码数据
            encrypt_encoded_data = aes_ctr_encrypt(
                bytes.fromhex(key),
                bytes.fromhex(new_nonce),
                bytes(encoded_data)
            )

            # 🔹 拼接 nonce 和密文
            packet_data = bytes.fromhex(new_nonce) + encrypt_encoded_data

            # 发送音频数据
            if src.config.udp_socket:
                src.config.udp_socket.sendto(packet_data, (server_ip, server_port))

    except Exception as e:
        logging.error(f"❌ send_audio 发生错误: {e}")

    finally:
        logging.info("🔴 send_audio 线程退出")
        src.config.local_sequence = 0  # 归零序列号
        if src.config.udp_socket:
            src.config.udp_socket.close()
            src.config.udp_socket = None
        mic.stop_stream()
        mic.close()


def recv_audio():
    """音频接收和播放线程函数
    1. 通过 UDP 接收音频数据
    2. 使用 AES-CTR 进行解密
    3. 使用 Opus 进行解码
    4. 播放 PCM 音频
    """

    key = src.config.aes_opus_info['udp']['key']
    nonce = src.config.aes_opus_info['udp']['nonce']
    sample_rate = src.config.aes_opus_info['audio_params']['sample_rate']
    frame_duration = src.config.aes_opus_info['audio_params']['frame_duration']

    # 🔹 计算 Opus 解码所需的帧数
    # **计算方式**：
    # 1. `frame_duration` (ms) / (1000 / sample_rate) = 每帧采样点数
    # 2. 例如：`frame_duration = 60ms`，`sample_rate = 24000`，则 `frame_num = 1440`
    frame_num = int(sample_rate * (frame_duration / 1000))

    logging.info(f"🔵 recv_audio: 采样率 -> {sample_rate}, 帧时长 -> {frame_duration}ms, 帧数 -> {frame_num}")

    # 初始化 Opus 解码器
    decoder = opuslib.Decoder(sample_rate, 1)

    # 确保 `audio` 正确初始化
    if audio is None:
        raise RuntimeError("❌ PyAudio 未初始化！")

    # 打开扬声器输出流
    spk = audio.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, output=True, frames_per_buffer=frame_num)

    try:
        while src.config.udp_socket:
            # 监听 UDP 端口接收音频数据
            data, _ = src.config.udp_socket.recvfrom(4096)

            # 🔹 分离 nonce 和加密音频数据
            received_nonce = data[:16]
            encrypted_audio = data[16:]

            # 🔹 AES 解密
            decrypted_audio = aes_ctr_decrypt(
                bytes.fromhex(key),
                received_nonce,
                encrypted_audio
            )

            # 🔹 Opus 解码（将解密后的数据转换为 PCM）
            pcm_audio = decoder.decode(decrypted_audio, frame_num)

            # 播放解码后的 PCM 音频
            spk.write(pcm_audio)

    except Exception as e:
        logging.error(f"❌ recv_audio 发生错误: {e}")
    finally:
        logging.info("🔴 recv_audio 线程退出")
        if src.config.udp_socket:
            src.config.udp_socket.close()
            src.config.udp_socket = None
        spk.stop_stream()
        spk.close()
