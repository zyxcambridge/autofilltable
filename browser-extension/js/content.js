/**
 * SmartFill.AI - Resume Auto-Fill
 * Content script for automatically filling in resume information
 */

// Resume data (loaded from profiles/default.json)
let resumeData = {
  "basic": {
    "name": "李明华",
    "gender": "男",
    "birth_year": "1992",
    "email": "example@email.com",
    "phone": "13800138000",
    "location": "Beijing"
  },
  "education": [
    {
      "period": "2011.09-2015.06",
      "school": "Sample University",
      "degree": "Bachelor",
      "major": "Computer Science"
    }
  ],
  "work_experience": [
    {
      "company": "示例科技（北京）有限公司",
      "period": "2023.03-2024.01",
      "title": "Machine Learning Engineer",
      "highlights": [
        "参与自动驾驶感知算法开发与优化",
        "负责模型选型与评估，完成多种模型的benchmark测试",
        "设计并实现模型部署流程，提高团队工作效率30%"
      ]
    }
  ],
  "skills": {
    "ai_frameworks": ["PyTorch", "TensorFlow", "Hugging Face", "LangChain", "ONNX"],
    "hardware": ["GPU(V100,A100)", "FPGA(基础应用)", "边缘计算设备"],
    "certifications": ["人工智能工程师认证"],
    "achievements": ["主持技术分享会20场，累计参与人数超过5000人"]
  }
};

// Field type detection patterns
const fieldPatterns = {
  "email": {
    patterns: ["email", "e-mail", "邮箱", "电子邮件", "邮件"],
    getValue: () => resumeData.basic.email
  },
  "password": {
    patterns: ["password", "密码", "pwd"],
    getValue: () => "YourSecurePassword123!" // 示例密码
  },
  "name": {
    patterns: ["name", "full name", "姓名", "全名"],
    getValue: () => resumeData.basic.name
  },
  "first_name": {
    patterns: ["first name", "given name", "名字"],
    getValue: () => {
      const fullName = resumeData.basic.name;
      // 对于中文名，通常姓氏是第一个字
      if (/[\u4e00-\u9fff]/.test(fullName)) {
        return fullName.substring(1);
      }
      // 对于英文名，取第一个空格前的部分
      return fullName.split(' ')[0];
    }
  },
  "last_name": {
    patterns: ["last name", "family name", "surname", "姓氏"],
    getValue: () => {
      const fullName = resumeData.basic.name;
      // 对于中文名，通常姓氏是第一个字
      if (/[\u4e00-\u9fff]/.test(fullName)) {
        return fullName.substring(0, 1);
      }
      // 对于英文名，取最后一个空格后的部分
      const parts = fullName.split(' ');
      return parts[parts.length - 1];
    }
  },
  "phone": {
    patterns: ["phone", "telephone", "mobile", "cell", "电话", "手机", "联系方式"],
    getValue: () => resumeData.basic.phone
  },
  "address": {
    patterns: ["address", "street", "地址", "街道", "住址"],
    getValue: () => resumeData.basic.location
  },
  "city": {
    patterns: ["city", "城市"],
    getValue: () => {
      const location = resumeData.basic.location;
      return location.split(',')[0] || location;
    }
  },
  "state": {
    patterns: ["state", "province", "省", "州"],
    getValue: () => "Beijing" // 示例值
  },
  "zip": {
    patterns: ["zip", "postal", "邮编", "邮政编码"],
    getValue: () => "100000" // 示例值
  },
  "country": {
    patterns: ["country", "国家"],
    getValue: () => "China"
  },
  "education": {
    patterns: ["education", "school", "university", "college", "学历", "教育", "学校"],
    getValue: () => {
      const edu = resumeData.education[0];
      return `${edu.school}, ${edu.degree} in ${edu.major} (${edu.period})`;
    }
  },
  "work": {
    patterns: ["work", "experience", "employment", "job", "工作", "经验", "职业"],
    getValue: () => {
      const work = resumeData.work_experience[0];
      return `${work.title} at ${work.company} (${work.period})`;
    }
  },
  "skills": {
    patterns: ["skills", "abilities", "技能", "能力"],
    getValue: () => resumeData.skills.ai_frameworks.join(", ")
  }
};

// Detect field type based on field attributes and surrounding text
function detectFieldType(element) {
  // Get field attributes
  const id = element.id ? element.id.toLowerCase() : "";
  const name = element.name ? element.name.toLowerCase() : "";
  const placeholder = element.placeholder ? element.placeholder.toLowerCase() : "";
  const ariaLabel = element.getAttribute("aria-label") ? element.getAttribute("aria-label").toLowerCase() : "";
  const type = element.type ? element.type.toLowerCase() : "";

  // Get label text if there's a label associated with this field
  let labelText = "";

  // Check for explicit label
  const labelElement = document.querySelector(`label[for="${element.id}"]`);
  if (labelElement) {
    labelText = labelElement.textContent.toLowerCase();
  }

  // Check for parent label
  if (!labelText && element.closest('label')) {
    labelText = element.closest('label').textContent.toLowerCase();
  }

  // Check for preceding text
  if (!labelText) {
    // Look for text nodes or elements that might be labels
    const previousElement = element.previousElementSibling;
    if (previousElement && !previousElement.querySelector('input, select, textarea')) {
      labelText = previousElement.textContent.toLowerCase();
    }
  }

  // Check for nearby headings or divs that might contain field labels
  if (!labelText) {
    const nearbyElements = element.parentElement.querySelectorAll('h1, h2, h3, h4, h5, h6, div, span, p');
    for (const nearby of nearbyElements) {
      if (nearby !== element &&
          !nearby.querySelector('input, select, textarea') &&
          nearby.textContent.length < 50) {
        labelText = nearby.textContent.toLowerCase();
        break;
      }
    }
  }

  // Combine all text for matching
  const allText = `${id} ${name} ${placeholder} ${labelText} ${ariaLabel} ${type}`;

  // Check for special cases
  if (type === "email") {
    return "email";
  }

  if (type === "password") {
    return "password";
  }

  if (type === "tel") {
    return "phone";
  }

  // Check against patterns
  for (const [fieldType, fieldInfo] of Object.entries(fieldPatterns)) {
    for (const pattern of fieldInfo.patterns) {
      if (allText.includes(pattern)) {
        console.log(`Detected field type: ${fieldType} for element:`, element);
        return fieldType;
      }
    }
  }

  // Special case for Workday forms
  if (window.location.hostname.includes("workday")) {
    // Workday often has specific patterns in their form structure
    const workdayFieldMap = {
      "email": ["email", "e-mail"],
      "password": ["password", "create password", "new password"],
      "verify_password": ["verify", "confirm", "re-enter"]
    };

    for (const [fieldType, patterns] of Object.entries(workdayFieldMap)) {
      for (const pattern of patterns) {
        if (allText.includes(pattern)) {
          console.log(`Detected Workday field type: ${fieldType} for element:`, element);
          return fieldType;
        }
      }
    }
  }

  return null;
}

// Fill field with appropriate value
function fillField(element, fieldType) {
  if (!fieldType || !fieldPatterns[fieldType]) {
    console.log("Unknown field type:", fieldType);
    return;
  }

  const value = fieldPatterns[fieldType].getValue();
  if (!value) {
    console.log(`No value available for field type: ${fieldType}`);
    return;
  }

  // Set the value
  element.value = value;

  // Trigger input event to notify the form that the value has changed
  element.dispatchEvent(new Event('input', { bubbles: true }));
  element.dispatchEvent(new Event('change', { bubbles: true }));

  console.log(`Filled ${fieldType} with: ${value}`);
}

// Handle field focus
function handleFieldFocus(event) {
  const element = event.target;

  // Only process input elements, textareas, and select elements
  if (element.tagName !== 'INPUT' && element.tagName !== 'TEXTAREA' && element.tagName !== 'SELECT') {
    return;
  }

  // Skip if the element already has a value
  if (element.value) {
    return;
  }

  // Detect field type
  const fieldType = detectFieldType(element);
  if (fieldType) {
    // Fill the field
    fillField(element, fieldType);
  }
}

// Handle field click (alternative to focus)
function handleFieldClick(event) {
  const element = event.target;

  // Only process input elements, textareas, and select elements
  if (element.tagName !== 'INPUT' && element.tagName !== 'TEXTAREA' && element.tagName !== 'SELECT') {
    return;
  }

  // Skip if the element already has a value
  if (element.value) {
    return;
  }

  // Detect field type
  const fieldType = detectFieldType(element);
  if (fieldType) {
    // Fill the field
    fillField(element, fieldType);
  }
}

// Initialize the extension
function initialize() {
  console.log("SmartFill.AI - Resume Auto-Fill initialized");
  console.log("Current resume data:", resumeData);

  // Expose resumeData for debugging
  window._smartfillResumeData = resumeData;

  // Load user data from storage
  if (chrome && chrome.storage && chrome.storage.sync) {
    chrome.storage.sync.get(['userName', 'userEmail', 'userPhone'], function(result) {
      console.log('Loaded user data from storage:', result);

      // Update resumeData with user data
      if (result.userName) {
        resumeData.basic.name = result.userName;
      }

      if (result.userEmail) {
        resumeData.basic.email = result.userEmail;
      }

      if (result.userPhone) {
        resumeData.basic.phone = result.userPhone;
      }

      console.log('Updated resume data:', resumeData);

      // Update exposed resumeData for debugging
      window._smartfillResumeData = resumeData;
    });
  } else {
    console.warn('Chrome storage API not available');
  }

  // Add event listeners for focus and click events
  document.addEventListener('focus', handleFieldFocus, true);
  document.addEventListener('click', handleFieldClick, true);

  // Process all visible form fields on page load
  setTimeout(() => {
    console.log('Processing form fields with data:', resumeData);
    const formFields = document.querySelectorAll('input, textarea, select');
    formFields.forEach(field => {
      if (!field.value && field.offsetParent !== null) { // Check if visible
        const fieldType = detectFieldType(field);
        if (fieldType) {
          console.log(`Auto-filling field type ${fieldType} with:`, fieldPatterns[fieldType].getValue());
          fillField(field, fieldType);
        }
      }
    });
  }, 2000); // Wait 2 seconds for the page to fully load and data to be updated
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'updateProfile') {
    console.log('Received profile update:', message);

    // Update user data if provided
    if (message.userData) {
      // Update name if provided
      if (message.userData.name) {
        resumeData.basic.name = message.userData.name;
        console.log('Updated name to:', resumeData.basic.name);
      }

      // Update email if provided
      if (message.userData.email) {
        resumeData.basic.email = message.userData.email;
        console.log('Updated email to:', resumeData.basic.email);
      }

      // Update phone number if provided
      if (message.userData.phone) {
        resumeData.basic.phone = message.userData.phone;
        console.log('Updated phone number to:', resumeData.basic.phone);
      }

      // Update exposed resumeData for debugging
      window._smartfillResumeData = resumeData;
    }

    // Send response
    sendResponse({ success: true });
  }
  return true; // Keep the message channel open for async response
});

// Start the extension
initialize();
