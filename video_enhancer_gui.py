import tkinter as tk
import signal
from tkinter import filedialog, ttk
import os
from video_enhancer import enhanceVideo

class VideoEnhancerGUI:
    def __init__(self, root):
        """
        初始化视频增强GUI界面
        :param root: Tkinter主窗口对象
        """
        self.root = root
        self.root.title("视频模糊变高清工具")
        self.root.geometry("600x300")

        # 输入路径变量
        self.inputPathVar = tk.StringVar(value=os.path.expanduser("~\\Downloads\\original.mp4"))
        # 输出路径变量
        self.outputPathVar = tk.StringVar(value=os.path.expanduser("~\\Downloads\\result.mp4"))
        # 处理进度变量
        self.progressVar = tk.DoubleVar(value=0)
        # 处理状态标志（True表示正在处理）
        self.isProcessing = False
        # 初始化停止标志（用于终止处理流程）
        self.should_stop = False

        # 定义SIGINT信号处理函数（主线程注册）
        def handle_sigint(signum, frame):
            self.should_stop = True
            tk.messagebox.showinfo('提示', '将在当前帧处理完成后停止...')
        # 主线程注册SIGINT信号处理（仅执行一次）
        if not hasattr(self, 'sigint_registered'):
            signal.signal(signal.SIGINT, handle_sigint)
            self.sigint_registered = True

        # 创建界面组件
        self.createWidgets()


    def createWidgets(self):
        """
        创建所有界面组件并布局
        """
        # 输入文件选择框
        ttk.Label(self.root, text="输入视频路径:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        self.inputEntry = ttk.Entry(self.root, textvariable=self.inputPathVar, width=50)
        self.inputEntry.grid(row=0, column=1, padx=10, pady=5)
        self.selectInputBtn = ttk.Button(self.root, text="选择文件", command=self.selectInputFile)
        self.selectInputBtn.grid(row=0, column=2, padx=10, pady=5)

        # 输出文件选择框
        ttk.Label(self.root, text="输出视频路径:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        self.outputEntry = ttk.Entry(self.root, textvariable=self.outputPathVar, width=50)
        self.outputEntry.grid(row=1, column=1, padx=10, pady=5)
        self.selectOutputBtn = ttk.Button(self.root, text="选择路径", command=self.selectOutputPath)
        self.selectOutputBtn.grid(row=1, column=2, padx=10, pady=5)

        # 进度条
        ttk.Label(self.root, text="处理进度:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        ttk.Progressbar(self.root, variable=self.progressVar, length=400).grid(row=2, column=1, columnspan=2, padx=10, pady=5)
        # 百分比显示标签
        self.percentLabel = ttk.Label(self.root, text="0%")
        self.percentLabel.grid(row=2, column=1, padx=(0,0), pady=5, sticky=tk.W)  # 减少左侧内边距至0使标签更左移

        # 开始处理按钮
        self.startBtn = ttk.Button(self.root, text="开始增强", command=self.startProcessing)
        self.startBtn.grid(row=3, column=1, padx=10, pady=20)

        # 终止处理按钮
        self.stopButton = ttk.Button(self.root, text="终止处理", command=self.stopProcessing, state=tk.DISABLED)
        self.stopButton.grid(row=4, column=1, padx=10, pady=5)

    def selectInputFile(self):
        """
        打开文件选择对话框选择输入视频文件
        """
        file_path = filedialog.askopenfilename(
            title="选择输入视频文件",
            filetypes=[("视频文件", "*.mp4;*.avi;*.mov"), ("所有文件", "*.*")]
        )
        if file_path:
            self.inputPathVar.set(file_path)

    def selectOutputPath(self):
        """
        打开目录选择对话框选择输出路径
        """
        dir_path = filedialog.askdirectory(title="选择输出目录")
        if dir_path:
            output_file = os.path.basename(self.inputPathVar.get())
            self.outputPathVar.set(os.path.join(dir_path, output_file))

    def startProcessing(self):
        """
        启动视频增强处理流程（使用线程避免界面卡顿）
        """
        input_path = self.inputPathVar.get()
        output_path = self.outputPathVar.get()

        if not os.path.exists(input_path):
            tk.messagebox.showerror("错误", "输入视频文件不存在！")
            return

        # 开始处理时禁用系统关闭按钮
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)  # 阻止关闭
        # 使用线程执行耗时操作
        from threading import Thread
        Thread(target=self.processVideo, args=(input_path, output_path), daemon=True).start()
        # 启用终止按钮
        self.stopButton.config(state=tk.NORMAL)

    def processVideo(self, input_path, output_path):
        """
        实际执行视频增强的方法（运行在子线程中）
        :param input_path: 输入视频路径
        :param output_path: 输出视频路径
        """
        self.isProcessing = True  # 标记处理开始
        # 定义进度回调函数
        def update_progress(processed, total):
            if not self.isProcessing:  # 检测到终止信号时停止更新
                return
            progress_percent = (processed / total) * 100 if total > 0 else 0
            self.progressVar.set(progress_percent)
            self.percentLabel.config(text=f"{progress_percent:.1f}%")  # 更新百分比显示
            self.root.update_idletasks()  # 强制更新界面

        # 调用增强函数并传入进度回调及停止标志
        result = enhanceVideo(input_path, output_path, on_progress=update_progress, should_stop=lambda: self.should_stop)
        self.isProcessing = False  # 标记处理结束
        # 处理完成后恢复系统关闭按钮
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)  # 恢复关闭功能
        """
        实际执行视频增强的方法（运行在子线程中）
        :param input_path: 输入视频路径
        :param output_path: 输出视频路径
        """
        # 这里需要实现进度更新逻辑（需要修改原enhanceVideo函数支持进度回调）
        # 定义进度回调函数
        def update_progress(processed, total):
            progress_percent = (processed / total) * 100 if total > 0 else 0
            self.progressVar.set(progress_percent)
            self.percentLabel.config(text=f"{progress_percent:.1f}%")  # 更新百分比显示
            self.root.update_idletasks()  # 强制更新界面

        # 调用增强函数并传入进度回调及停止标志
        result = enhanceVideo(input_path, output_path, on_progress=update_progress, should_stop=lambda: self.should_stop)
        if result:
            tk.messagebox.showinfo("完成", "视频增强成功！")
        else:
            tk.messagebox.showerror("失败", "视频增强过程中发生错误！")
        # 处理完成后自动退出程序
        self.root.destroy()

    def stopProcessing(self):
        """
        终止当前视频增强处理流程，并禁用所有界面组件
        """
        self.should_stop = True  # 设置停止标志触发终止
        self.isProcessing = False
        # 禁用所有界面组件
        self.inputEntry.config(state=tk.DISABLED)
        self.selectInputBtn.config(state=tk.DISABLED)
        self.outputEntry.config(state=tk.DISABLED)
        self.selectOutputBtn.config(state=tk.DISABLED)
        self.startBtn.config(state=tk.DISABLED)
        self.stopButton.config(state=tk.DISABLED)
        tk.messagebox.showinfo("提示", "处理将在当前帧完成后终止...")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoEnhancerGUI(root)
    root.mainloop()