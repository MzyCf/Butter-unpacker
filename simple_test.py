#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化测试程序
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys

print("Python版本:", sys.version)
print("当前工作目录:", os.getcwd())

try:
    import tkinterdnd2 as tkdnd
    print("tkinterdnd2导入成功")
    DND_AVAILABLE = True
except ImportError as e:
    print(f"tkinterdnd2导入失败: {e}")
    DND_AVAILABLE = False

class SimpleTest:
    def __init__(self):
        print("初始化GUI...")
        
        if DND_AVAILABLE:
            self.root = tkdnd.Tk()
            print("使用tkinterdnd2.Tk()")
        else:
            self.root = tk.Tk()
            print("使用标准tk.Tk()")
            
        self.root.title("简单测试")
        self.root.geometry("400x300")
        
        # 简单的标签
        label = tk.Label(self.root, text="GUI测试程序", font=('Arial', 14))
        label.pack(pady=20)
        
        # 选择文件夹按钮
        btn = tk.Button(
            self.root, 
            text="选择文件夹", 
            command=self.select_folder,
            font=('Arial', 10)
        )
        btn.pack(pady=10)
        
        # 状态标签
        self.status_label = tk.Label(self.root, text="等待选择文件夹...")
        self.status_label.pack(pady=10)
        
        # 如果支持拖放，添加拖放区域
        if DND_AVAILABLE:
            self.setup_drag_drop()
        
        print("GUI初始化完成")
        
    def setup_drag_drop(self):
        """设置拖放功能"""
        try:
            drop_frame = tk.Frame(self.root, bg='lightgray', height=100)
            drop_frame.pack(pady=20, padx=20, fill='x')
            drop_frame.pack_propagate(False)
            
            drop_label = tk.Label(drop_frame, text="拖放文件夹到此处", bg='lightgray')
            drop_label.pack(expand=True)
            
            drop_frame.drop_target_register(tkdnd.DND_FILES)
            drop_frame.dnd_bind('<<Drop>>', self.on_drop)
            
            print("拖放功能设置完成")
        except Exception as e:
            print(f"设置拖放功能失败: {e}")
            
    def on_drop(self, event):
        """处理拖放事件"""
        try:
            files = self.root.tk.splitlist(event.data)
            if files:
                folder_path = files[0]
                if os.path.isdir(folder_path):
                    self.status_label.config(text=f"拖放选择: {os.path.basename(folder_path)}")
                    print(f"拖放文件夹: {folder_path}")
                else:
                    self.status_label.config(text="请拖放文件夹，不是文件")
        except Exception as e:
            print(f"拖放处理错误: {e}")
            
    def select_folder(self):
        """选择文件夹"""
        try:
            folder_path = filedialog.askdirectory(title="选择文件夹")
            if folder_path:
                self.status_label.config(text=f"选择: {os.path.basename(folder_path)}")
                print(f"选择文件夹: {folder_path}")
                
                # 列出文件夹内容
                try:
                    items = os.listdir(folder_path)
                    print(f"文件夹内容 ({len(items)}项):")
                    for item in items[:10]:  # 只显示前10项
                        print(f"  - {item}")
                    if len(items) > 10:
                        print(f"  ... 还有 {len(items) - 10} 项")
                except Exception as e:
                    print(f"列出文件夹内容失败: {e}")
        except Exception as e:
            print(f"选择文件夹错误: {e}")
            
    def run(self):
        """运行程序"""
        print("启动主循环...")
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"主循环错误: {e}")
        print("程序结束")

if __name__ == "__main__":
    print("=== 简化测试程序启动 ===")
    try:
        app = SimpleTest()
        app.run()
    except Exception as e:
        print(f"程序运行错误: {e}")
        import traceback
        traceback.print_exc()
    print("=== 程序结束 ===")