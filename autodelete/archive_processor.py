#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
压缩包自动处理工具
功能：检测并修正异常格式的压缩包，自动解压并递归处理
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinterdnd2 as tkdnd
import os
import re
import subprocess
import json
import threading
from pathlib import Path
import shutil
import time
try:
    import win32api
    import win32con
    SYSTEM_POPUP_AVAILABLE = True
except ImportError:
    SYSTEM_POPUP_AVAILABLE = False

class ArchiveProcessor:
    def __init__(self):
        self.root = tkdnd.Tk()
        self.root.title("压缩包自动处理工具 v1.0")
        self.root.geometry("650x800")
        self.root.configure(bg='#ffffff')
        self.root.resizable(True, True)
        
        # 设置窗口图标（如果有的话）
        try:
            self.root.iconbitmap(default='icon.ico')
        except:
            pass
        
        # 配置文件路径
        self.config_file = "config.json"
        self.passwords = self.load_passwords()
        
        # 支持的压缩包格式
        self.archive_extensions = ['.7z', '.zip', '.rar', '.tar', '.gz', '.bz2', '.xz']
        
        # 处理状态
        self.is_processing = False
        self.stop_processing = False  # 手动停止标志
        
        # 密码选项控制
        self.has_password = tk.BooleanVar(value=False)  # 默认假设无密码
        self.use_bandizip_wait = tk.BooleanVar(value=True)  # 默认启用Bandizip等待
        
        # 日志历史记录（按解压操作分组，保存最近3次操作）
        self.log_history = []  # 当前操作的日志
        self.operation_logs = []  # 最近3次操作的完整日志
        self.current_operation_id = None
        
        self.setup_ui()
        self.setup_drag_drop()
        
        # Bandizip路径检查（在UI创建后）
        self.bandizip_path = self.find_bandizip()
        if not self.bandizip_path:
            self.show_bandizip_warning()
        
        # 启动时的欢迎信息
        self.log("欢迎使用压缩包自动处理工具！")
        self.log("请选择或拖放包含异常压缩包的文件夹")
        
    def setup_ui(self):
        """设置用户界面"""
        # 顶部标题栏 - GitHub风格的深色标题栏
        header_frame = tk.Frame(self.root, bg='#24292f', height=80)
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # 主标题
        title_label = tk.Label(
            header_frame, 
            text="📦 BUTTER UNPACKER", 
            font=('Segoe UI', 20, 'bold'),
            bg='#24292f',
            fg='#f0f6fc'
        )
        title_label.pack(pady=20)
        
        # 内容区域
        content_frame = tk.Frame(self.root, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=0, pady=0)
        
        # 副标题
        subtitle_label = tk.Label(
            content_frame,
            text="批量处理压缩包，支持递归解压和异常文件名修复",
            font=('Segoe UI', 11),
            bg='#ffffff',
            fg='#656d76'
        )
        subtitle_label.pack(pady=20)
        
        # 拖放区域 - GitHub风格的边框和阴影
        self.drop_frame = tk.Frame(
            content_frame, 
            bg='#f6f8fa', 
            relief='solid', 
            bd=1,
            height=160
        )
        self.drop_frame.pack(pady=20, padx=40, fill='x')
        self.drop_frame.pack_propagate(False)
        
        # 拖放图标和文字
        drop_icon_label = tk.Label(
            self.drop_frame,
            text="📁",
            font=('Segoe UI', 28),
            bg='#f6f8fa',
            fg='#0969da',
            cursor='hand2'
        )
        drop_icon_label.pack(pady=(25, 8))
        drop_icon_label.bind('<Button-1>', lambda e: self.select_folder())
        
        drop_label = tk.Label(
            self.drop_frame,
            text="拖放文件夹到此处\n或点击此处选择文件夹",
            font=('Segoe UI', 12),
            bg='#f6f8fa',
            fg='#656d76',
            justify='center',
            cursor='hand2'
        )
        drop_label.pack(expand=True)
        drop_label.bind('<Button-1>', lambda e: self.select_folder())
        
        # 选项区域
        option_frame = tk.Frame(content_frame, bg='#ffffff')
        option_frame.pack(pady=15)
        
        # 密码选项复选框
        self.password_checkbox = tk.Checkbutton(
            option_frame,
            text="🔒 目标文件有密码（选中时跳过无密码尝试）",
            variable=self.has_password,
            font=('Segoe UI', 10),
            bg='#ffffff',
            fg='#24292f',
            activebackground='#ffffff',
            selectcolor='#ffffff'
        )
        self.password_checkbox.pack(pady=3)
        
        # Bandizip等待选项复选框
        self.bandizip_wait_checkbox = tk.Checkbutton(
            option_frame,
            text="⏳ 启用Bandizip手动密码输入（不推荐开启）",
            variable=self.use_bandizip_wait,
            font=('Segoe UI', 10),
            bg='#ffffff',
            fg='#24292f',
            activebackground='#ffffff',
            selectcolor='#ffffff'
        )
        self.bandizip_wait_checkbox.pack(pady=3)
        
        # 按钮区域
        button_frame = tk.Frame(content_frame, bg='#ffffff')
        button_frame.pack(pady=20)
        
        # 选择文件夹按钮 - GitHub风格的绿色按钮
        self.select_btn = tk.Button(
            button_frame,
            text="📂 选择文件夹",
            font=('Segoe UI', 10),
            bg='#1f883d',
            fg='white',
            relief='solid',
            bd=1,
            padx=20,
            pady=8,
            command=self.select_folder,
            cursor='hand2',
            activebackground='#1a7f37',
            disabledforeground='white'
        )
        self.select_btn.pack(side='left', padx=6)
        
        # 密码管理按钮 - GitHub风格的蓝色按钮
        self.password_btn = tk.Button(
            button_frame,
            text="🔐 密码管理",
            font=('Segoe UI', 10),
            bg='#0969da',
            fg='white',
            relief='solid',
            bd=1,
            padx=20,
            pady=8,
            command=self.open_password_manager,
            cursor='hand2',
            activebackground='#0860ca',
            disabledforeground='white'
        )
        self.password_btn.pack(side='left', padx=6)
        
        # 主操作按钮（开始处理/停止处理） - GitHub风格的橙色按钮
        self.main_action_btn = tk.Button(
            button_frame,
            text="⚡ 开始处理",
            font=('Segoe UI', 10),
            bg='#fb8500',
            fg='white',
            relief='solid',
            bd=1,
            padx=20,
            pady=8,
            command=self.toggle_processing,
            state='disabled',
            cursor='hand2',
            activebackground='#e07600',
            disabledforeground='white'
        )
        self.main_action_btn.pack(side='left', padx=6)
        
        # 进度条
        self.progress = ttk.Progressbar(
            content_frame, 
            mode='indeterminate',
            length=400
        )
        self.progress.pack(pady=20)
        
        # 日志区域
        log_frame = tk.Frame(content_frame, bg='#ffffff')
        log_frame.pack(pady=15, padx=40, fill='both', expand=True)
        
        log_header = tk.Label(
            log_frame, 
            text="📋 处理日志", 
            font=('Segoe UI', 13),
            bg='#ffffff',
            fg='#24292f',
            relief='flat',
            bd=0
        )
        log_header.pack(anchor='w', pady=(0, 10))
        
        # 日志文本框容器
        log_container = tk.Frame(log_frame, bg='#ffffff')
        log_container.pack(fill='both', expand=True)
        
        # 日志文本框 - GitHub风格的代码区域
        self.log_text = tk.Text(
            log_container,
            height=8,
            font=('Courier New', 9),
            bg='#f6f8fa',
            fg='#24292f',
            relief='solid',
            bd=1,
            wrap='word',
            padx=12,
            pady=10
        )
        self.log_text.pack(side='left', fill='both', expand=True)
        
        # 滚动条
        scrollbar = tk.Scrollbar(log_container, command=self.log_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 当前选择的文件夹
        self.selected_folder = None
        
    def setup_drag_drop(self):
        """设置拖放功能"""
        self.drop_frame.drop_target_register(tkdnd.DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
        
    def on_drop(self, event):
        """处理拖放事件"""
        files = self.root.tk.splitlist(event.data)
        if files:
            folder_path = files[0]
            if os.path.isdir(folder_path):
                self.selected_folder = folder_path
                self.log(f"已选择文件夹: {folder_path}")
                self.main_action_btn.config(state='normal')
            else:
                messagebox.showwarning("警告", "请拖放文件夹，不是文件")
                
    def select_folder(self):
        """选择文件夹对话框"""
        folder_path = filedialog.askdirectory(title="选择要处理的文件夹")
        if folder_path:
            self.selected_folder = folder_path
            self.log(f"已选择文件夹: {folder_path}")
            self.main_action_btn.config(state='normal')
            
    def log(self, message, operation_type=None):
        """添加日志信息"""
        import datetime
        import uuid
        
        # 添加时间戳
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        # 处理操作分组
        if operation_type == 'start':
            # 开始新的解压操作
            if self.current_operation_id and self.log_history:
                # 保存上一个操作的日志
                self.operation_logs.append({
                    'id': self.current_operation_id,
                    'logs': self.log_history.copy()
                })
                # 保持最近3次操作
                if len(self.operation_logs) > 3:
                    self.operation_logs.pop(0)
            
            # 开始新操作
            self.current_operation_id = str(uuid.uuid4())[:8]
            self.log_history = []
        
        # 添加到当前操作日志
        self.log_history.append(log_entry)
        
        # 如果是操作结束，保存当前操作
        if operation_type == 'end' and self.current_operation_id:
            self.operation_logs.append({
                'id': self.current_operation_id,
                'logs': self.log_history.copy()
            })
            # 保持最近3次操作
            if len(self.operation_logs) > 3:
                self.operation_logs.pop(0)
            self.save_recent_logs()
        
        def update_log():
            self.log_text.insert(tk.END, f"{log_entry}\n")
            self.log_text.see(tk.END)
            self.root.update_idletasks()
        
        # 如果在主线程中，直接更新；否则使用after方法安全更新
        if threading.current_thread() == threading.main_thread():
            update_log()
        else:
            self.root.after(0, update_log)
    
    def save_recent_logs(self):
        """保存最近3次解压操作的完整日志到本地文件"""
        try:
            log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recent_logs.txt")
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write("最近3次解压操作的完整日志:\n")
                f.write("=" * 60 + "\n\n")
                
                if not self.operation_logs:
                    f.write("暂无解压操作记录\n")
                    return
                
                for i, operation in enumerate(reversed(self.operation_logs), 1):
                    f.write(f"操作 {i} (ID: {operation['id']}):\n")
                    f.write("-" * 40 + "\n")
                    for log_entry in operation['logs']:
                        f.write(log_entry + "\n")
                    f.write("\n")
        except Exception as e:
            # 避免日志保存错误影响主程序运行
            pass
        
    def load_passwords(self):
        """加载保存的密码"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('passwords', [])
        except Exception as e:
            self.log(f"加载配置文件失败: {e}")
        return []
        
    def save_passwords(self):
        """保存密码到配置文件"""
        try:
            config = {'passwords': self.passwords}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"保存配置文件失败: {e}")
            
    def find_bandizip(self):
        """查找Bandizip安装路径"""
        possible_paths = [
            r"C:\Program Files\WindowsApps\Bandisoft.com.15700C60EE320_7.40.22.0_x64__dytvnjx3s1h08\bin\Bandizip.exe",
            r"C:\Program Files\Bandizip\Bandizip.exe",
            r"C:\Program Files (x86)\Bandizip\Bandizip.exe",
            r"C:\Users\{}\AppData\Local\Bandizip\Bandizip.exe".format(os.getenv('USERNAME'))
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
                
        # 如果找不到，提示用户手动选择
        return None
    
    def show_bandizip_warning(self):
        """显示Bandizip未找到的警告"""
        result = messagebox.askyesno(
            "Bandizip未找到", 
            "未找到Bandizip安装路径。\n\n" +
            "本工具需要Bandizip来解压文件。\n" +
            "是否要手动选择Bandizip.exe的位置？",
            icon='warning'
        )
        
        if result:
            file_path = filedialog.askopenfilename(
                title="选择Bandizip.exe",
                filetypes=[("可执行文件", "*.exe")],
                initialdir="C:\\Program Files"
            )
            if file_path and os.path.exists(file_path):
                self.bandizip_path = file_path
                self.log(f"已设置Bandizip路径: {file_path}")
            else:
                self.log("警告: 未设置Bandizip路径，解压功能将不可用")
        else:
            self.log("警告: 未设置Bandizip路径，解压功能将不可用")
        
    def open_password_manager(self):
        """打开密码管理窗口"""
        password_window = tk.Toplevel(self.root)
        password_window.title("密码管理")
        password_window.geometry("400x300")
        password_window.configure(bg='#f0f0f0')
        
        # 密码列表
        tk.Label(
            password_window, 
            text="常用解压密码:", 
            font=('Microsoft YaHei', 12, 'bold'),
            bg='#f0f0f0'
        ).pack(pady=10)
        
        # 密码列表框
        list_frame = tk.Frame(password_window, bg='#f0f0f0')
        list_frame.pack(pady=10, padx=20, fill='both', expand=True)
        
        self.password_listbox = tk.Listbox(
            list_frame,
            font=('Microsoft YaHei', 10),
            bg='#ffffff'
        )
        self.password_listbox.pack(side='left', fill='both', expand=True)
        
        # 更新密码列表
        for password in self.passwords:
            self.password_listbox.insert(tk.END, password)
            
        # 滚动条
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        self.password_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.password_listbox.yview)
        
        # 输入框和按钮
        input_frame = tk.Frame(password_window, bg='#f0f0f0')
        input_frame.pack(pady=10, padx=20, fill='x')
        
        self.password_entry = tk.Entry(
            input_frame,
            font=('Microsoft YaHei', 10),
            show='*'
        )
        self.password_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        add_btn = tk.Button(
            input_frame,
            text="添加",
            font=('Microsoft YaHei', 9),
            bg='#4CAF50',
            fg='white',
            relief='flat',
            command=self.add_password
        )
        add_btn.pack(side='right', padx=(0, 5))
        
        remove_btn = tk.Button(
            input_frame,
            text="删除",
            font=('Microsoft YaHei', 9),
            bg='#f44336',
            fg='white',
            relief='flat',
            command=self.remove_password
        )
        remove_btn.pack(side='right')
        
    def add_password(self):
        """添加密码"""
        password = self.password_entry.get().strip()
        if password and password not in self.passwords:
            self.passwords.append(password)
            self.password_listbox.insert(tk.END, password)
            self.password_entry.delete(0, tk.END)
            self.save_passwords()
            
    def remove_password(self):
        """删除选中的密码"""
        selection = self.password_listbox.curselection()
        if selection:
            index = selection[0]
            password = self.passwords.pop(index)
            self.password_listbox.delete(index)
            self.save_passwords()
            
    def toggle_processing(self):
        """切换处理状态（开始/停止）"""
        if self.is_processing:
            # 当前正在处理，执行停止操作
            self.stop_processing = True
            self.log("⏹️ 用户请求停止处理...")
            self.main_action_btn.config(state='disabled', text='正在停止...', bg='#8c959f')
        else:
            # 当前未处理，执行开始操作
            self.start_processing()
    
    def start_processing(self):
        """开始处理选中的文件夹"""
        if not self.selected_folder:
            messagebox.showwarning("警告", "请先选择一个文件夹")
            return
            
        if not self.bandizip_path:
            bandizip_path = filedialog.askopenfilename(
                title="请选择Bandizip.exe",
                filetypes=[("可执行文件", "*.exe")]
            )
            if bandizip_path:
                self.bandizip_path = bandizip_path
            else:
                messagebox.showerror("错误", "需要Bandizip才能解压文件")
                return
        
        if self.is_processing:
            messagebox.showinfo("提示", "正在处理中，请等待当前任务完成")
            return
            
        # 确认开始处理
        result = messagebox.askyesno(
            "确认处理", 
            f"即将处理文件夹:\n{self.selected_folder}\n\n" +
            "处理过程中会自动解压并删除原压缩包。\n" +
            "确定要继续吗？"
        )
        
        if not result:
            return
            
        # 在新线程中处理，避免界面卡死
        self.is_processing = True
        self.stop_processing = False
        self.main_action_btn.config(state='normal', text='⏹️ 停止处理', bg='#da3633')
        self.select_btn.config(state='disabled')
        self.progress.start()
        self.log("="*50)
        self.log(f"开始处理文件夹: {self.selected_folder}", operation_type='start')
        if self.has_password.get():
            self.log("🔒 已启用密码模式，将跳过无密码尝试")
        else:
            self.log("🔓 无密码模式，将先尝试无密码解压")
        if self.use_bandizip_wait.get():
            self.log("⏳ 已启用Bandizip手动密码输入")
        else:
            self.log("⏭️ 已禁用Bandizip手动密码输入")
        
        processing_thread = threading.Thread(
            target=self.process_folder,
            args=(self.selected_folder,)
        )
        processing_thread.daemon = True
        processing_thread.start()
        
    def process_folder(self, folder_path):
        """处理文件夹中的压缩包"""
        try:
            self.log(f"开始处理文件夹: {folder_path}")
            self._process_folder_recursive(folder_path)
            self.log("处理完成！")
        except Exception as e:
            self.log(f"处理过程中出现错误: {e}")
        finally:
            self.root.after(0, self._processing_finished)
            
    def _processing_finished(self):
        """处理完成后的UI更新"""
        was_stopped = self.stop_processing
        self.is_processing = False
        self.stop_processing = False
        self.progress.stop()
        self.main_action_btn.config(state='normal', text='⚡ 开始处理', bg='#fb8500')
        self.select_btn.config(state='normal')
        self.log("="*50)
        if was_stopped:
            self.log("处理已被用户停止！", operation_type='end')
            if SYSTEM_POPUP_AVAILABLE:
                win32api.MessageBox(0, "处理已被用户停止！", "已停止", win32con.MB_OK | win32con.MB_ICONINFORMATION)
            else:
                messagebox.showinfo("已停止", "处理已被用户停止！")
        else:
            self.log("文件夹处理完成！", operation_type='end')
            if SYSTEM_POPUP_AVAILABLE:
                win32api.MessageBox(0, "文件夹处理完成！", "完成", win32con.MB_OK | win32con.MB_ICONINFORMATION)
            else:
                messagebox.showinfo("完成", "文件夹处理完成！")
        
    def _process_folder_recursive(self, folder_path):
        """递归处理文件夹"""
        try:
            # 检查是否需要停止处理
            if self.stop_processing:
                self.log("⏹️ 处理已被用户停止")
                return
                
            # 检查新的终止条件：出现exe等可执行文件或没有压缩包
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            
            # 检查是否有可执行文件
            executable_extensions = ['.exe', '.msi', '.bat', '.cmd', '.com', '.scr']
            has_executable = any(f.lower().endswith(ext) for f in files for ext in executable_extensions)
            
            # 检查是否还有压缩包（包括正常格式和异常格式）
            has_normal_archive = any(f.lower().endswith(ext) for f in files for ext in self.archive_extensions)
            has_malformed_archive = any(self.is_malformed_archive(f) for f in files)
            has_archive = has_normal_archive or has_malformed_archive
            
            if has_executable:
                self.log(f"🎯 文件夹 {os.path.basename(folder_path)} 中发现可执行文件，停止处理")
                return
            elif not has_archive:
                self.log(f"📁 文件夹 {os.path.basename(folder_path)} 中没有压缩包，跳过当前文件夹但继续递归子文件夹")
                # 不直接返回，而是跳过当前文件夹的处理，但仍然递归处理子文件夹
                # 递归处理子文件夹
                try:
                    for item in os.listdir(folder_path):
                        item_path = os.path.join(folder_path, item)
                        if os.path.isdir(item_path):
                            self._process_folder_recursive(item_path)
                except OSError as e:
                    self.log(f"⚠️ 无法读取子文件夹: {e}")
                return
                
            # 记录已处理的压缩包，避免重复处理
            processed_archives = set()
                
            self.log(f"🔍 检查文件夹: {os.path.basename(folder_path)}")
            
            # 多轮处理，直到没有新的压缩包可处理
            max_rounds = 5  # 防止无限循环
            round_count = 0
            
            while round_count < max_rounds:
                # 检查是否需要停止处理
                if self.stop_processing:
                    self.log("⏹️ 处理已被用户停止")
                    return
                    
                round_count += 1
                processed_any = False
                
                # 重新获取当前文件夹内容（因为解压可能产生新文件）
                current_files = []
                try:
                    current_files = os.listdir(folder_path)
                except OSError as e:
                    self.log(f"⚠️ 无法读取文件夹 {folder_path}: {e}")
                    break
                
                # 处理当前文件夹中的压缩包
                for filename in current_files:
                    # 检查是否需要停止处理
                    if self.stop_processing:
                        self.log("⏹️ 处理已被用户停止")
                        return
                    file_path = os.path.join(folder_path, filename)
                    if os.path.isfile(file_path):
                        # 跳过已处理的压缩包
                        if filename in processed_archives:
                            continue
                            
                        if self.is_malformed_archive(filename):
                            self.log(f"🗜️ 发现异常格式压缩包: {filename}")
                            corrected_path = self.correct_archive_name(file_path)
                            if corrected_path and self.extract_archive(corrected_path, folder_path):
                                # 不删除源压缩文件，保留原始文件
                                self.log(f"💾 保留原压缩包: {filename}")
                                processed_archives.add(filename)  # 标记原始文件名为已处理
                                # 同时标记修正后的文件名为已处理，避免重复解压
                                corrected_filename = os.path.basename(corrected_path)
                                processed_archives.add(corrected_filename)
                                processed_any = True
                                self.log(f"✅ 第{round_count}轮处理完成: {filename}")
                                break  # 处理一个文件后重新扫描
                        elif any(filename.lower().endswith(ext) for ext in self.archive_extensions):
                            # 检查是否是正常格式的压缩包但需要解压
                            if self._should_extract_normal_archive(file_path):
                                self.log(f"🗜️ 发现需要解压的压缩包: {filename}")
                                if self.extract_archive(file_path, folder_path):
                                    # 不删除源压缩文件，保留原始文件
                                    self.log(f"💾 保留原压缩包: {filename}")
                                    processed_archives.add(filename)  # 标记为已处理
                                    processed_any = True
                                    self.log(f"✅ 第{round_count}轮处理完成: {filename}")
                                    break  # 处理一个文件后重新扫描
                
                # 如果这一轮没有处理任何文件，退出循环
                if not processed_any:
                    break
                    
                self.log(f"🔄 第{round_count}轮处理完成，继续检查...")
            
            # 递归处理子文件夹
            try:
                for item in os.listdir(folder_path):
                    item_path = os.path.join(folder_path, item)
                    if os.path.isdir(item_path):
                        self._process_folder_recursive(item_path)
            except OSError as e:
                self.log(f"⚠️ 无法读取子文件夹: {e}")
                
        except Exception as e:
            self.log(f"💥 处理文件夹时出错: {e}")
    
    def _should_extract_normal_archive(self, file_path):
        """判断是否应该解压正常格式的压缩包"""
        # 获取文件夹中的文件数量
        folder_path = os.path.dirname(file_path)
        try:
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            # 如果文件夹中只有这一个压缩包，或者压缩包数量较少，则解压
            archive_files = [f for f in files if any(f.lower().endswith(ext) for ext in self.archive_extensions)]
            return len(files) <= 2 or len(archive_files) == 1
        except:
            return False
                    
    def is_malformed_archive(self, filename):
        """检查是否为异常格式的压缩包"""
        filename_lower = filename.lower()
        
        # 检查是否包含压缩包扩展名但格式异常
        for ext in self.archive_extensions:
            if ext in filename_lower:
                # 如果文件名包含扩展名但不以该扩展名结尾，则认为是异常格式
                if not filename_lower.endswith(ext):
                    # 进一步检查，确保不是复合扩展名（如.tar.gz）
                    if ext == '.gz' and filename_lower.endswith('.tar.gz'):
                        continue
                    if ext == '.bz2' and filename_lower.endswith('.tar.bz2'):
                        continue
                    if ext == '.xz' and filename_lower.endswith('.tar.xz'):
                        continue
                    return True
        return False
        
    def correct_archive_name(self, file_path):
        """修正压缩包文件名"""
        try:
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            filename_lower = filename.lower()
            
            # 尝试修正文件名
            corrected_name = filename
            
            # 按扩展名长度排序，优先处理较长的扩展名（如.tar.gz）
            sorted_extensions = sorted(self.archive_extensions, key=len, reverse=True)
            
            for ext in sorted_extensions:
                if ext in filename_lower and not filename_lower.endswith(ext):
                    # 找到扩展名的位置
                    ext_pos = filename_lower.find(ext)
                    if ext_pos != -1:
                        # 保留扩展名之前的部分，去掉扩展名之后的部分
                        base_name = filename[:ext_pos]
                        corrected_name = base_name + ext
                        break
                        
            corrected_path = os.path.join(directory, corrected_name)
            
            if corrected_name != filename:
                # 检查目标文件是否已存在
                if os.path.exists(corrected_path):
                    # 如果存在，添加数字后缀
                    base, ext = os.path.splitext(corrected_name)
                    counter = 1
                    while os.path.exists(os.path.join(directory, f"{base}_{counter}{ext}")):
                        counter += 1
                    corrected_name = f"{base}_{counter}{ext}"
                    corrected_path = os.path.join(directory, corrected_name)
                    
                os.rename(file_path, corrected_path)
                self.log(f"文件名已修正: {filename} -> {corrected_name}")
                return corrected_path
            else:
                return file_path
                
        except Exception as e:
            self.log(f"修正文件名失败: {e}")
            return None
            
    def extract_archive(self, archive_path, extract_to):
        """使用Bandizip解压文件"""
        try:
            self.log(f"📦 开始解压: {os.path.basename(archive_path)}")
            self.log(f"📁 目标路径: {extract_to}")
            
            # 检查源文件是否存在
            if not os.path.exists(archive_path):
                self.log(f"❌ 源文件不存在: {archive_path}")
                return False
                
            # 检查目标路径是否存在，不存在则创建
            if not os.path.exists(extract_to):
                try:
                    os.makedirs(extract_to, exist_ok=True)
                    self.log(f"📁 创建目标目录: {extract_to}")
                except Exception as e:
                    self.log(f"❌ 无法创建目标目录: {e}")
                    return False
            
            # 记录解压前的文件列表
            files_before = set()
            try:
                files_before = set(os.listdir(extract_to))
                self.log(f"📋 解压前目标目录文件数: {len(files_before)}")
            except Exception as e:
                self.log(f"⚠️ 无法读取目标目录: {e}")
            
            # 根据密码选项决定密码尝试策略
            if self.has_password:
                # 如果选择了有密码模式，跳过无密码尝试
                passwords_to_try = self.passwords
                self.log("🔐 密码模式：跳过无密码尝试，直接使用密码列表")
            else:
                # 默认模式：先尝试无密码，再尝试密码列表
                passwords_to_try = [''] + self.passwords
            
            for i, password in enumerate(passwords_to_try):
                try:
                    # 构建命令行参数，参考批处理文件格式
                    if password:
                        # 使用类似批处理文件的格式: Bandizip.exe x -p:password -o:path "archive"
                        cmd = [self.bandizip_path, 'x', f'-p:{password}', f'-o:{extract_to}', '-y', '-aoa', archive_path]
                        self.log(f"🔑 尝试密码 {i+1}/{len(passwords_to_try)}: {'***' if password else '(无密码)'}")
                    else:
                        cmd = [self.bandizip_path, 'x', f'-o:{extract_to}', '-y', '-aoa', archive_path]
                        self.log("🔓 尝试无密码解压...")
                    
                    # 记录实际执行的命令（用于调试）
                    cmd_str = ' '.join([f'"{arg}"' if ' ' in arg else arg for arg in cmd])
                    self.log(f"💻 执行命令: {cmd_str}")
                        
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=300,  # 5分钟超时
                        shell=False  # 不使用shell，避免引号问题
                    )
                    
                    # 详细记录命令执行结果
                    self.log(f"📊 命令返回码: {result.returncode}")
                    if result.stdout:
                        stdout_lines = result.stdout.strip().split('\n')
                        for line in stdout_lines:
                            if line.strip():
                                self.log(f"📤 标准输出: {line.strip()}")
                    if result.stderr:
                        stderr_lines = result.stderr.strip().split('\n')
                        for line in stderr_lines:
                            if line.strip():
                                self.log(f"📥 错误输出: {line.strip()}")
                    
                    # 分析Bandizip的输出信息
                    success_indicators = ['Everything is Ok', 'Files: ', 'Folders: ']
                    error_indicators = ['Wrong password', 'Data Error', 'CRC Failed', 'Cannot open']
                    
                    output_text = (result.stdout + result.stderr).lower()
                    has_success_indicator = any(indicator.lower() in output_text for indicator in success_indicators)
                    has_error_indicator = any(indicator.lower() in output_text for indicator in error_indicators)
                    
                    if has_error_indicator:
                        self.log(f"🔍 检测到错误指示符，可能是密码错误或文件损坏")
                    elif has_success_indicator:
                        self.log(f"🔍 检测到成功指示符，解压可能成功")
                    
                    # 等待解压操作完全完成
                    time.sleep(2)  # 等待2秒确保文件系统操作完成
                    self.log("⏳ 等待解压操作完成...")
                    
                    # 检查解压后的文件变化（多次检查确保准确性）
                    files_after = set()
                    new_files = set()
                    
                    for check_attempt in range(3):  # 最多检查3次
                        try:
                            files_after = set(os.listdir(extract_to))
                            new_files = files_after - files_before
                            
                            if new_files:
                                break  # 发现新文件，退出检查循环
                            elif check_attempt < 2:  # 如果还有检查机会
                                time.sleep(1)  # 再等待1秒
                                self.log(f"🔄 第{check_attempt + 2}次检查文件变化...")
                        except Exception as e:
                            self.log(f"⚠️ 第{check_attempt + 1}次检查失败: {e}")
                            if check_attempt < 2:
                                time.sleep(1)
                    
                    try:
                        self.log(f"📋 解压后目标目录文件数: {len(files_after)}")
                        if new_files:
                            self.log(f"📄 新增文件: {', '.join(list(new_files)[:5])}{'...' if len(new_files) > 5 else ''}")
                        else:
                            self.log(f"⚠️ 未发现新文件")
                    except Exception as e:
                        self.log(f"⚠️ 无法检查解压结果: {e}")
                    
                    if result.returncode == 0 and len(files_after) > len(files_before):
                        self.log(f"✅ 解压成功: {os.path.basename(archive_path)}")
                        return True
                    else:
                        if password:
                            self.log(f"❌ 密码错误或文件损坏 (返回码: {result.returncode})")
                        else:
                            self.log(f"❌ 无密码解压失败 (返回码: {result.returncode})")
                        
                except subprocess.TimeoutExpired:
                    self.log(f"⏰ 解压超时: {os.path.basename(archive_path)}")
                    break
                except Exception as e:
                    self.log(f"⚠️ 解压过程出错: {e}")
                    continue
                    
            # 根据用户设置决定是否使用Bandizip内置密码管理器
            if self.use_bandizip_wait.get():
                self.log(f"🔑 尝试使用Bandizip内置密码管理器...")
                if self.try_bandizip_password_manager(archive_path, extract_to):
                    return True
            else:
                self.log(f"⏭️ 已跳过Bandizip手动密码输入（用户未启用）")
                
            self.log(f"❌ 解压失败: {os.path.basename(archive_path)} (已尝试所有密码和密码管理器)")
            return False
            
        except Exception as e:
            self.log(f"💥 解压文件时出错: {e}")
            return False
            
    def try_bandizip_password_manager(self, archive_path, extract_to):
        """尝试使用Bandizip内置密码管理器解压文件"""
        try:
            # 记录解压前的文件列表
            files_before = set()
            try:
                files_before = set(os.listdir(extract_to))
            except Exception:
                files_before = set()
            
            # 使用Bandizip GUI模式打开文件，让用户手动输入密码
            # 这会调用Bandizip的密码管理器
            cmd = [self.bandizip_path, archive_path]
            self.log(f"💻 启动Bandizip GUI: {' '.join(cmd)}")
            
            # 启动Bandizip GUI（非阻塞）
            process = subprocess.Popen(cmd, shell=False)
            
            # 等待用户操作（最多等待60秒）
            self.log(f"⏳ 等待用户在Bandizip中输入密码并解压（最多60秒）...")
            
            # 检查文件变化
            for i in range(60):  # 检查60次，每次等待1秒
                time.sleep(1)
                try:
                    files_after = set(os.listdir(extract_to))
                    new_files = files_after - files_before
                    
                    if new_files:
                        self.log(f"✅ 检测到新文件，解压成功: {', '.join(list(new_files)[:3])}{'...' if len(new_files) > 3 else ''}")
                        # 尝试终止Bandizip进程
                        try:
                            process.terminate()
                        except Exception:
                            pass
                        return True
                except Exception:
                    continue
            
            # 超时后终止进程
            try:
                process.terminate()
                self.log(f"⏰ 等待超时，已终止Bandizip进程")
            except Exception:
                pass
                
            return False
            
        except Exception as e:
            self.log(f"⚠️ 使用密码管理器时出错: {e}")
            return False
            
    def run(self):
        """运行应用程序"""
        self.root.mainloop()

if __name__ == "__main__":
    app = ArchiveProcessor()
    app.run()