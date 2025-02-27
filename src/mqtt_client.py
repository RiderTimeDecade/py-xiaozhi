import json
import logging
import socket
import threading
import paho.mqtt.client as mqtt
import src.config
from audio_transmission import send_audio,recv_audio
import src.config


class MQTTClient:
    def __init__(self):
        """初始化 MQTT 客户端连接
        
        设置 MQTT 客户端配置，包括：
        - 客户端 ID、用户名和密码认证
        - TLS 加密配置
        - 连接回调函数
        - Socket 配置
        - 音频传输相关的初始化
        
        Raises:
            ValueError: 当 MQTT 配置信息不完整时抛出
        """
        if not src.config.mqtt_info or "client_id" not in src.config.mqtt_info:
            raise ValueError("❌ MQTT 配置错误: 'client_id' 为空！请检查 `get_ota_version()` 是否正确执行。")

        # 初始化 MQTT 客户端，使用 MQTT v5.0 协议
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=src.config.mqtt_info["client_id"]
        )
        
        # 设置认证信息
        self.client.username_pw_set(username=src.config.mqtt_info["username"], 
                                  password=src.config.mqtt_info["password"])

        # 配置 TLS 加密连接
        self.client.tls_set(
            ca_certs=None,
            certfile=None,
            keyfile=None,
            cert_reqs=mqtt.ssl.CERT_REQUIRED,
            tls_version=mqtt.ssl.PROTOCOL_TLS
        )

        # 设置回调函数
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect  # 当 MQTT 连接断开时触发
        # 连接到 MQTT 服务器
        self.client.connect(src.config.mqtt_info["endpoint"], 
                          port=8883, 
                          keepalive=60,
                          clean_start=mqtt.MQTT_CLEAN_START_FIRST_ONLY)

        # 设置 socket 选项，允许地址重用
        self.client.socket().setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # **非阻塞模式** 启动 MQTT 客户端循环（会在后台自动处理 MQTT 事件）
        self.client.loop_start()

        # 初始化状态变量
        self.aes_opus_info = src.config.aes_opus_info  # 音频加密和编码信息
        self.conn_state = False                        # 连接状态标志
        self.tts_state = "stop"                         # TTS 状态
        self.session_id = None  # 会话 ID


        self.recv_audio_thread = threading.Thread()    # 音频接收线程
        self.send_audio_thread = threading.Thread()    # 音频发送线程
        self.send_audio = send_audio                  # 音频发送函数
        self.recv_audio = recv_audio                  # 音频接收函数
        self.gui = None
        self.message_callback = None

    @property
    def conn_state(self):
        """获取当前连接状态
        
        Returns:
            bool: True 表示已连接，False 表示未连接
        """
        return self._conn_state

    @conn_state.setter
    def conn_state(self, value):
        """设置连接状态
        
        Args:
            value (bool): 新的连接状态
        """
        self._conn_state = value

    @property
    def tts_state(self):
        """获取当前 TTS 状态
        
        Returns:
            str 或 None: TTS 的当前状态，None 表示未初始化
        """
        return self._tts_state

    @tts_state.setter
    def tts_state(self, value):
        """设置 TTS 状态
        
        Args:
            value (str): 新的 TTS 状态
        """
        self._tts_state = value

    def on_connect(self, client, userdata, flags, reason_code, properties):
        """MQTT 连接回调函数（V5.0协议）
        
        Args:
            client: MQTT 客户端实例
            userdata: 用户定义数据（未使用）
            flags: 连接标志
            reason_code: 连接结果代码
            properties: 连接属性
        """
        if reason_code.is_failure:
            logging.error(f"❌ 连接失败: {reason_code}")
            return
        logging.info("✅ 成功连接 MQTT 服务器")

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        """MQTT 断开连接回调函数
        
        处理断开连接事件，并尝试自动重连
        
        Args:
            client: MQTT 客户端实例
            userdata: 用户定义数据（未使用）
            disconnect_flags: 断开连接标志
            reason_code: 断开原因代码
            properties: 断开连接属性
        """
        logging.warning(f"⚠️ 连接断开: {reason_code.name}")
        self.client.reconnect()

    def on_message(self, client, userdata, message):
        """处理MQTT消息"""
        try:
            msg = json.loads(message.payload)
            logging.info(f"📩 收到消息: {message.topic} - {msg}")

            if not isinstance(msg, dict) or 'type' not in msg:
                logging.error("❌ 消息格式错误: 缺少type字段")
                return
                
            # 触发GUI回调
            if self.message_callback:
                self.message_callback(msg)
                
            msg_type = msg.get('type')
            if msg_type == 'hello':
                self._handle_hello_message(msg)
            elif msg_type == 'tts':
                self._handle_tts_message(msg)
            elif msg_type == 'goodbye':
                self._handle_goodbye_message(msg)

        except json.JSONDecodeError:
            logging.error("❌ JSON解析错误")
        except Exception as e:
            logging.error(f"❌ 消息处理错误: {str(e)}")

    def _handle_hello_message(self, msg):
        """处理 hello 类型消息
        
        建立 UDP 连接并启动音频传输线程
        
        Args:
            msg (dict): 包含 UDP 服务器信息的消息
        """
        try:
            # 先停止现有的音频线程
            self._stop_audio_threads()
            
            # 关闭现有的UDP连接
            if hasattr(src.config, 'udp_socket') and src.config.udp_socket:
                try:
                    src.config.udp_socket.close()
                except:
                    pass
                    
            if 'udp' in msg and all(k in msg['udp'] for k in ('server', 'port')):
                # 创建新的UDP连接
                src.config.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                src.config.udp_socket.connect((msg['udp']['server'], msg['udp']['port']))
                
                # 更新会话信息
                src.config.aes_opus_info.update(msg)
                self.aes_opus_info = src.config.aes_opus_info
                self.session_id = msg.get('session_id')  # 更新会话ID
                self.conn_state = True
                
                # 启动音频处理线程
                self._start_audio_threads()
                
                logging.info(f"✅ UDP连接已建立，会话ID: {self.session_id}")
            else:
                logging.error("❌ UDP配置信息不完整")
                return

        except Exception as e:
            logging.error(f"❌ 处理hello消息错误: {str(e)}")
            self.conn_state = False
            self.session_id = None

    def _handle_tts_message(self, msg):
        """处理 TTS 类型消息
        
        更新 TTS 状态
        
        Args:
            msg (dict): 包含 TTS 状态的消息
        """
        try:
            if 'state' not in msg:
                logging.error("❌ TTS消息缺少state字段")
                return
            self.tts_state = msg['state']
            logging.info(f"✅ TTS状态更新: {self.tts_state}")
        except Exception as e:
            logging.error(f"❌ 处理TTS消息错误: {str(e)}")

    def _handle_goodbye_message(self, msg):
        """处理 goodbye 类型消息
        
        清理会话资源，关闭连接
        
        Args:
            msg (dict): 包含会话终止信息的消息
        """
        try:
            if msg.get('session_id') != self.session_id:
                logging.warning(f"⚠️ 会话ID不匹配: 期望 {self.session_id}, 收到 {msg.get('session_id')}")
                return

            logging.info("🔚 收到会话终止消息，清理资源")

            # 停止音频线程
            self._stop_audio_threads()

            # 关闭 UDP 连接
            if hasattr(src.config, 'udp_socket') and src.config.udp_socket:
                try:
                    src.config.udp_socket.close()
                except:
                    pass
                src.config.udp_socket = None

            # 重置状态
            self.session_id = None
            self.conn_state = False
            self.aes_opus_info['session_id'] = None

        except Exception as e:
            logging.error(f"❌ 处理goodbye消息错误: {str(e)}")

    def _start_audio_threads(self):
        """启动音频收发线程
        
        创建并启动音频接收和发送线程
        """
        if not self.recv_audio_thread.is_alive():
            self.recv_audio_thread = threading.Thread(target=self.recv_audio)
            self.recv_audio_thread.start()
            logging.info("✅ 启动音频接收线程")

        if not self.send_audio_thread.is_alive():
            self.send_audio_thread = threading.Thread(target=self.send_audio)
            self.send_audio_thread.start()
            logging.info("✅ 启动音频发送线程")

    def _stop_audio_threads(self):
        """停止音频收发线程
        
        等待并终止音频接收和发送线程
        """
        for thread in (self.recv_audio_thread, self.send_audio_thread):
            if thread and thread.is_alive():
                thread.join(timeout=1)
        logging.info("✅ 音频线程已停止")

    def get_session_id(self):
        """获取当前会话ID
        
        Returns:
            str 或 None: 当前会话的ID，如果没有活动会话则返回 None
        """
        return self.session_id

    def set_message_callback(self, callback):
        """设置消息回调函数"""
        self.message_callback = callback

    def publish(self, message):
        """发布消息到MQTT主题并触发GUI回调
        
        Args:
            message: 要发布的消息内容（将被转换为JSON格式）
        """
        # 发布到MQTT主题
        self.client.publish(src.config.mqtt_info['publish_topic'], json.dumps(message))
        
        # 触发GUI回调
        if isinstance(message, dict):
            print(json.dumps(message))
            if self.message_callback:
                self.message_callback(message)
        else:
            print(message)
            if self.message_callback:
                self.message_callback(message)

    def handle_message(self, message):
        """处理接收到的消息"""
        if self.message_callback:
            self.message_callback(message)
        # ... 其他消息处理逻辑保持不变 ...

