#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心功能测试（无GUI）
测试压缩包检测和处理逻辑
"""

import os
import re
import json
from pathlib import Path

class ArchiveProcessorCore:
    def __init__(self):
        # 支持的压缩包格式
        self.archive_extensions = ['.7z', '.zip', '.rar', '.tar', '.gz', '.bz2', '.xz']
        
        # 测试密码列表
        self.passwords = ['123456', 'password', '123', 'admin', '']
        
    def is_malformed_archive(self, filename):
        """检查是否为异常格式的压缩包"""
        # 检查是否包含压缩包扩展名但格式异常
        for ext in self.archive_extensions:
            if ext in filename.lower() and not filename.lower().endswith(ext):
                return True
        return False
        
    def correct_archive_name(self, filename):
        """修正压缩包文件名"""
        try:
            # 尝试修正文件名
            corrected_name = filename
            for ext in self.archive_extensions:
                if ext in filename.lower():
                    # 找到扩展名位置并修正
                    pattern = re.compile(re.escape(ext) + r'[^.]*', re.IGNORECASE)
                    corrected_name = pattern.sub(ext, filename)
                    break
                    
            return corrected_name if corrected_name != filename else None
                
        except Exception as e:
            print(f"修正文件名失败: {e}")
            return None
            
    def analyze_folder(self, folder_path):
        """分析文件夹内容"""
        if not os.path.exists(folder_path):
            return None
            
        try:
            items = os.listdir(folder_path)
            files = [f for f in items if os.path.isfile(os.path.join(folder_path, f))]
            dirs = [f for f in items if os.path.isdir(os.path.join(folder_path, f))]
            
            # 检查异常压缩包
            malformed_archives = []
            for filename in files:
                if self.is_malformed_archive(filename):
                    corrected = self.correct_archive_name(filename)
                    malformed_archives.append({
                        'original': filename,
                        'corrected': corrected
                    })
                    
            return {
                'path': folder_path,
                'total_items': len(items),
                'files': len(files),
                'directories': len(dirs),
                'malformed_archives': malformed_archives,
                'should_stop': len(files) > 2  # 终止条件
            }
            
        except Exception as e:
            print(f"分析文件夹失败: {e}")
            return None
            
    def test_with_sample_files(self):
        """使用示例文件名测试"""
        test_files = [
            "document.7z删",
            "backup.zip备份",
            "archive.rar.old",
            "data.tar.gz.bak",
            "normal.txt",
            "image.jpg",
            "video.7z",  # 正常格式
            "compressed.zip"  # 正常格式
        ]
        
        print("=== 文件名检测测试 ===")
        for filename in test_files:
            is_malformed = self.is_malformed_archive(filename)
            corrected = self.correct_archive_name(filename) if is_malformed else None
            
            print(f"文件: {filename}")
            print(f"  异常格式: {'是' if is_malformed else '否'}")
            if corrected:
                print(f"  修正后: {corrected}")
            print()
            
    def test_folder_analysis(self, test_folder=None):
        """测试文件夹分析功能"""
        if test_folder is None:
            test_folder = os.getcwd()  # 使用当前目录
            
        print(f"=== 文件夹分析测试 ===")
        print(f"分析目录: {test_folder}")
        
        result = self.analyze_folder(test_folder)
        if result:
            print(f"总项目数: {result['total_items']}")
            print(f"文件数: {result['files']}")
            print(f"目录数: {result['directories']}")
            print(f"是否应停止处理: {'是' if result['should_stop'] else '否'}")
            
            if result['malformed_archives']:
                print(f"\n发现异常压缩包 ({len(result['malformed_archives'])}个):")
                for archive in result['malformed_archives']:
                    print(f"  {archive['original']} -> {archive['corrected']}")
            else:
                print("\n未发现异常压缩包")
        else:
            print("分析失败")
            
    def save_test_config(self):
        """保存测试配置"""
        config = {
            'passwords': self.passwords,
            'archive_extensions': self.archive_extensions
        }
        
        try:
            with open('test_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print("测试配置已保存到 test_config.json")
        except Exception as e:
            print(f"保存配置失败: {e}")
            
def main():
    print("=== 压缩包处理器核心功能测试 ===")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Python版本: {os.sys.version}")
    print()
    
    processor = ArchiveProcessorCore()
    
    # 测试文件名检测和修正
    processor.test_with_sample_files()
    
    # 测试文件夹分析
    processor.test_folder_analysis()
    
    # 保存测试配置
    processor.save_test_config()
    
    print("\n=== 测试完成 ===")
    
    # 等待用户输入（如果在交互环境中）
    try:
        input("\n按回车键退出...")
    except:
        pass

if __name__ == "__main__":
    main()