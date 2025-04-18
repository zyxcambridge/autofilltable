/**
 * SmartFill.AI - Resume Auto-Fill
 * Popup script for handling extension UI
 */

document.addEventListener('DOMContentLoaded', function() {
  // Get UI elements
  const autoFillToggle = document.getElementById('autoFillToggle');
  const editProfileBtn = document.getElementById('editProfileBtn');
  
  // Load settings
  chrome.storage.sync.get(['autoFill'], function(result) {
    if (result.autoFill !== undefined) {
      autoFillToggle.checked = result.autoFill;
    }
  });
  
  // Save settings when toggle changes
  autoFillToggle.addEventListener('change', function() {
    chrome.storage.sync.set({ autoFill: autoFillToggle.checked });
    
    // Send message to content script to update settings
    chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, { 
          action: 'updateSettings',
          settings: { autoFill: autoFillToggle.checked }
        });
      }
    });
  });
  
  // Handle edit profile button
  editProfileBtn.addEventListener('click', function() {
    // Open options page or a profile editor
    chrome.runtime.openOptionsPage();
  });
});
