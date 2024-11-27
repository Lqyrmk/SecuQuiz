import os
import platform

def clear_console():
    # 判断当前操作系统
    if platform.system() == 'Windows':
        os.system('cls')  # Windows
    else:
        os.system('clear')  # Unix/Linux/macOS