/**
 * SmartFill.AI - Resume Auto-Fill
 * Popup script for handling extension UI
 */

document.addEventListener('DOMContentLoaded', function() {
  // Get UI elements
  const autoFillToggle = document.getElementById('autoFillToggle');
  const nameInput = document.getElementById('nameInput');
  const emailInput = document.getElementById('emailInput');
  const phoneInput = document.getElementById('phoneInput');
  const saveProfileBtn = document.getElementById('saveProfileBtn');

  // Load settings and user data
  chrome.storage.sync.get(['autoFill', 'userName', 'userEmail', 'userPhone'], function(result) {
    if (result.autoFill !== undefined) {
      autoFillToggle.checked = result.autoFill;
    }

    if (result.userName) {
      nameInput.value = result.userName;
    }

    if (result.userEmail) {
      emailInput.value = result.userEmail;
    }

    if (result.userPhone) {
      phoneInput.value = result.userPhone;
    }
  });

  // Save settings when toggle changes
  autoFillToggle.addEventListener('change', function() {
    chrome.storage.sync.set({ autoFill: autoFillToggle.checked });

    // Send message to content script to update settings
    updateContentScript();
  });

  // Handle save profile button
  saveProfileBtn.addEventListener('click', function() {
    const name = nameInput.value.trim();
    const email = emailInput.value.trim();
    const phone = phoneInput.value.trim();

    // Validate inputs (simple validation)
    if (!name) {
      alert('Please enter a valid name');
      return;
    }

    if (!email || !email.includes('@')) {
      alert('Please enter a valid email address');
      return;
    }

    if (!phone) {
      alert('Please enter a valid phone number');
      return;
    }

    // Save user data to storage
    console.log('Saving user data:', { name, email, phone });
    chrome.storage.sync.set({
      userName: name,
      userEmail: email,
      userPhone: phone
    }, function() {
      // Verify data was saved correctly
      chrome.storage.sync.get(['userName', 'userEmail', 'userPhone'], function(result) {
        console.log('Verified saved data:', result);
      });
      // Show success message
      const saveBtn = document.getElementById('saveProfileBtn');
      const originalText = saveBtn.textContent;

      saveBtn.textContent = 'Saved!';
      saveBtn.style.backgroundColor = '#28a745';

      setTimeout(function() {
        saveBtn.textContent = originalText;
        saveBtn.style.backgroundColor = '#4a6baf';
      }, 1500);

      // Update content script with new data
      updateContentScript();
    });
  });

  // Function to update content script with current settings and data
  function updateContentScript() {
    chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, {
          action: 'updateProfile',
          settings: {
            autoFill: autoFillToggle.checked
          },
          userData: {
            name: nameInput.value.trim(),
            email: emailInput.value.trim(),
            phone: phoneInput.value.trim()
          }
        });
      }
    });
  }

  // Handle reset data button
  const resetDataBtn = document.getElementById('resetDataBtn');
  if (resetDataBtn) {
    resetDataBtn.addEventListener('click', function() {
      if (confirm('Are you sure you want to reset all data to defaults?')) {
        // Clear storage
        chrome.storage.sync.clear(function() {
          console.log('Storage cleared');

          // Reset input fields to defaults
          nameInput.value = '李明华';
          emailInput.value = 'example@email.com';
          phoneInput.value = '13800138000';

          // Show success message
          alert('Data has been reset to defaults');

          // Update content script
          updateContentScript();
        });
      }
    });
  }

  // Handle reload page button
  const reloadPageBtn = document.getElementById('reloadPageBtn');
  if (reloadPageBtn) {
    reloadPageBtn.addEventListener('click', function() {
      chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
        if (tabs[0]) {
          chrome.tabs.reload(tabs[0].id);
        }
      });
    });
  }

  // Handle debug button
  const debugBtn = document.getElementById('debugBtn');
  if (debugBtn) {
    debugBtn.addEventListener('click', function() {
      chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
        if (tabs[0]) {
          chrome.tabs.sendMessage(tabs[0].id, { action: 'showDebugPanel' });
        }
      });
    });
  }
});
