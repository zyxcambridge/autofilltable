# 自动填表工具

## 简介
该工具用于自动识别本地个人信息并填充到表单中。使用Python实现，通过PyAutoGUI模拟键盘和鼠标操作，并使用tkinter提供图形用户界面。

## 功能
- 读取本地Excel文件中的个人信息
- 识别并提取数据
- 自动填充表单
- 简单的图形用户界面

## 依赖项
- Python 3.x
- pandas
- pyautogui
- openpyxl
- tkinter

## 安装
1. 安装Python 3.x
2. 安装所需库
    ```sh
    pip install pandas pyautogui openpyxl
    ```

## 使用方法
1. 下载并保存以下代码到本地文件（如 `auto_fill_form.py`）。

```python
import pandas as pd
import pyautogui as pag
import tkinter as tk
from tkinter import filedialog
import time

def browse_file():
    filename = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    data = pd.read_excel(filename)
    global personal_info
    personal_info = data.to_dict('records')[0]
    status_label.config(text="文件加载成功")

def fill_form(info):
    time.sleep(3)  # 给用户时间切换到表单界面
    pag.click(x=100, y=200)  # 点击第一个表单字段（示例坐标）
    pag.write(info['name'])
    pag.press('tab')
    pag.write(info['email'])
    # 继续填写其他字段...

root = tk.Tk()
root.title("自动填表工具")

browse_button = tk.Button(root, text="选择文件", command=browse_file)
browse_button.pack()

fill_button = tk.Button(root, text="开始填表", command=lambda: fill_form(personal_info))
fill_button.pack()

status_label = tk.Label(root, text="")
status_label.pack()

root.mainloop()
```

2. 运行脚本：
    ```sh
    python auto_fill_form.py
    ```
3. 使用图形界面选择包含个人信息的Excel文件，然后点击“开始填表”按钮。

## 注意事项
- 确保Excel文件的字段与代码中的字段匹配。
- 填表前切换到正确的表单界面。
- 根据实际表单位置调整`pag.click(x, y)`中的坐标。

## 贡献
欢迎提出问题和改进建议。您可以通过提交PR来贡献代码。

## 许可证
此项目遵循MIT许可证。详情请参见LICENSE文件。