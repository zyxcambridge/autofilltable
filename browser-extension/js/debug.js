/**
 * SmartFill.AI - Resume Auto-Fill
 * Debug script for troubleshooting
 */

// Function to inject debug panel into the page
function injectDebugPanel() {
  // Create debug panel
  const debugPanel = document.createElement('div');
  debugPanel.id = 'smartfill-debug-panel';
  debugPanel.style.cssText = `
    position: fixed;
    bottom: 10px;
    right: 10px;
    width: 300px;
    max-height: 400px;
    overflow-y: auto;
    background-color: rgba(0, 0, 0, 0.8);
    color: #fff;
    padding: 10px;
    border-radius: 5px;
    font-family: monospace;
    font-size: 12px;
    z-index: 9999;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
  `;
  
  // Add title
  const title = document.createElement('h3');
  title.textContent = 'SmartFill.AI Debug';
  title.style.cssText = 'margin: 0 0 10px 0; color: #4a6baf;';
  debugPanel.appendChild(title);
  
  // Add close button
  const closeButton = document.createElement('button');
  closeButton.textContent = 'Close';
  closeButton.style.cssText = 'position: absolute; top: 10px; right: 10px; padding: 2px 5px;';
  closeButton.addEventListener('click', function() {
    document.body.removeChild(debugPanel);
  });
  debugPanel.appendChild(closeButton);
  
  // Add content container
  const content = document.createElement('div');
  content.id = 'smartfill-debug-content';
  debugPanel.appendChild(content);
  
  // Add to page
  document.body.appendChild(debugPanel);
  
  // Update debug info
  updateDebugInfo();
}

// Function to update debug info
function updateDebugInfo() {
  const content = document.getElementById('smartfill-debug-content');
  if (!content) return;
  
  // Clear content
  content.innerHTML = '';
  
  // Add section for storage data
  const storageSection = document.createElement('div');
  storageSection.innerHTML = '<h4>Storage Data:</h4>';
  content.appendChild(storageSection);
  
  // Get storage data
  chrome.storage.sync.get(['userName', 'userEmail', 'userPhone', 'autoFill'], function(result) {
    const storageData = document.createElement('pre');
    storageData.textContent = JSON.stringify(result, null, 2);
    storageSection.appendChild(storageData);
  });
  
  // Add section for resume data
  const resumeSection = document.createElement('div');
  resumeSection.innerHTML = '<h4>Current Resume Data:</h4>';
  content.appendChild(resumeSection);
  
  // Get resume data from content script
  const resumeData = window.resumeData || { basic: { name: 'Not available', email: 'Not available', phone: 'Not available' } };
  const resumeDataElem = document.createElement('pre');
  resumeDataElem.textContent = JSON.stringify(resumeData.basic, null, 2);
  resumeSection.appendChild(resumeDataElem);
  
  // Add refresh button
  const refreshButton = document.createElement('button');
  refreshButton.textContent = 'Refresh Data';
  refreshButton.style.cssText = 'margin-top: 10px; padding: 5px 10px;';
  refreshButton.addEventListener('click', updateDebugInfo);
  content.appendChild(refreshButton);
}

// Inject debug panel when requested
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'showDebugPanel') {
    injectDebugPanel();
    sendResponse({ success: true });
  }
  return true;
});

// Export window.resumeData for debugging
if (typeof window.resumeData === 'undefined') {
  Object.defineProperty(window, 'resumeData', {
    get: function() {
      return window._smartfillResumeData || { basic: { name: 'Not available', email: 'Not available', phone: 'Not available' } };
    },
    set: function(value) {
      window._smartfillResumeData = value;
      console.log('resumeData updated:', value);
    },
    enumerable: true,
    configurable: true
  });
}
