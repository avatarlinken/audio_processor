import os
import numpy as np
from pydub import AudioSegment
import soundfile as sf
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time

class AudioProcessor:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("音频处理器")
        self.window.geometry("500x400")
        
        # SMPTE参数设置
        self.fps = tk.StringVar(value="30")
        self.drop_frame = tk.BooleanVar(value=False)
        self.bit_depth = tk.StringVar(value="16")
        self.signal_type = tk.StringVar(value="sine")
        self.volume = tk.DoubleVar(value=0.5)
        
        # 添加采样率变量
        self.sample_rate = 44100  # 默认采样率
        self.input_file_path = None
        
        self.setup_ui()

    def setup_ui(self):
        # 创建参数设置框架
        settings_frame = ttk.LabelFrame(self.window, text="SMPTE参数设置", padding="10")
        settings_frame.pack(fill="x", padx=10, pady=5)

        # 帧率选择
        ttk.Label(settings_frame, text="帧率:").grid(row=0, column=0, sticky="w", padx=5)
        fps_combo = ttk.Combobox(settings_frame, textvariable=self.fps, width=10)
        fps_combo['values'] = ("24", "25", "29.97", "30", "50", "59.94", "60")
        fps_combo.grid(row=0, column=1, sticky="w", padx=5)

        # 丢帧设置
        ttk.Checkbutton(settings_frame, text="丢帧", variable=self.drop_frame).grid(
            row=0, column=2, sticky="w", padx=20)

        # 位深度选择
        ttk.Label(settings_frame, text="位深度:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        bit_depth_combo = ttk.Combobox(settings_frame, textvariable=self.bit_depth, width=10)
        bit_depth_combo['values'] = ("16", "24", "32")
        bit_depth_combo.grid(row=1, column=1, sticky="w", padx=5)

        # 信号类型选择
        ttk.Label(settings_frame, text="信号类型:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        signal_type_combo = ttk.Combobox(settings_frame, textvariable=self.signal_type, width=10)
        signal_type_combo['values'] = ("sine", "square", "modulated")
        signal_type_combo.grid(row=2, column=1, sticky="w", padx=5)

        # 音量控制
        ttk.Label(settings_frame, text="时间码音量:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        volume_scale = ttk.Scale(settings_frame, from_=0.0, to=1.0, variable=self.volume, 
                               orient="horizontal", length=200)
        volume_scale.grid(row=3, column=1, columnspan=2, sticky="w", padx=5)

        # 创建文件选择框架
        file_frame = ttk.LabelFrame(self.window, text="文件选择", padding="10")
        file_frame.pack(fill="x", padx=10, pady=5)

        # 文件路径显示
        self.file_path_var = tk.StringVar(value="未选择文件")
        file_path_label = ttk.Label(file_frame, textvariable=self.file_path_var, wraplength=400)
        file_path_label.pack(fill="x", padx=5, pady=5)

        # 创建按钮框架
        button_frame = ttk.Frame(file_frame)
        button_frame.pack(fill="x", padx=5, pady=5)

        # 选择文件按钮
        select_button = ttk.Button(button_frame, text="选择音频文件", command=self.select_file)
        select_button.pack(side="left", padx=5)

        # 重置参数按钮
        reset_button = ttk.Button(button_frame, text="重置参数", command=self.reset_parameters)
        reset_button.pack(side="left", padx=5)

        # 转换按钮
        self.convert_button = ttk.Button(button_frame, text="开始转换", command=self.start_conversion, state="disabled")
        self.convert_button.pack(side="left", padx=5)

        # 创建进度框架
        progress_frame = ttk.LabelFrame(self.window, text="转换进度", padding="10")
        progress_frame.pack(fill="x", padx=10, pady=5)

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, length=300, mode='determinate', 
                                          variable=self.progress_var)
        self.progress_bar.pack(fill="x", padx=5, pady=5)

        # 状态指示区域（状态灯和文字）
        status_frame = ttk.Frame(progress_frame)
        status_frame.pack(fill="x", padx=5)
        
        # 状态灯（使用Canvas绘制）
        self.status_light = tk.Canvas(status_frame, width=20, height=20, highlightthickness=0)
        self.status_light.pack(side="left", padx=(0, 5))
        self.status_light_id = self.status_light.create_oval(5, 5, 15, 15, fill="green")
        
        # 状态标签
        self.status_label = ttk.Label(status_frame, text="就绪", wraplength=400)
        self.status_label.pack(side="left", fill="x", pady=5)

    def reset_parameters(self):
        """重置所有参数到默认值"""
        self.fps.set("30")
        self.drop_frame.set(False)
        self.bit_depth.set("16")
        self.signal_type.set("sine")
        self.volume.set(0.5)

    def generate_smpte_timecode(self, duration_ms):
        """生成SMPTE LTC时间码音频"""
        # 使用输入文件的采样率
        sample_rate = self.sample_rate
        
        # 获取用户设置的参数
        fps = float(self.fps.get())
        is_drop_frame = self.drop_frame.get()
        signal_type = self.signal_type.get()
        volume = self.volume.get()
        
        duration_s = duration_ms / 1000.0
        total_frames = int(duration_s * fps)
        
        # 确保采样点数是整数
        total_samples = int(sample_rate * duration_s)
        samples_per_frame = int(total_samples / total_frames)
        
        # 创建输出数组
        output = np.zeros(total_samples)
        
        for frame in range(total_frames):
            # 计算时间码值（考虑丢帧）
            if is_drop_frame and fps in [29.97, 59.94]:
                # 丢帧时间码计算
                total_minutes = frame // (int(fps) * 60)
                remaining_frames = frame % (int(fps) * 60)
                dropped_frames = 2 * total_minutes - (total_minutes // 10) * 2
                actual_frame = frame + dropped_frames
            else:
                actual_frame = frame

            # 生成这一帧的时间码
            hours = (actual_frame // (int(fps) * 60 * 60)) % 24
            minutes = (actual_frame // (int(fps) * 60)) % 60
            seconds = (actual_frame // int(fps)) % 60
            frames = actual_frame % int(fps)
            
            # 将时间信息转换为二进制
            timecode_bits = []
            # 帧数 (6位)
            timecode_bits.extend(format(int(frames), '06b'))
            # 秒数 (6位)
            timecode_bits.extend(format(seconds, '06b'))
            # 分钟 (6位)
            timecode_bits.extend(format(minutes, '06b'))
            # 小时 (5位)
            timecode_bits.extend(format(hours, '05b'))
            
            # 添加用户位和标志位
            user_bits = format(0, '032b')  # 32位用户数据
            timecode_bits.extend(user_bits)
            
            # 添加同步字 (16位)
            sync_word = '0011111111111101'
            timecode_bits.extend(sync_word)
            
            # 曼彻斯特编码
            manchester = []
            for bit in timecode_bits:
                if bit == '1':
                    manchester.extend([1, -1])  # 1 -> 高到低
                else:
                    manchester.extend([-1, 1])  # 0 -> 低到高
            
            # 计算每个比特的采样点数，确保整除
            total_bits = len(manchester)
            samples_per_bit = samples_per_frame // total_bits
            if samples_per_bit < 1:
                samples_per_bit = 1
            
            # 根据选择的信号类型生成波形
            if signal_type == 'square':
                frame_signal = np.repeat(manchester, samples_per_bit)
            elif signal_type == 'modulated':
                # 使用固定长度的时间数组
                t = np.linspace(0, duration_s/total_frames, samples_per_frame)
                carrier = np.sin(2 * np.pi * 1000 * t)
                frame_signal = np.repeat(manchester, samples_per_bit) * carrier[:len(manchester) * samples_per_bit]
            else:  # sine
                t = np.linspace(0, duration_s/total_frames, samples_per_frame)
                sine_wave = np.sin(2 * np.pi * 1000 * t)
                frame_signal = np.repeat(manchester, samples_per_bit) * sine_wave[:len(manchester) * samples_per_bit]
            
            # 确保帧信号长度正确
            if len(frame_signal) > samples_per_frame:
                frame_signal = frame_signal[:samples_per_frame]
            elif len(frame_signal) < samples_per_frame:
                padding = samples_per_frame - len(frame_signal)
                frame_signal = np.pad(frame_signal, (0, padding), mode='constant')
            
            # 将波形写入输出数组
            start_idx = frame * samples_per_frame
            end_idx = start_idx + samples_per_frame
            if end_idx > len(output):
                # 如果超出范围，只写入剩余部分
                end_idx = len(output)
                frame_signal = frame_signal[:end_idx - start_idx]
            
            output[start_idx:end_idx] = frame_signal
        
        # 标准化信号幅度并应用音量设置
        if np.max(np.abs(output)) > 0:
            output = output / np.max(np.abs(output)) * volume
        
        return output

    def merge_channels(self, left, right):
        """专业立体声降混算法 (ITU-R BS.775标准)
        
        使用ITU-R BS.775标准的系数进行立体声到单声道的转换，
        保持浮点数精度以确保波形连续性。
        """
        # 转换为64位浮点数以保持最高精度
        left = np.asarray(left, dtype=np.float64)
        right = np.asarray(right, dtype=np.float64)
        
        # 将输入数据归一化到 [-1, 1] 范围
        max_abs_left = np.max(np.abs(left))
        max_abs_right = np.max(np.abs(right))
        max_abs = max(max_abs_left, max_abs_right)
        if max_abs > 0:
            left = left / max_abs
            right = right / max_abs
        
        # ITU-R BS.775标准系数 (1/√2 ≈ 0.7071067811865476)
        ITU_COEF = 0.7071067811865476
        
        # 应用ITU-R BS.775标准的降混公式
        merged = ITU_COEF * (left + right)
        
        # 确保没有值超出范围
        merged = np.clip(merged, -1.0, 1.0)
        
        # 转换回32位浮点数，保持精度
        merged = merged.astype(np.float32)
        
        # 创建双声道输出
        stereo_output = np.zeros((len(merged), 2), dtype=np.float32)
        stereo_output[:, 0] = merged  # 左声道放混合信号
        # 右声道保持为0
            
        return stereo_output

    def select_file(self):
        """选择音频文件"""
        file_path = filedialog.askopenfilename(
            filetypes=[("音频文件", "*.wav *.mp3 *.aac *.ogg *.flac")]
        )
        if file_path:
            self.input_file_path = file_path
            self.file_path_var.set(file_path)
            self.convert_button.configure(state="normal")
            
            # 读取输入文件的采样率
            try:
                audio_data, sample_rate = sf.read(file_path)
                self.sample_rate = sample_rate
                self.status_label.config(text=f"已加载文件，采样率: {sample_rate} Hz")
            except Exception as e:
                messagebox.showerror("错误", f"读取文件失败: {str(e)}")
                return

    def update_progress(self, value, status_text):
        """更新进度条和状态文本"""
        self.progress_var.set(value)
        self.status_label.configure(text=status_text)
        self.window.update_idletasks()

    def update_status(self, status_text, status_type="ready"):
        """更新状态标签的文本和状态灯颜色
        
        Args:
            status_text: 状态文本
            status_type: 状态类型，可选值：ready（就绪）, processing（处理中）, error（错误）
        """
        self.status_label.config(text=status_text)
        
        # 更新状态灯颜色
        color_map = {
            "ready": "green",
            "processing": "yellow",
            "error": "red"
        }
        self.status_light.itemconfig(self.status_light_id, fill=color_map.get(status_type, "gray"))

    def open_file_location(self, file_path):
        """打开文件所在文件夹并高亮显示文件"""
        # 使用 Windows explorer 打开文件夹并选中文件
        import subprocess
        subprocess.run(['explorer', '/select,', os.path.normpath(file_path)])

    def start_conversion(self):
        """开始转换过程"""
        try:
            file_path = self.file_path_var.get()
            if file_path == "未选择文件":
                messagebox.showerror("错误", "请先选择音频文件")
                return

            # 禁用转换按钮
            self.convert_button.configure(state="disabled")
            
            # 更新状态
            self.update_progress(10, "正在加载音频文件...")
            self.update_status("正在加载音频文件...", "processing")
            # 加载音频文件
            audio = AudioSegment.from_file(file_path)
            
            # 更新状态
            self.update_progress(30, "正在处理音频通道...")
            self.update_status("正在处理音频通道...", "processing")
            # 获取音频样本
            samples = np.array(audio.get_array_of_samples())
            
            # 处理不同声道数的情况
            if audio.channels == 1:
                left_channel = samples
            else:
                # 将立体声拆分成左右声道
                samples = samples.reshape((-1, audio.channels))
                left_channel = samples[:, 0]
                if audio.channels > 1:
                    right_channel = samples[:, 1]
                    # 使用自然混音算法
                    mixed_channels = self.merge_channels(left_channel, right_channel)
                    left_channel = mixed_channels[:, 0]  # 获取混音后的左声道
                    
                    # # 保存混音文件
                    # mixed_timestamp = time.strftime("%Y%m%d_%H%M%S")
                    # mixed_output_path = os.path.splitext(file_path)[0] + f"_mixed_{mixed_timestamp}.wav"
                    # # 保存为双声道文件，右声道为空
                    # sf.write(mixed_output_path, mixed_channels, audio.frame_rate)
                    # self.status_label.config(text=f"已保存混音文件: {os.path.basename(mixed_output_path)}")

            self.update_progress(50, "正在生成SMPTE时间码...")
            self.update_status("正在生成SMPTE时间码...", "processing")
            
            # 生成SMPTE时间码
            smpte_signal = self.generate_smpte_timecode(len(audio))
            
            self.update_progress(70, "正在合并音频通道...")
            self.update_status("正在合并音频通道...", "processing")
            
            # 确保时间码信号长度与音频信号匹配
            if len(smpte_signal) > len(left_channel):
                smpte_signal = smpte_signal[:len(left_channel)]
            elif len(smpte_signal) < len(left_channel):
                smpte_signal = np.pad(smpte_signal, (0, len(left_channel) - len(smpte_signal)))
            
            # 创建新的双声道音频数组
            new_samples = np.column_stack((left_channel, smpte_signal * 32767))

            self.update_progress(90, "正在保存文件...")
            self.update_status("正在保存文件...", "processing")
            
            # 生成带时间戳的文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = os.path.splitext(file_path)[0] + f"_processed_{timestamp}.wav"
            
            # 保存处理后的文件
            sf.write(output_path, new_samples, audio.frame_rate)

            self.update_progress(100, "转换完成！")
            self.update_status("转换完成！", "ready")
            
            # 显示成功消息并询问是否打开文件位置
            result = messagebox.askquestion("成功", 
                f"处理完成！\n文件已保存至：\n{output_path}\n\n是否打开文件所在位置？")
            
            # 如果用户点击"是"，则打开文件位置
            if result == 'yes':
                self.open_file_location(output_path)
            
            # 重置进度条和状态
            self.progress_var.set(0)
            self.convert_button.configure(state="normal")

        except Exception as e:
            self.progress_var.set(0)
            self.update_status("转换失败", "error")
            self.convert_button.configure(state="normal")
            messagebox.showerror("错误", f"处理过程中出现错误：{str(e)}")

    def process_audio(self):
        """已废弃，使用 start_conversion 替代"""
        self.start_conversion()

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = AudioProcessor()
    app.run()
