/**
 * SmartFill.AI - Resume Auto-Fill
 * Background script for handling extension functionality
 */

// Listen for installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('SmartFill.AI extension installed');

  // Check if we have any stored user data
  chrome.storage.sync.get(['userName', 'userEmail', 'userPhone'], function(result) {
    console.log('Initial stored user data:', result);
  });
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'getResumeData') {
    console.log('Received getResumeData request');

    // Load user data from storage
    chrome.storage.sync.get(['userName', 'userEmail', 'userPhone'], function(result) {
      console.log('Retrieved user data from storage:', result);

      const name = result.userName || '李明华'; // Default if not set
      const email = result.userEmail || 'example@email.com'; // Default if not set
      const phone = result.userPhone || '13800138000'; // Default if not set

      console.log('Using data for response:', { name, email, phone });

      // Return resume data with user's custom data
      sendResponse({
        success: true,
        data: {
          "basic": {
            "name": name,
            "gender": "男",
            "birth_year": "1992",
            "email": email,
            "phone": phone,
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
          ]
        }
      });
    });
    return true; // Keep the message channel open for async response
  }
});
