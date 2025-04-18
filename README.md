# SmartFill.AI - 智能简历自动填充工具

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-brightgreen)](https://zyxcambridge.github.io/autofilltable/)

[查看项目网站](https://zyxcambridge.github.io/autofilltable/)

## 简介
该工具利用LLM（大语言模型）技术，智能识别表单字段并自动填充个人简历信息。支持通过右键菜单在任意应用程序中快速填充信息，提高求职效率。

## 核心功能
- 通过右键菜单在任意应用中快速填充简历信息
- 智能识别表单字段类型（姓名、邮箱、工作经验等）
- 基于上下文自动生成合适的内容
- 支持多种简历字段（基本信息、教育背景、工作经验、技能等）
- 本地处理个人信息，保护隐私安全

基于您的需求和现有技术方案，以下是利用LLM（大语言模型）在Mac系统中实现右键自动填充简历个人信息的完整设计方案：

---

### 一、技术架构设计
1. **系统层集成**
   - 使用 **Swift + Automator** 开发系统级右键菜单扩展，注册`com.apple.services`实现全局右键菜单支持。
   - 通过 **AppleScript** 或 **JavaScript for Automation** 监听用户选择的文本区域，捕捉光标所在输入框内容。

2. **LLM模型部署**
   - **本地微调模型**：基于开源的ChatGLM-6B或LLaMA架构，使用简历数据集（如岗位描述、个人信息字段）进行微调，使其精准识别“邮箱”“电话”等字段。
   - **上下文理解**：参考网页[3]的上下文融合技术，将当前文本内容与用户个人信息库结合，生成填充建议（如根据“联系”后接空白自动补全邮箱）。

3. **数据安全方案**
   - 个人信息存储采用 **SQLCipher** 加密数据库，密钥通过Mac系统钥匙链管理。
   - 传输过程使用 **HTTPS+SSL Pinning**，避免中间人攻击（适用于云端同步场景）。

---

### 二、核心功能实现
1. **右键触发逻辑**
   ```swift
   // 注册右键菜单服务
   NSSharingService(named: .compose)?.perform(withItems: [selectedText])
   // 调用LLM推理接口
   let result = LLMEngine.predict(context: selectedText, userData: keychainData)
   ```
   *（参考网页[8]的插件调用逻辑）*

2. **字段识别与填充**
   - **LLM输入**：`当前文本片段 + 用户个人信息JSON`
   - **输出示例**：
     ```json
     {"action": "insert", "position": 15, "content": "yonghu@example.com"}
     ```
   - 通过 **NSTextInputClient** 实现光标位置的内容插入。

3. **个性化配置**
   - 用户可在设置界面管理多个身份档案（如求职版、社交版），参考网页[4]的模块化设计。
   - 支持自定义填充规则，例如：“当检测到‘紧急联系人’时，优先填充父母电话”。

---

### 三、开发工具链
| 模块          | 技术选型                 | 参考来源       |
|---------------|--------------------------|---------------|
| 前端交互      | SwiftUI + AppKit         | 网页[6][8]    |
| 模型训练      | LLaMA-Factory微调框架    | 网页[2]       |
| 数据加密      | SQLCipher + AES-256-GCM  | 网页[11]      |
| 自动化脚本    | JXA (JavaScript for Automation) | 网页[6] |

---

### 四、进阶优化方向
1. **跨应用适配**
   - 针对Safari/Chrome浏览器、Pages/Word文档分别编写输入适配器，解决不同应用的DOM结构差异问题。

2. **智能纠错**
   - 集成类似网页[4]的智能纠错功能，当LLM检测到邮箱格式错误时自动提示修正。

3. **语音输入扩展**
   - 参考网页[3]的语音转文本技术，支持语音指令触发填充（如“填入工作邮箱”）。

---

### 五、测试与部署
1. **单元测试用例**
   ```python
   # 测试邮箱识别准确率
   def test_email_detection():
       input_text = "联系方式："
       expected = "yonghu@example.com"
       assert llm_predict(input_text) == expected
   ```
   *（参考网页[2]的测试方法）*

2. **分发方案**
   - 通过 **Homebrew** 提供一键安装：
     `brew install --cask resume-autofill`
   - 上架Mac App Store需启用沙盒机制，限制文件访问权限。

---

此方案综合了LLM的智能识别、系统级集成和安全防护，相比传统填充工具（如网页[5]的POI-TL模板填充）具备上下文感知能力，较网页[4]的在线简历平台更注重本地隐私保护。开发周期预计2-3个月，初期可先实现基础字段填充，后续逐步迭代智能推荐等功能。

## 依赖项
- Python 3.x
- rumps (macOS状态栏应用)
- pyobjc-framework-Quartz (访问 macOS 辅助功能 API)
- openai (集成 OpenAI API)
- keyring (安全存储凭证)
- cryptography (数据加密)

## 安装
1. 安装Python 3.x
2. 安装所需库
    ```sh
    pip install rumps pyobjc-framework-Quartz pyobjc-core openai requests cryptography keyring tk Pillow
    ```
3. 运行安装脚本安装右键菜单服务
    ```sh
    ./install_service.sh
    ```

## 使用方法
1. 在任意应用中选中文本（如表单字段标签）
   - 支持的字段类型：邮箱、电话、姓名、地址、教育经历、工作经验、技能、项目经验、个人简介
   - 支持中文和英文关键词（如“邮箱”或“Email”）
2. 右键点击并选择“Services > SmartFill Resume Info”
3. 系统将自动分析字段类型并填充相应的简历信息
4. 信息将自动插入到光标位置

## 注意事项
- 首次使用时可能需要授予辅助功能权限
- 确保在个人资料中填写了完整的简历信息
- 如果需要使用OpenAI API，请在设置中配置API密钥

## 更新个人资料
个人资料存储在 `profiles/default.json` 文件中，可以直接编辑该文件更新个人信息。文件结构如下：

```json
{
  "version": "1.0",
  "data": {
    "basic": {
      "name": "姓名",
      "gender": "性别",
      "birth_year": "出生年份",
      "email": "邮箱",
      "phone": "电话",
      "location": "所在地"
    },
    "education": [
      {
        "period": "时间段",
        "school": "学校名称",
        "degree": "学位",
        "major": "专业"
      }
    ],
    "work_experience": [
      {
        "company": "公司名称",
        "period": "时间段",
        "title": "职位",
        "highlights": [
          "工作亮点1",
          "工作亮点2"
        ]
      }
    ],
    "skills": {
      "ai_frameworks": ["技能1", "技能2"],
      "hardware": ["硬件技能"],
      "certifications": ["证书"],
      "achievements": ["成就"]
    }
  }
}
```

## 贡献
欢迎提出问题和改进建议。您可以通过提交PR来贡献代码。

## 许可证
此项目遵循MIT许可证。详情请参见LICENSE文件。