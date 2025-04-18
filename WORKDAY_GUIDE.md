# Using SmartFill.AI with Workday Job Applications

This guide will help you use the SmartFill.AI service to automatically fill in job application forms on Workday.

## Prerequisites

1. Make sure you have installed the SmartFill.AI service using the `install_service.sh` script
2. Ensure your profile data in `profiles/default.json` is up to date
3. Grant accessibility permissions to the service when prompted

## Using the Service with Workday Forms

### Method 1: Select Field Label Text

1. Open the Workday job application form in your browser
2. For each field you want to fill:
   - Select the field label text (e.g., "First Name", "Email", "Phone")
   - Right-click on the selected text
   - Choose "Services > SmartFill Resume Info" from the context menu
   - The service will automatically identify the field type and insert the appropriate information

### Method 2: Type Field Name and Select

If Method 1 doesn't work (sometimes field labels can't be selected):

1. Click in the form field you want to fill
2. Type the name of the field (e.g., "First Name", "Email", "Phone")
3. Select the text you just typed
4. Right-click and choose "Services > SmartFill Resume Info"
5. The service will replace your typed text with the appropriate information
6. You may need to delete any extra text that was not replaced

## Supported Field Types

The service can recognize and fill the following field types in Workday forms:

- First Name / 名字
- Last Name / 姓氏
- Email / 邮箱
- Phone / 电话
- Address / 地址
- City / 城市
- State/Province / 省份
- Postal Code / 邮编
- Country / 国家
- LinkedIn Profile
- Website / 网站
- Education / 教育经历
- Work Experience / 工作经验
- Skills / 技能

## Troubleshooting

If the service doesn't work:

1. **Check Accessibility Permissions**: Go to System Preferences > Security & Privacy > Privacy > Accessibility and make sure your browser and Automator have permissions.

2. **Try Different Selection**: Sometimes the field label might include hidden characters. Try selecting just part of the label or typing the field name yourself.

3. **Manual Entry**: If the service still doesn't work for a particular field, you can always enter the information manually.

4. **Restart Services**: Run the following command in Terminal to restart the Services menu:
   ```
   /System/Library/CoreServices/pbs -flush
   ```

5. **Check Logs**: Look for error messages in the Terminal output when using the service.

## Advanced: Customizing Field Recognition

If you need to customize how fields are recognized, you can edit the `web_form_bridge.py` file and modify the `analyze_field_type` function to add more field type patterns.
