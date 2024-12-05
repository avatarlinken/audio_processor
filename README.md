# SMPTE时间码音频处理器

这是一个专业的音频处理工具，可以：
1. 使用专业的下混合算法（ITU-R BS.775-3标准）将多声道音频合并到左声道
2. 在右声道生成标准的SMPTE LTC（Linear Time Code）时间码

## 功能特点

### 音频处理
- 支持MP3和WAV格式音频文件
- 支持单声道、双声道及多声道输入
- 使用ITU-R BS.775-3标准的下混合算法
- 输出为标准WAV格式

### SMPTE时间码
- 支持多种帧率：
  * 24fps（电影标准）
  * 25fps（PAL制式）
  * 29.97fps（NTSC制式）
  * 30fps
  * 50fps
  * 59.94fps
  * 60fps
- 支持丢帧时间码（Drop Frame，用于29.97和59.94fps）
- 多种信号类型：
  * 正弦波（Sine）
  * 方波（Square）
  * 调制波（Modulated）
- 可调节时间码音量（0-100%）
- 支持多种位深度：16/24/32位

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 运行程序：
```bash
python audio_processor.py
```

2. 设置SMPTE参数：
   - 选择合适的帧率
   - 根据需要启用丢帧功能（29.97/59.94fps时可用）
   - 选择信号类型
   - 调整时间码音量

3. 处理音频：
   - 点击"选择音频文件"按钮
   - 选择要处理的音频文件
   - 点击"开始转换"
   - 等待处理完成

处理后的文件将自动保存在原文件所在目录，文件名添加"_processed"后缀。

## 技术说明

### 声道合并算法
使用ITU-R BS.775-3标准的下混合算法：
- L = L + 0.707*R（约-3dB衰减）
- 自动防止信号削波
- 保持最佳声音定位感

### SMPTE时间码
- 使用标准的80位二进制帧格式
- 包含完整的时、分、秒、帧信息
- 支持用户位和标志位
- 使用曼彻斯特编码确保同步

## 注意事项

- 建议使用44.1kHz或48kHz的音频文件
- 确保有足够的磁盘空间（输出文件可能大于输入文件）
- 处理大文件时可能需要等待较长时间
- 某些参数组合（如高帧率+高采样率）可能需要更多处理时间

## 错误处理

程序会在以下情况显示错误信息：
- 文件格式不支持
- 磁盘空间不足
- 文件访问权限问题
- 处理过程中的其他错误

如果遇到问题，请查看状态栏的错误信息或联系开发者。