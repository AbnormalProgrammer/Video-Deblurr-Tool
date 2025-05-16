# 视频增强工具使用说明

## 环境要求
- Python 版本：3.8.10

## 虚拟环境配置
1. 创建虚拟环境（若未创建）：`python -m venv venv`
2. 激活虚拟环境（Windows）：`venv\Scripts\activate`
   激活虚拟环境（MacOS）：`source venv/bin/activate`
3. 退出虚拟环境（Windows）：`venv\Scripts\deactivate`
   退出虚拟环境（MacOS）：`deactivate`

## 依赖安装
使用Python 3.8.10安装项目依赖：
pip install -r requirements.txt

### 依赖列表（requirements.txt内容）
opencv-python==4.5.1  # 用于视频帧的读取、处理与输出
numpy==1.21.0  # 处理视频帧的数值计算与矩阵操作
ffmpeg-python==0.2.0  # 视频文件的编解码与格式转换
rich==10.0.0  # 终端输出美化，显示进度和日志信息
torch==1.8.0  # 深度学习框架，用于ESRGAN模型的推理计算
basicsr==1.4.2  # 基础超分辨率工具库，提供模型和算法支持
realesrgan==0.3.0  # 实际超分辨率模型实现，负责视频模糊变高清处理

## 使用步骤
1. 激活虚拟环境（见上文）
2. 安装依赖（见上文）
3. 运行增强脚本：
python video_enhancer.py -i 输入视频路径 -o 输出视频路径

示例（Windows）：
python video_enhancer.py -i C:\Users\Stroman\Downloads\original.mp4 -o C:\Users\Stroman\Downloads\result.mp4
示例（MacOS）：
python video_enhancer.py -i /Users/Stroman/Downloads/original.mp4 -o /Users/Stroman/Downloads/result.mp4
示例（缺省参数）：
python video_enhancer.py  # 使用默认输入路径：C:\Users\Stroman\Downloads\original.mp4，默认输出路径：C:\Users\Stroman\Downloads\result.mp4（Windows）
python video_enhancer.py  # 使用默认输入路径：/Users/Stroman/Downloads/original.mp4，默认输出路径：/Users/Stroman/Downloads/result.mp4（MacOS）

## 图形化界面使用说明
### 启动方法
运行以下命令启动图形化界面：
python video_enhancer_gui.py

### 界面组件说明
- 输入视频路径：显示或手动输入待增强的视频文件路径，支持点击「选择文件」按钮浏览选择。
- 输出视频路径：显示或手动输入增强后视频的保存路径，支持点击「选择路径」按钮浏览选择输出目录（文件名自动与输入文件保持一致）。
- 处理进度条：显示当前视频增强的处理进度百分比（0%-100%）。
- 开始增强按钮：点击后启动视频增强处理流程（处理过程中界面不会卡顿）。
- 终止处理按钮：处理过程中启用，点击后可终止当前处理（系统将在当前帧处理完成后停止）。

### 操作步骤示例
1. 选择输入文件：点击「选择文件」按钮，在弹出的对话框中选择需要增强的视频文件（支持MP4/AVI/MOV格式）。
2. 设置输出路径：点击「选择路径」按钮，在弹出的对话框中选择增强后视频的保存目录（输出文件名会自动与输入文件同名）。
3. 启动处理：确认路径无误后，点击「开始增强」按钮，系统将自动完成视频增强并通过消息框提示结果。
4. 终止处理（可选）：若需中途停止，点击「终止处理」按钮，系统将在当前帧处理完成后停止并释放资源。

## 注意事项
- 输入视频路径需为存在的文件
- 输出路径需有写入权限
- 首次运行会自动下载ESRGAN模型（约100MB），下载URL：https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
- 处理过程中进度条会显示预估剩余时间（基于当前平均处理速度计算，公式：剩余帧数 / 平均处理速度）
- 使用CPU运行时，由于深度学习模型计算量较大，视频处理可能消耗大量时间。若有NVIDIA GPU（支持CUDA），建议配置GPU环境以加速处理。
- 若需强制终止处理，可按下键盘的Ctrl+C组合键。程序会在当前帧处理完成后停止，并自动释放视频资源（如关闭输入输出流），确保系统资源正常回收。