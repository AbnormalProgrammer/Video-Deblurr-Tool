import cv2
import numpy as np
import ffmpeg
import logging
import os
import sys
import concurrent.futures
import time
import json
from queue import Queue
from collections import deque
from threading import Lock, Thread
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
import torch
import signal
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

def enhanceVideo(inputPath, outputPath, on_progress=None, should_stop=None):
    """
    视频增强主函数
    :param inputPath: 输入视频文件路径（字符串类型）
    :param outputPath: 输出视频文件路径（字符串类型）
    :param on_progress: 进度回调函数（可选），格式：on_progress(processed_frames, total_frames)
    :param should_stop: 终止标志检查函数（可选），调用返回True时终止处理，格式：should_stop() -> bool
    :return: 布尔值，表示处理是否成功（True为成功，False为失败）
    """
    # 全局终止标志
    global shouldStop
    shouldStop = False

    def handleSigint(signum, frame):
        """
        信号处理函数：捕获Ctrl+C终止信号
        :param signum: 信号编号
        :param frame: 栈帧对象
        """
        global shouldStop
        logging.info("检测到Ctrl+C终止信号，将在当前帧处理完成后停止...")
        shouldStop = True

    # 注意：信号注册已移至GUI主线程，此处不再重复注册
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # 创建rich进度条（增强显示）
    progress = Progress(
        TextColumn("[bold green][progress.description]{task.description}"),
        BarColumn(bar_width=60, style="blue", complete_style="red"),  # 总进度（未完成）蓝色，当前处理进度（已完成）红色
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("[cyan]{task.completed}/{task.total}帧"),
        TimeRemainingColumn(),
        TextColumn("[yellow]{task.fields[speed]:.2f}帧/秒"),
        TextColumn("[magenta]{task.fields[eta]:.2f}秒剩余")  # 新增预估剩余时间显示
    )
    
    # 检查输入文件是否存在
    if not os.path.exists(inputPath):
        logging.error(f"输入视频文件 {inputPath} 不存在")
        return False
    
    try:
        # 读取视频
        cap = cv2.VideoCapture(inputPath)
    
        # 获取视频参数
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        totalFrames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        processedFrames = 0
    
        # 创建VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(outputPath, fourcc, fps, (width, height))
        
        # 初始化最近处理时间队列（保存最近10帧的处理时间，用于计算平均速度）
        recent_durations = deque(maxlen=10)
        
        # 初始化ESRGAN模型
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        upsampler = RealESRGANer(
            scale=4,
            model_path='https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth',
            model=model,
            tile=0,
            tile_pad=10,
            pre_pad=0,
            half=False,
            device=torch.device('cpu')
        )
        
        with progress:
            task_id = progress.add_task("[green]处理视频...", total=totalFrames, speed=0, eta=0)
            
            # 创建线程池，复用线程以提高效率
            with concurrent.futures.ThreadPoolExecutor() as executor:
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                        
                    processedFrames += 1
                    start_time = time.time()  # 记录帧处理开始时间
                    
                    # 检查GUI传入的停止标志（主线程设置）
                    if should_stop is not None and should_stop():
                        logging.info("触发终止标志，停止处理并释放资源...")
                        break

                    # 提交帧处理任务到线程池
                    future = executor.submit(processFrame, frame, upsampler)
                    processed_frame = future.result()
                    
                    end_time = time.time()  # 记录帧处理结束时间
                    duration = end_time - start_time  # 计算当前帧处理耗时（秒）
                    recent_durations.append(duration)  # 将耗时加入队列
                    
                    # 计算平均处理速度（帧/秒）
                    if len(recent_durations) > 0:
                        avg_duration = sum(recent_durations) / len(recent_durations)
                        current_speed = 1 / avg_duration if avg_duration > 0 else 0
                        remaining_frames = totalFrames - processedFrames
                        eta = remaining_frames * avg_duration  # 预估剩余时间（秒）
                    else:
                        current_speed = 0
                        eta = 0
                    
                    # 更新进度条字段
                    progress.update(task_id, advance=1, fields={'speed': current_speed, 'eta': eta}, description="[green]处理视频...")
                    
                    # 触发进度回调（如果有）
                    if on_progress:
                        on_progress(processedFrames, totalFrames)
                    
                    # 写入处理后的帧
                    out.write(processed_frame)
    
        # 释放资源
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        logging.info(f"视频增强完成，输出文件: {outputPath}")
        return True
    
    except Exception as e:
        logging.error(f"视频处理过程中发生错误: {str(e)}")
        if 'cap' in locals():
            cap.release()
        if 'out' in locals():
            out.release()
        cv2.destroyAllWindows()
        return False

def saveProcessingState(stateFilePath, inputPath, outputPath, processedFrames, totalFrames):
    """
    保存当前处理状态到JSON文件
    :param stateFilePath: 状态文件路径（字符串类型）
    :param inputPath: 输入视频文件路径（字符串类型）
    :param outputPath: 输出视频文件路径（字符串类型）
    :param processedFrames: 已处理帧数（整数类型）
    :param totalFrames: 总帧数（整数类型）
    :return: 布尔值，表示保存是否成功（True为成功，False为失败）
    """
    try:
        state = {
            "inputPath": inputPath,
            "outputPath": outputPath,
            "processedFrames": processedFrames,
            "totalFrames": totalFrames
        }
        with open(stateFilePath, "w") as f:
            json.dump(state, f)
        return True
    except Exception as e:
        logging.error(f"保存状态文件失败: {str(e)}")
        return False

def loadProcessingState(stateFilePath):
    """
    从JSON文件加载处理状态
    :param stateFilePath: 状态文件路径（字符串类型）
    :return: 字典类型，包含输入路径、输出路径、已处理帧数、总帧数；若加载失败返回None
    """
    try:
        if os.path.exists(stateFilePath):
            with open(stateFilePath, "r") as f:
                state = json.load(f)
            return state
        else:
            return None
    except Exception as e:
        logging.error(f"加载状态文件失败: {str(e)}")
        return None

def processFrame(frame, upsampler):
    """
    使用ESRGAN模型处理单帧图像以提升清晰度
    :param frame: 待处理的单帧图像（numpy数组格式）
    :param upsampler: 预初始化的ESRGAN上采样器对象
    :return: 增强后的单帧图像（numpy数组格式）
    """
    # 转换颜色空间（OpenCV使用BGR，模型通常使用RGB）
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # 使用ESRGAN模型增强图像
    output, _ = upsampler.enhance(frame_rgb, outscale=4)
    # 转换回BGR颜色空间
    output_bgr = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
    return output_bgr

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='视频增强工具')
    parser.add_argument('-i', '--input', default='C:\\Users\\Stroman\\Downloads\\original.mp4', help='输入视频文件路径(默认: C:\\Users\\Stroman\\Downloads\\original.mp4')
    parser.add_argument('-o', '--output', default='C:\\Users\\Stroman\\Downloads\\result.mp4', help='输出视频文件路径(默认: C:\\Users\\Stroman\\Downloads\\result.mp4')
    args = parser.parse_args()
    
    if not enhanceVideo(args.input, args.output):
        sys.exit(1)