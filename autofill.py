#coding=utf-8
# 需求描述

# 	1.	读取本地txt文件内容。
# 	2.	txt文件包含个人描述，第一行是名字，第二行是电话号码。
# 	3.	自动识别网页中相应的字段，并填写读取的名字和电话号码。
import pyautogui as pag
import time
import tkinter as tk
from tkinter import filedialog

def browse_file():
    filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    with open(filename, 'r') as file:
        lines = file.readlines()
        global name, phone
        name = lines[0].strip()
        phone = lines[1].strip()
        status_label.config(text="文件加载成功")

def fill_form(name, phone):
    time.sleep(3)  # 给用户时间切换到表单界面
    # 下面是模拟键盘操作填充表单字段的示例
    pag.click(x=200, y=300)  # 点击名字字段（示例坐标）
    pag.write(name)
    pag.press('tab')
    pag.write(phone)

root = tk.Tk()
root.title("自动填表工具")

browse_button = tk.Button(root, text="选择文件", command=browse_file)
browse_button.pack()

fill_button = tk.Button(root, text="开始填表", command=lambda: fill_form(name, phone))
fill_button.pack()

status_label = tk.Label(root, text="")
status_label.pack()

root.mainloop()