#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包脚本 - 使用PyInstaller将程序打包为exe
"""

import os
import sys
import shutil


def clean_build():
    """清理之前的构建文件"""
    dirs_to_remove = ['build', 'dist']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print(f"Removing {dir_name}...")
            shutil.rmtree(dir_name)
    
    # 删除spec文件
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            print(f"Removing {file}...")
            os.remove(file)


def build_exe():
    """打包exe"""
    import PyInstaller.__main__
    
    # 打包参数
    args = [
        'main.py',  # 主程序入口
        '--name=OCR变量管理器',  # exe名称
        '--windowed',  # 使用窗口模式（不显示控制台）
        '--onefile',  # 打包为单个exe文件
        '--icon=resources/icon.ico',  # 图标文件
        '--add-data=config.yaml;.',  # 包含配置文件
        '--add-data=ui;ui',  # 包含ui模块
        '--add-data=core;core',  # 包含core模块
        '--add-data=resources;resources',  # 包含resources模块（包含图标）
        '--hidden-import=PyQt5',  # 隐藏导入
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=apscheduler',
        '--hidden-import=apscheduler.schedulers.background',
        '--hidden-import=apscheduler.triggers.cron',
        '--hidden-import=apscheduler.triggers.interval',
        '--hidden-import=yaml',
        '--hidden-import=PIL',
        '--hidden-import=cv2',
        '--hidden-import=numpy',
        '--hidden-import=requests',
        '--hidden-import=fastapi',
        '--hidden-import=uvicorn',
        '--hidden-import=winshell',
        '--hidden-import=win32com.client',
    ]
    
    print("Building executable...")
    print(f"Args: {' '.join(args)}")
    
    PyInstaller.__main__.run(args)


def copy_additional_files():
    """复制额外文件到dist目录"""
    dist_dir = 'dist'
    
    # 确保config.yaml存在
    if not os.path.exists(os.path.join(dist_dir, 'config.yaml')):
        if os.path.exists('config.yaml'):
            print("Copying config.yaml to dist...")
            shutil.copy('config.yaml', dist_dir)
    
    # 创建images目录
    images_dir = os.path.join(dist_dir, 'images')
    if not os.path.exists(images_dir):
        print("Creating images directory...")
        os.makedirs(images_dir)
    
    # 创建logs目录
    logs_dir = os.path.join(dist_dir, 'logs')
    if not os.path.exists(logs_dir):
        print("Creating logs directory...")
        os.makedirs(logs_dir)


def main():
    """主函数"""
    print("=" * 60)
    print("OCR变量管理器 - 打包工具")
    print("=" * 60)
    
    # 清理
    print("\nStep 1: Cleaning previous builds...")
    clean_build()
    
    # 打包
    print("\nStep 2: Building executable...")
    build_exe()
    
    # 复制额外文件
    print("\nStep 3: Copying additional files...")
    copy_additional_files()
    
    print("\n" + "=" * 60)
    print("Build completed!")
    print(f"Executable: dist/OCR变量管理器.exe")
    print("=" * 60)


if __name__ == '__main__':
    main()
