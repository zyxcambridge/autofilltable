# SmartFill.AI 浏览器扩展安装指南

## 图标问题解决方案

如果您在安装扩展时遇到"Could not load icon 'icons/icon16.png' specified in 'icons'"错误，请按照以下步骤操作：

### 方法1：生成正确的图标文件

1. 打开`browser-extension/icons/icon_generator.html`文件在浏览器中
2. 点击页面上的"下载"按钮，下载三个不同尺寸的图标
3. 将下载的图标文件移动到`browser-extension/icons/`目录中，替换现有的占位文件

### 方法2：使用简化版的manifest.json

如果方法1不起作用，您可以使用不包含图标配置的简化版manifest.json文件：

1. 将`manifest_simple.json`重命名为`manifest.json`（先备份原始文件）：
   ```
   mv manifest.json manifest.json.bak
   mv manifest_simple.json manifest.json
   ```

2. 然后尝试重新安装扩展

## 完整安装步骤

### Chrome浏览器

1. 打开Chrome浏览器，访问扩展页面：`chrome://extensions/`
2. 开启右上角的"开发者模式"
3. 点击"加载已解压的扩展程序"
4. 选择`browser-extension`文件夹
5. 扩展将被安装并显示在工具栏中

### Firefox浏览器

1. 打开Firefox浏览器，访问`about:debugging#/runtime/this-firefox`
2. 点击"临时载入附加组件"
3. 选择`browser-extension/manifest.json`文件
4. 扩展将被临时安装

## 验证安装

安装成功后：

1. 您应该能在浏览器工具栏中看到扩展图标
2. 点击图标应该会显示扩展的弹出窗口
3. 访问任何包含表单的网页，点击表单字段应该会自动填充相应信息

## 常见问题

### 扩展无法加载

- 确保您已经开启了"开发者模式"
- 检查manifest.json文件是否格式正确
- 尝试使用简化版的manifest.json文件

### 自动填充不工作

- 确保扩展已正确安装
- 检查浏览器控制台是否有错误信息
- 尝试重新加载页面
- 确保您点击的是支持的表单字段类型
