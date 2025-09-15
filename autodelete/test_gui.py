#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试GUI功能的简化版本
用于验证拖放和文件选择功能
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os

try:
    import tkinterdnd2 as tkdnd
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    print("警告: tkinterdnd2 未安装，拖放功能将不可用")
    print("请运行: pip install tkinterdnd2")

class TestGUI:
    def __init__(self):
        if DND_AVAILABLE:
            self.root = tkdnd.Tk()
        else:
            self.root = tk.Tk()
            
        self.root.title("GUI功能测试")
        self.root.geometry("500x400")
        self.root.configure(bg='#f0f0f0')
        
        self.selected_folder = None
        self.setup_ui()
        
        if DND_AVAILABLE:
            self.setup_drag_drop()
        
    def setup_ui(self):
        """设置测试界面"""
        # 标题
        title_label = tk.Label(
            self.root, 
            text="GUI功能测试", 
            font=('Microsoft YaHei', 16, 'bold'),
            bg='#f0f0f0',
            fg='#333333'
        )
        title_label.pack(pady=20)
        
        # 拖放区域
        self.drop_frame = tk.Frame(
            self.root, 
            bg='#ffffff', 
            relief='dashed', 
            bd=2,
            height=120
        )
        self.drop_frame.pack(pady=20, padx=40, fill='x')
        self.drop_frame.pack_propagate(False)
        
        if DND_AVAILABLE:
            drop_text = "拖放文件夹到此处\n(拖放功能已启用)"
        else:
            drop_text = "拖放功能不可用\n请安装 tkinterdnd2"
            
        drop_label = tk.Label(
            self.drop_frame,
            text=drop_text,
            font=('Microsoft YaHei', 12),
            bg='#ffffff',
            fg='#666666' if DND_AVAILABLE else '#ff0000'
        )
        drop_label.pack(expand=True)
        
        # 按钮
        button_frame = tk.Frame(self.root, bg='#f0f0f0')
        button_frame.pack(pady=20)
        
        select_btn = tk.Button(
            button_frame,
            text="选择文件夹",
            font=('Microsoft YaHei', 10),
            bg='#4CAF50',
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            command=self.select_folder
        )
        select_btn.pack(side='left', padx=10)
        
        test_btn = tk.Button(
            button_frame,
            text="测试选择的文件夹",
            font=('Microsoft YaHei', 10),
            bg='#2196F3',
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            command=self.test_folder
        )
        test_btn.pack(side='left', padx=10)
        
        # 状态显示
        self.status_label = tk.Label(
            self.root,
            text="请选择一个文件夹",
            font=('Microsoft YaHei', 10),
            bg='#f0f0f0',
            fg='#666666',
            wraplength=400
        )
        self.status_label.pack(pady=20)
        
        # 文件列表
        list_frame = tk.Frame(self.root, bg='#f0f0f0')
        list_frame.pack(pady=10, padx=40, fill='both', expand=True)
        
        tk.Label(
            list_frame, 
            text="文件夹内容:", 
            font=('Microsoft YaHei', 10, 'bold'),
            bg='#f0f0f0'
        ).pack(anchor='w')
        
        self.file_listbox = tk.Listbox(
            list_frame,
            font=('Consolas', 9),
            bg='#ffffff'
        )
        self.file_listbox.pack(fill='both', expand=True, pady=(5, 0))
        
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
                self.update_status(f"拖放选择: {folder_path}")
                self.list_folder_contents()
            else:
                messagebox.showwarning("警告", "请拖放文件夹，不是文件")
                
    def select_folder(self):
        """选择文件夹对话框"""
        folder_path = filedialog.askdirectory(title="选择要测试的文件夹")
        if folder_path:
            self.selected_folder = folder_path
            self.update_status(f"对话框选择: {folder_path}")
            self.list_folder_contents()
            
    def update_status(self, message):
        """更新状态显示"""
        self.status_label.config(text=message)
        
    def list_folder_contents(self):
        """列出文件夹内容"""
        if not self.selected_folder:
            return
            
        self.file_listbox.delete(0, tk.END)
        
        try:
            items = os.listdir(self.selected_folder)
            if not items:
                self.file_listbox.insert(tk.END, "(文件夹为空)")
            else:
                for item in sorted(items):
                    item_path = os.path.join(self.selected_folder, item)
                    if os.path.isdir(item_path):
                        self.file_listbox.insert(tk.END, f"📁 {item}")
                    else:
                        self.file_listbox.insert(tk.END, f"📄 {item}")
        except Exception as e:
            self.file_listbox.insert(tk.END, f"错误: {e}")
            
    def test_folder(self):
        """测试选择的文件夹"""
        if not self.selected_folder:
            messagebox.showwarning("警告", "请先选择文件夹")
            return
            
        try:
            items = os.listdir(self.selected_folder)
            file_count = len([f for f in items if os.path.isfile(os.path.join(self.selected_folder, f))])
            dir_count = len([f for f in items if os.path.isdir(os.path.join(self.selected_folder, f))])
            
            # 检查是否有可能的压缩包
            archive_extensions = ['.7z', '.zip', '.rar', '.tar', '.gz', '.bz2', '.xz']
            potential_archives = []
            
            for item in items:
                if os.path.isfile(os.path.join(self.selected_folder, item)):
                    # 检查异常格式的压缩包
                    for ext in archive_extensions:
                        if ext in item.lower() and not item.lower().endswith(ext):
                            potential_archives.append(item)
                            break
                            
            message = f"文件夹分析结果:\n\n"
            message += f"路径: {self.selected_folder}\n"
            message += f"文件数量: {file_count}\n"
            message += f"子文件夹数量: {dir_count}\n\n"
            
            if potential_archives:
                message += f"发现可能的异常压缩包 ({len(potential_archives)}个):\n"
                for archive in potential_archives[:5]:  # 最多显示5个
                    message += f"  • {archive}\n"
                if len(potential_archives) > 5:
                    message += f"  ... 还有 {len(potential_archives) - 5} 个\n"
            else:
                message += "未发现异常格式的压缩包\n"
                
            # 检查终止条件
            if file_count > 2:
                message += f"\n⚠️ 文件数量({file_count})大于2，符合处理终止条件"
            else:
                message += f"\n✅ 文件数量({file_count})不大于2，可以继续处理"
                
            messagebox.showinfo("测试结果", message)
            
        except Exception as e:
            messagebox.showerror("错误", f"测试文件夹时出错: {e}")
            
    def run(self):
        """运行测试程序"""
        self.root.mainloop()

if __name__ == "__main__":
    print("启动GUI功能测试...")
    if not DND_AVAILABLE:
        print("\n注意: 拖放功能需要安装 tkinterdnd2")
        print("安装命令: pip install tkinterdnd2")
        print("\n当前只能测试文件选择对话框功能\n")
    
    app = TestGUI()
    app.run()