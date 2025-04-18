# SmartFill.AI Browser Extension

这个浏览器扩展可以自动填充表单字段，特别是在求职申请网站上。当您点击表单字段时，扩展会自动检测字段类型并填入相应的简历信息。

## 功能特点

- **自动检测字段类型**：根据字段标签、属性和上下文自动识别字段类型
- **点击自动填充**：点击输入框时自动填充相应信息
- **支持多种字段**：姓名、邮箱、电话、地址等常见简历字段
- **特别优化Workday**：针对Workday求职平台进行了特别优化

## 安装方法

### 准备图标文件

在安装扩展之前，您需要先生成正确的图标文件：

1. 打开`browser-extension/icons/icon_generator.html`文件在浏览器中
2. 点击页面上的"下载"按钮，下载三个不同尺寸的图标
3. 将下载的图标文件移动到`browser-extension/icons/`目录中，替换现有的占位文件

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

## 使用方法

1. 安装扩展后，访问任何包含表单的网页
2. 点击表单字段（如"Email Address"输入框）
3. 扩展将自动检测字段类型并填入相应信息
4. 如果需要禁用自动填充，可以点击扩展图标并关闭"Auto-fill on focus"选项

## 特别说明

- 此扩展默认使用`profiles/default.json`中的示例数据
- 所有数据处理都在本地完成，不会发送到任何服务器
- 对于Workday等特定网站有特殊优化

## 隐私声明

此扩展不会收集或传输您的个人数据。所有数据处理都在您的浏览器中本地完成。

## 故障排除

如果遇到"Could not load icon 'icons/icon16.png' specified in 'icons'"错误：

1. 确保您已经按照"准备图标文件"部分的说明生成了正确的图标文件
2. 检查`browser-extension/icons/`目录中是否包含以下文件：
   - icon16.png
   - icon48.png
   - icon128.png
3. 如果仍然有问题，可以尝试修改manifest.json文件，移除图标相关的配置
