import threading
import customtkinter as ctk
import platform
import subprocess
import concurrent.futures
from PIL import Image, ImageTk
import os
import src.config
import socket
import json
from datetime import datetime

class GUI:
    def __init__(self, mqtt_client):
        self.mqtt_client = mqtt_client
        # 设置消息回调
        self.mqtt_client.set_message_callback(self.handle_message)
        
        # 设置主题和外观
        self.current_theme = "light"  # 默认为白天模式
        ctk.set_appearance_mode(self.current_theme)
        ctk.set_default_color_theme("blue")
        
        # 初始化情感状态
        self.current_emotion = "neutral"
        self.emotion_icons = {
            'thinking': '🤔',
            'funny': '😂',
            'happy': '😊',
            'sad': '😢',
            'angry': '😠',
            'surprised': '😮',
            'confused': '😕',
            'neutral': '😐'
        }
        # 记录最后一条AI消息的头像标签
        self.last_ai_avatar_label = None
        
        # 创建主窗口
        root = ctk.CTk()
        self.root = root
        self.root.title("小智语音助手")
        self.root.geometry("800x600")
        self.root.configure(fg_color=("gray95", "gray10"))  # 更柔和的背景色
        
        # 显示验证码窗口
        self.show_verification_code()
        
        # 音量控制相关变量初始化
        self.volume_timer = None
        self.volume_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.last_volume = 50
        self.volume_debounce_time = 300
        
        # 创建左侧边栏
        self.sidebar = ctk.CTkFrame(
            root,
            width=200,
            corner_radius=0,
            fg_color=("gray90", "gray15")
        )
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar.pack_propagate(False)
        
        # Logo区域
        logo_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )
        logo_frame.pack(pady=20, padx=10)
        
        self.logo_label = ctk.CTkLabel(
            logo_frame,
            text="小智助手",
            font=("SF Pro Display", 24, "bold"),
            text_color=("gray10", "gray90")
        )
        self.logo_label.pack()
        
        # 版本号
        version_label = ctk.CTkLabel(
            logo_frame,
            text="v1.0.0",
            font=("SF Pro Display", 10),
            text_color=("gray40", "gray60")
        )
        version_label.pack()
        
        # 分割线
        separator = ctk.CTkFrame(
            self.sidebar,
            height=1,
            fg_color=("gray80", "gray25")
        )
        separator.pack(fill="x", padx=15, pady=10)
        
        # 主题切换按钮
        self.theme_button = ctk.CTkButton(
            self.sidebar,
            text="🌙 夜间模式",  # 由于默认是白天模式，所以显示切换到夜间模式的选项
            font=("SF Pro Display", 14),
            height=40,
            corner_radius=8,
            command=self.toggle_theme,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray20")
        )
        self.theme_button.pack(pady=10, padx=20, fill="x")
        
        # 清除消息按钮
        self.clear_button = ctk.CTkButton(
            self.sidebar,
            text="🗑️ 清除消息",
            font=("SF Pro Display", 14),
            height=40,
            corner_radius=8,
            command=self.clear_messages,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray20")
        )
        self.clear_button.pack(pady=10, padx=20, fill="x")
        
        # 添加弹性空间
        spacer = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )
        spacer.pack(fill="both", expand=True)
        
        # 创建主内容区
        self.main_content = ctk.CTkFrame(
            root,
            corner_radius=15,
            fg_color=("gray95", "gray10")
        )
        self.main_content.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        # 状态栏
        self.status_frame = ctk.CTkFrame(
            self.main_content,
            height=40,
            corner_radius=8,
            fg_color=("gray90", "gray15")
        )
        self.status_frame.pack(fill="x", padx=10, pady=10)
        
        # 状态图标
        self.status_icon = ctk.CTkLabel(
            self.status_frame,
            text="🟢" if self.mqtt_client.conn_state else "🔴",
            font=("SF Pro Display", 14),
            text_color=("green" if self.mqtt_client.conn_state else "red")
        )
        self.status_icon.pack(side="left", padx=(15, 5), pady=8)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame, 
            text="状态: 未连接",
            font=("SF Pro Display", 14),
            text_color=("gray10", "gray90")
        )
        self.status_label.pack(side="left", pady=8)
        
        # 添加情感状态显示
        self.emotion_label = ctk.CTkLabel(
            self.status_frame,
            text=self.emotion_icons[self.current_emotion],
            font=("Segoe UI Emoji", 18),  # 使用支持emoji的字体
            text_color=("gray10", "gray90")
        )
        self.emotion_label.pack(side="right", padx=15, pady=8)
        
        # 消息显示区域
        self.messages_frame = ctk.CTkScrollableFrame(
            self.main_content,
            corner_radius=8,
            fg_color=("gray90", "gray15")
        )
        self.messages_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.messages = []
        
        # 底部控制区
        self.bottom_frame = ctk.CTkFrame(
            self.main_content,
            corner_radius=8,
            fg_color=("gray90", "gray15")
        )
        self.bottom_frame.pack(fill="x", padx=10, pady=10)
        
        # 音量控制区域
        self.volume_frame = ctk.CTkFrame(
            self.bottom_frame,
            fg_color="transparent"
        )
        self.volume_frame.pack(fill="x", padx=15, pady=5)
        
        volume_icon = ctk.CTkLabel(
            self.volume_frame, 
            text="🔊",
            font=("SF Pro Display", 16),
            text_color=("gray10", "gray90")
        )
        volume_icon.pack(side="left", padx=(0, 10))
        
        self.volume_slider = ctk.CTkSlider(
            self.volume_frame,
            from_=0,
            to=100,
            command=lambda v: self.handle_volume_change(int(v)),
            progress_color=("#1677ff", "#1677ff"),
            button_color=("#ffffff", "#ffffff"),
            button_hover_color=("#f0f0f0", "#f0f0f0")
        )
        self.volume_slider.set(50)
        self.volume_slider.pack(side="left", fill="x", expand=True, padx=5)
        
        # 语音控制按钮
        self.talk_button = ctk.CTkButton(
            self.bottom_frame,
            text="按住说话",
            font=("SF Pro Display", 16, "bold"),
            height=50,
            corner_radius=25,
            fg_color=("#1677ff", "#1677ff"),
            hover_color=("#1668dc", "#1668dc")
        )
        self.talk_button.pack(pady=15, padx=20, fill="x")
        
        # 添加录音状态指示
        self.recording = False
        
        # 绑定按钮事件
        self.talk_button.bind("<ButtonPress-1>", self.on_button_press)
        self.talk_button.bind("<ButtonRelease-1>", self.on_button_release)
        
        # 状态更新线程
        threading.Thread(target=self.update_status, daemon=True).start()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def handle_message(self, message):
        """处理接收到的消息"""
        try:
            data = message if isinstance(message, dict) else json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'stt':
                # 显示语音识别结果
                text = data.get('text', '')
                if text:
                    self.add_message(text, is_user=True)
                    
            elif msg_type == 'tts':
                # 显示AI回复
                state = data.get('state')
                text = data.get('text', '')
                if state == 'sentence_start' and text:
                    self.add_message(text, is_user=False)
                        
            elif msg_type == 'llm':
                # 处理情感和文本
                emotion = data.get('emotion', '')
                text = data.get('text', '')
                
                # 如果有情感变化，只更新状态栏和最后一条AI消息的表情
                if emotion:
                    self.update_emotion(emotion)
                    if self.last_ai_avatar_label:
                        self.last_ai_avatar_label.configure(text=self.emotion_icons[emotion])
                
                # 只有在有文本内容时才添加新消息
                if text:
                    self.add_message(text, is_user=False)

        except Exception as e:
            print(f"处理消息失败: {e}")

    def stream_text(self, label, text, delay=30):
        """优化的流式输出文本效果"""
        if not hasattr(self, '_stream_text_cache'):
            self._stream_text_cache = {}
            
        # 为每个label创建独立的计数器
        label_id = id(label)
        if label_id not in self._stream_text_cache:
            self._stream_text_cache[label_id] = 0
            
        def update_text():
            if self._stream_text_cache[label_id] < len(text):
                current_text = text[:self._stream_text_cache[label_id] + 1]
                label.configure(text=current_text)
                self._stream_text_cache[label_id] += 1
                self.root.after(delay, update_text)
            else:
                # 清理缓存
                del self._stream_text_cache[label_id]
                
        update_text()

    def add_message(self, text, is_user=True):
        """添加新消息到消息列表，支持流式输出"""
        # 创建消息框架
        message_frame = ctk.CTkFrame(
            self.messages_frame,
            fg_color=("#e6f4ff" if is_user else "#f5f5f5", "#1a1a1a" if is_user else "#262626"),
            corner_radius=15
        )
        
        # 设置消息框架的布局
        if is_user:
            message_frame.pack(fill="x", padx=(100, 20), pady=5, anchor="e")
        else:
            message_frame.pack(fill="x", padx=(20, 100), pady=5, anchor="w")
        
        # 头部信息框架
        header_frame = ctk.CTkFrame(
            message_frame,
            fg_color="transparent"
        )
        header_frame.pack(fill="x", padx=15, pady=(5, 0))
        
        # 添加头像和时间，根据是否为用户消息调整布局
        if is_user:
            time_label = ctk.CTkLabel(
                header_frame,
                text=datetime.now().strftime("%H:%M"),
                font=("SF Pro Display", 10),
                text_color=("gray40", "gray60")
            )
            time_label.pack(side="left", padx=5)
            
            avatar_label = ctk.CTkLabel(
                header_frame,
                text="👤",
                font=("Segoe UI Emoji", 24),  # 调整用户头像emoji的大小
                width=32,  # 固定宽度
                height=32  # 固定高度
            )
            avatar_label.pack(side="right", padx=5)
        else:
            avatar_label = ctk.CTkLabel(
                header_frame,
                text=self.emotion_icons[self.current_emotion],
                font=("Segoe UI Emoji", 24),  # 调整AI头像emoji的大小
                width=32,  # 固定宽度
                height=32  # 固定高度
            )
            avatar_label.pack(side="left", padx=5)
            # 保存最后一条AI消息的头像标签引用
            self.last_ai_avatar_label = avatar_label
            
            time_label = ctk.CTkLabel(
                header_frame,
                text=datetime.now().strftime("%H:%M"),
                font=("SF Pro Display", 10),
                text_color=("gray40", "gray60")
            )
            time_label.pack(side="right", padx=5)
        
        # 消息内容
        message_label = ctk.CTkLabel(
            message_frame,
            text="",  # 初始为空
            font=("SF Pro Display", 14),  # 调整消息文本大小
            text_color=("gray10", "gray90"),
            wraplength=350,
            justify="left" if not is_user else "right"
        )
        message_label.pack(fill="x", padx=15, pady=(5, 10))
        
        self.messages.append(message_frame)
        self.messages_frame._parent_canvas.yview_moveto(1.0)
        
        # 流式输出文本
        self.stream_text(message_label, text)

    def clear_messages(self):
        """清除所有消息"""
        for message in self.messages:
            message.destroy()
        self.messages = []

    def show_settings(self):
        """显示设置对话框"""
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("400x500")
        settings_window.configure(fg_color=("gray95", "gray10"))
        
        # 创建设置容器
        settings_frame = ctk.CTkFrame(
            settings_window,
            corner_radius=15,
            fg_color=("gray90", "gray15")
        )
        settings_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title = ctk.CTkLabel(
            settings_frame,
            text="设置",
            font=("SF Pro Display", 20, "bold")
        )
        title.pack(pady=20)
        
        # 设备ID设置
        device_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        device_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            device_frame,
            text="设备ID",
            font=("SF Pro Display", 14)
        ).pack(anchor="w")
        
        device_id_entry = ctk.CTkEntry(
            device_frame,
            font=("SF Pro Display", 13),
            height=35,
            corner_radius=8
        )
        device_id_entry.insert(0, src.config.DEVICE_ID)
        device_id_entry.pack(fill="x", pady=5)
        
        # 服务器设置
        server_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        server_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            server_frame,
            text="服务器地址",
            font=("SF Pro Display", 14)
        ).pack(anchor="w")
        
        server_entry = ctk.CTkEntry(
            server_frame,
            font=("SF Pro Display", 13),
            height=35,
            corner_radius=8
        )
        server_entry.insert(0, src.config.MQTT_BROKER)
        server_entry.pack(fill="x", pady=5)

    def on_button_press(self, event):
        """按钮按下事件处理"""
        self.recording = True
        self.talk_button.configure(
            fg_color=("#ff4d4f", "#ff4d4f"),
            text="正在录音...",
            hover_color=("#ff7875", "#ff7875")
        )
        
        if not self.mqtt_client.conn_state or not self.mqtt_client.session_id:
            if src.config.udp_socket:
                src.config.udp_socket.close()
                src.config.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                
            hello_msg = {
                "type": "hello",
                "version": 3,
                "transport": "udp",
                "audio_params": {
                    "format": "opus",
                    "sample_rate": 16000,
                    "channels": 1,
                    "frame_duration": 60
                }
            }
            self.mqtt_client.publish(hello_msg)
            
        if self.mqtt_client.tts_state in ["start", "sentence_start"]:
            self.mqtt_client.publish({"type": "abort"})
            
        session_id = self.mqtt_client.get_session_id()
        if session_id:
            listen_msg = {
                "session_id": session_id,
                "type": "listen",
                "state": "start",
                "mode": "manual"
            }
            self.mqtt_client.publish(listen_msg)

    def on_button_release(self, event):
        """按钮释放事件处理"""
        self.recording = False
        self.talk_button.configure(
            fg_color=("#1677ff", "#1677ff"),
            text="按住说话",
            hover_color=("#1668dc", "#1668dc")
        )
        
        session_id = self.mqtt_client.get_session_id()
        if session_id:
            stop_msg = {
                "session_id": session_id,
                "type": "listen",
                "state": "stop"
            }
            self.mqtt_client.publish(stop_msg)

    def update_status(self):
        """更新状态显示"""
        status = "已连接" if self.mqtt_client.conn_state else "未连接"
        recording_status = " | 录音中" if self.recording else ""
        
        # 更新状态图标
        self.status_icon.configure(
            text="🟢" if self.mqtt_client.conn_state else "🔴"
        )
        
        # 更新状态文本
        self.status_label.configure(
            text=f"状态: {status}{recording_status} | TTS: {self.mqtt_client.tts_state}"
        )
        
        self.root.after(1000, self.update_status)

    def on_close(self):
        """关闭窗口时退出"""
        if hasattr(self, 'volume_executor'):
            self.volume_executor.shutdown(wait=False)
        self.root.destroy()

    def handle_volume_change(self, volume: int):
        """处理音量变化"""
        if volume == self.last_volume:
            return
            
        self.last_volume = volume
        
        if self.volume_timer:
            self.root.after_cancel(self.volume_timer)
            
        self.volume_timer = self.root.after(
            self.volume_debounce_time, 
            lambda: self.volume_executor.submit(self.update_volume, volume)
        )

    def update_volume(self, volume: int):
        """更新系统音量"""
        system = platform.system()
        
        try:
            if system == "Windows":
                try:
                    # 方案1：使用pycaw
                    try:
                        from ctypes import cast, POINTER
                        from comtypes import CLSCTX_ALL
                        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                        
                        devices = AudioUtilities.GetSpeakers()
                        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                        volume_control = cast(interface, POINTER(IAudioEndpointVolume))
                        volume_db = -65.25 * (1 - volume/100.0)
                        volume_control.SetMasterVolumeLevel(volume_db, None)
                        print(f"音量设置为: {volume}%")
                        return
                    except:
                        pass

                    # 方案2：使用PowerShell
                    try:
                        cmd = f'powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"'
                        for _ in range(50):  # 先将音量调到最小
                            subprocess.run(cmd.replace('175', '174'), shell=True)
                        
                        steps = int(volume / 2)  # 每次增加2%
                        for _ in range(steps):  # 然后调整到目标音量
                            subprocess.run(cmd, shell=True)
                        print(f"音量设置为: {volume}% (使用PowerShell)")
                        return
                    except:
                        pass

                    # 方案3：使用nircmd（如果已安装）
                    try:
                        subprocess.run(['nircmd.exe', 'setsysvolume', str(int(65535 * volume / 100))])
                        print(f"音量设置为: {volume}% (使用nircmd)")
                        return
                    except:
                        pass

                except Exception as e:
                    print(f"设置音量失败: {e}")
            
            elif system == "Darwin":  # macOS
                subprocess.run(
                    ["osascript", "-e", f"set volume output volume {volume}"], 
                    capture_output=True
                )
            
            else:
                print(f"不支持在 {system} 平台上设置音量")

        except Exception as e:
            print(f"设置音量失败: {e}")

    def show_verification_code(self):
        """显示验证码对话框"""
        if hasattr(src.config, 'VERIFICATION_CODE'):
            # 创建验证码窗口
            verification_window = ctk.CTkToplevel(self.root)
            verification_window.title("验证码")
            verification_window.geometry("300x200")
            verification_window.configure(fg_color=("gray95", "gray10"))
            
            # 确保验证码窗口显示在主窗口之上
            verification_window.transient(self.root)
            verification_window.grab_set()
            
            # 创建内容框架
            content_frame = ctk.CTkFrame(
                verification_window,
                corner_radius=15,
                fg_color=("gray90", "gray15")
            )
            content_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # 标题
            title_label = ctk.CTkLabel(
                content_frame,
                text="请记录您的验证码",
                font=("SF Pro Display", 16, "bold")
            )
            title_label.pack(pady=(20, 10))
            
            # 验证码显示
            code_label = ctk.CTkLabel(
                content_frame,
                text=str(src.config.VERIFICATION_CODE),
                font=("SF Pro Display", 32, "bold"),
                text_color=("blue", "#00aaff")
            )
            code_label.pack(pady=10)
            
            # 说明文本
            info_label = ctk.CTkLabel(
                content_frame,
                text="首次使用需要输入此验证码\n请妥善保管",
                font=("SF Pro Display", 12),
                text_color=("gray40", "gray60")
            )
            info_label.pack(pady=10)
            
            # 确认按钮
            confirm_button = ctk.CTkButton(
                content_frame,
                text="我已记录",
                font=("SF Pro Display", 14),
                height=35,
                corner_radius=8,
                command=verification_window.destroy
            )
            confirm_button.pack(pady=15)
            
            # 窗口居中显示
            verification_window.update()
            window_width = verification_window.winfo_width()
            window_height = verification_window.winfo_height()
            screen_width = verification_window.winfo_screenwidth()
            screen_height = verification_window.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            verification_window.geometry(f"+{x}+{y}")
            
            # 等待窗口关闭
            self.root.wait_window(verification_window)

    def toggle_theme(self):
        """切换主题模式"""
        if self.current_theme == "light":
            self.current_theme = "dark"
            ctk.set_appearance_mode("dark")
            self.theme_button.configure(text="☀️ 日间模式")
        else:
            self.current_theme = "light"
            ctk.set_appearance_mode("light")
            self.theme_button.configure(text="🌙 夜间模式")

    def update_emotion(self, emotion):
        """更新情感状态显示"""
        if emotion in self.emotion_icons:
            self.current_emotion = emotion
            # 更新状态栏的情感图标
            if hasattr(self, 'emotion_label'):
                self.emotion_label.configure(text=self.emotion_icons[emotion])
