document.addEventListener('DOMContentLoaded', function() {
  // Storage keys
  const STORAGE_KEYS = {
    BACKEND_URL_ENCRYPTED: 'backendUrlEncrypted',
    API_KEY_ENCRYPTED: 'apiKeyEncrypted',
    PASSWORD_HASH: 'passwordHash',
    SALT: 'salt'
  };

  // --- ENCRYPTION UTILITIES ---
  async function hashPassword(password, salt) {
    const encoder = new TextEncoder();
    const data = encoder.encode(password + salt);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    return bufferToHex(hashBuffer);
  }

  async function deriveKey(password, salt) {
    const encoder = new TextEncoder();
    const keyMaterial = await crypto.subtle.importKey(
      'raw',
      encoder.encode(password),
      { name: 'PBKDF2' },
      false,
      ['deriveKey']
    );
    
    return await crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: encoder.encode(salt),
        iterations: 100000,
        hash: 'SHA-256'
      },
      keyMaterial,
      { name: 'AES-GCM', length: 256 },
      false,
      ['encrypt', 'decrypt']
    );
  }

  async function encryptData(data, password, salt) {
    const encoder = new TextEncoder();
    const key = await deriveKey(password, salt);
    const iv = crypto.getRandomValues(new Uint8Array(12));
    
    const encryptedBuffer = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv: iv },
      key,
      encoder.encode(data)
    );
    
    // Combine IV and encrypted data
    const combined = new Uint8Array(iv.length + encryptedBuffer.byteLength);
    combined.set(iv);
    combined.set(new Uint8Array(encryptedBuffer), iv.length);
    
    return bufferToHex(combined);
  }

  async function decryptData(encryptedHex, password, salt) {
    try {
      const combined = hexToBuffer(encryptedHex);
      const iv = combined.slice(0, 12);
      const data = combined.slice(12);
      
      const key = await deriveKey(password, salt);
      
      const decryptedBuffer = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv: iv },
        key,
        data
      );
      
      const decoder = new TextDecoder();
      return decoder.decode(decryptedBuffer);
    } catch (e) {
      throw new Error('Decryption failed - incorrect password');
    }
  }

  function bufferToHex(buffer) {
    return Array.from(new Uint8Array(buffer))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  }

  function hexToBuffer(hex) {
    const bytes = new Uint8Array(hex.length / 2);
    for (let i = 0; i < hex.length; i += 2) {
      bytes[i / 2] = parseInt(hex.substr(i, 2), 16);
    }
    return bytes;
  }

  function generateSalt() {
    return bufferToHex(crypto.getRandomValues(new Uint8Array(16)));
  }

  // --- URL NORMALIZATION ---
  function normalizeBackendUrl(url) {
    // Remove trailing slashes and whitespace
    return url.replace(/\/+$/, '').trim();
  }

  // --- SCREEN MANAGEMENT ---
  function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenId).classList.add('active');
  }

  function setStatus(containerId, state, message) {
    const statusDiv = document.getElementById(containerId);
    statusDiv.innerHTML = message;
    statusDiv.className = state;
  }

  // --- INITIALIZATION ---
  async function checkSetupStatus() {
    chrome.storage.local.get([STORAGE_KEYS.PASSWORD_HASH, STORAGE_KEYS.API_KEY_ENCRYPTED, STORAGE_KEYS.BACKEND_URL_ENCRYPTED, STORAGE_KEYS.SALT], function(result) {
      const hasPassword = result[STORAGE_KEYS.PASSWORD_HASH];
      const hasApiKey = result[STORAGE_KEYS.API_KEY_ENCRYPTED];
      const hasBackendUrl = result[STORAGE_KEYS.BACKEND_URL_ENCRYPTED];
      const hasSalt = result[STORAGE_KEYS.SALT];
      
      // If any required data is missing, clear everything and start fresh
      if (!hasPassword || !hasApiKey || !hasBackendUrl || !hasSalt) {
        chrome.storage.local.clear(function() {
          showScreen('setupScreen');
        });
      } else {
        showScreen('mainScreen');
      }
    });
  }

  // --- SETUP SCREEN ---
  document.getElementById('setupBtn').addEventListener('click', async function() {
    const backendUrl = normalizeBackendUrl(document.getElementById('setupBackendUrl').value.trim());
    const apiKey = document.getElementById('setupApiKey').value.trim();
    const password = document.getElementById('setupPassword').value;
    const passwordConfirm = document.getElementById('setupPasswordConfirm').value;
    
    if (!backendUrl) {
      setStatus('setupStatus', 'error', 'Please enter a backend URL');
      return;
    }
    
    if (!apiKey) {
      setStatus('setupStatus', 'error', 'Please enter an API key');
      return;
    }
    
    if (!password || password.length < 6) {
      setStatus('setupStatus', 'error', 'Password must be at least 6 characters');
      return;
    }
    
    if (password !== passwordConfirm) {
      setStatus('setupStatus', 'error', 'Passwords do not match');
      return;
    }
    
    setStatus('setupStatus', '', 'Verifying server availability...');
    
    try {
      // Verify server is reachable before saving
      const response = await fetch(backendUrl, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) {
        setStatus('setupStatus', 'error', 'Server verification failed: ' + response.status);
        return;
      }
    } catch (error) {
      setStatus('setupStatus', 'error', 'Cannot connect to server: ' + error.message);
      return;
    }
    
    try {
      const salt = generateSalt();
      const passwordHash = await hashPassword(password, salt);
      const encryptedBackendUrl = await encryptData(backendUrl, password, salt);
      const encryptedApiKey = await encryptData(apiKey, password, salt);
      
      chrome.storage.local.set({
        [STORAGE_KEYS.PASSWORD_HASH]: passwordHash,
        [STORAGE_KEYS.BACKEND_URL_ENCRYPTED]: encryptedBackendUrl,
        [STORAGE_KEYS.API_KEY_ENCRYPTED]: encryptedApiKey,
        [STORAGE_KEYS.SALT]: salt
      }, function() {
        setStatus('setupStatus', 'success', 'Setup complete! Redirecting...');
        setTimeout(() => showScreen('mainScreen'), 1000);
      });
    } catch (error) {
      setStatus('setupStatus', 'error', 'Setup failed: ' + error.message);
    }
  });

  // --- MAIN SCREEN ---
  document.getElementById('updateBtn').addEventListener('click', function() {
    showScreen('passwordScreen');
    document.getElementById('passwordInput').value = '';
    document.getElementById('passwordStatus').innerHTML = '';
  });

  document.getElementById('changePasswordBtn').addEventListener('click', function() {
    showScreen('changePasswordScreen');
    document.getElementById('oldPassword').value = '';
    document.getElementById('newPassword').value = '';
    document.getElementById('newPasswordConfirm').value = '';
    document.getElementById('changePasswordStatus').innerHTML = '';
  });

  document.getElementById('updateCredentialsBtn').addEventListener('click', function() {
    showScreen('updateCredentialsScreen');
    document.getElementById('updateBackendUrl').value = '';
    document.getElementById('updateApiKey').value = '';
    document.getElementById('updateCredPassword').value = '';
    document.getElementById('updateCredentialsStatus').innerHTML = '';
  });

  document.getElementById('resetBtn').addEventListener('click', function() {
    showScreen('resetScreen');
    document.getElementById('resetStatus').innerHTML = '';
  });

  // --- PASSWORD SCREEN ---
  document.getElementById('passwordSubmitBtn').addEventListener('click', async function() {
    const password = document.getElementById('passwordInput').value;
    
    if (!password) {
      setStatus('passwordStatus', 'error', 'Please enter your password');
      return;
    }
    
    setStatus('passwordStatus', '', 'Verifying password...');
    
    chrome.storage.local.get([STORAGE_KEYS.PASSWORD_HASH, STORAGE_KEYS.BACKEND_URL_ENCRYPTED, STORAGE_KEYS.API_KEY_ENCRYPTED, STORAGE_KEYS.SALT], async function(result) {
      try {
        const salt = result[STORAGE_KEYS.SALT];
        const storedHash = result[STORAGE_KEYS.PASSWORD_HASH];
        const inputHash = await hashPassword(password, salt);
        
        if (inputHash !== storedHash) {
          setStatus('passwordStatus', 'error', 'Incorrect password');
          return;
        }
        
        // Password is correct, decrypt backend URL and API key, then sync cookies
        const backendUrl = await decryptData(result[STORAGE_KEYS.BACKEND_URL_ENCRYPTED], password, salt);
        const apiKey = await decryptData(result[STORAGE_KEYS.API_KEY_ENCRYPTED], password, salt);
        await syncCookies(backendUrl, apiKey);
        
      } catch (error) {
        setStatus('passwordStatus', 'error', 'Error: ' + error.message);
      }
    });
  });

  document.getElementById('passwordCancelBtn').addEventListener('click', function() {
    showScreen('mainScreen');
  });

  // --- CHANGE PASSWORD SCREEN ---
  document.getElementById('changePasswordSubmitBtn').addEventListener('click', async function() {
    const oldPassword = document.getElementById('oldPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const newPasswordConfirm = document.getElementById('newPasswordConfirm').value;
    
    if (!oldPassword || !newPassword || !newPasswordConfirm) {
      setStatus('changePasswordStatus', 'error', 'All fields are required');
      return;
    }
    
    if (newPassword.length < 6) {
      setStatus('changePasswordStatus', 'error', 'New password must be at least 6 characters');
      return;
    }
    
    if (newPassword !== newPasswordConfirm) {
      setStatus('changePasswordStatus', 'error', 'New passwords do not match');
      return;
    }
    
    setStatus('changePasswordStatus', '', 'Verifying old password...');
    
    chrome.storage.local.get([STORAGE_KEYS.PASSWORD_HASH, STORAGE_KEYS.BACKEND_URL_ENCRYPTED, STORAGE_KEYS.API_KEY_ENCRYPTED, STORAGE_KEYS.SALT], async function(result) {
      try {
        const salt = result[STORAGE_KEYS.SALT];
        const storedHash = result[STORAGE_KEYS.PASSWORD_HASH];
        const oldPasswordHash = await hashPassword(oldPassword, salt);
        
        if (oldPasswordHash !== storedHash) {
          setStatus('changePasswordStatus', 'error', 'Incorrect current password');
          return;
        }
        
        // Decrypt backend URL and API key with old password
        const backendUrl = await decryptData(result[STORAGE_KEYS.BACKEND_URL_ENCRYPTED], oldPassword, salt);
        const apiKey = await decryptData(result[STORAGE_KEYS.API_KEY_ENCRYPTED], oldPassword, salt);
        
        // Generate new salt and encrypt both with new password
        const newSalt = generateSalt();
        const newPasswordHash = await hashPassword(newPassword, newSalt);
        const newEncryptedBackendUrl = await encryptData(backendUrl, newPassword, newSalt);
        const newEncryptedApiKey = await encryptData(apiKey, newPassword, newSalt);
        
        chrome.storage.local.set({
          [STORAGE_KEYS.PASSWORD_HASH]: newPasswordHash,
          [STORAGE_KEYS.BACKEND_URL_ENCRYPTED]: newEncryptedBackendUrl,
          [STORAGE_KEYS.API_KEY_ENCRYPTED]: newEncryptedApiKey,
          [STORAGE_KEYS.SALT]: newSalt
        }, function() {
          setStatus('changePasswordStatus', 'success', 'Password updated successfully!');
          setTimeout(() => showScreen('mainScreen'), 1500);
        });
        
      } catch (error) {
        setStatus('changePasswordStatus', 'error', 'Error: ' + error.message);
      }
    });
  });

  document.getElementById('changePasswordCancelBtn').addEventListener('click', function() {
    showScreen('mainScreen');
  });

  // --- UPDATE CREDENTIALS SCREEN ---
  document.getElementById('updateCredentialsSubmitBtn').addEventListener('click', async function() {
    const newBackendUrl = normalizeBackendUrl(document.getElementById('updateBackendUrl').value.trim());
    const newApiKey = document.getElementById('updateApiKey').value.trim();
    const password = document.getElementById('updateCredPassword').value;
    
    if (!password) {
      setStatus('updateCredentialsStatus', 'error', 'Please enter your password');
      return;
    }
    
    if (!newBackendUrl && !newApiKey) {
      setStatus('updateCredentialsStatus', 'error', 'Please enter at least one field to update');
      return;
    }
    
    setStatus('updateCredentialsStatus', '', 'Verifying password...');
    
    chrome.storage.local.get([STORAGE_KEYS.PASSWORD_HASH, STORAGE_KEYS.BACKEND_URL_ENCRYPTED, STORAGE_KEYS.API_KEY_ENCRYPTED, STORAGE_KEYS.SALT], async function(result) {
      try {
        const salt = result[STORAGE_KEYS.SALT];
        const storedHash = result[STORAGE_KEYS.PASSWORD_HASH];
        const inputHash = await hashPassword(password, salt);
        
        if (inputHash !== storedHash) {
          setStatus('updateCredentialsStatus', 'error', 'Incorrect password');
          return;
        }
        
        // Password is correct, decrypt current values
        const currentBackendUrl = await decryptData(result[STORAGE_KEYS.BACKEND_URL_ENCRYPTED], password, salt);
        const currentApiKey = await decryptData(result[STORAGE_KEYS.API_KEY_ENCRYPTED], password, salt);
        
        // Use current values if fields are empty
        const finalBackendUrl = newBackendUrl || currentBackendUrl;
        const finalApiKey = newApiKey || currentApiKey;
        
        // Verify server availability if URL changed
        if (newBackendUrl) {
          setStatus('updateCredentialsStatus', '', 'Verifying server availability...');
          try {
            const response = await fetch(finalBackendUrl, {
              method: 'GET',
              headers: { 'Content-Type': 'application/json' }
            });
            
            if (!response.ok) {
              setStatus('updateCredentialsStatus', 'error', 'Server verification failed: ' + response.status);
              return;
            }
          } catch (error) {
            setStatus('updateCredentialsStatus', 'error', 'Cannot connect to server: ' + error.message);
            return;
          }
        }
        
        // Encrypt and save new values
        const encryptedBackendUrl = await encryptData(finalBackendUrl, password, salt);
        const encryptedApiKey = await encryptData(finalApiKey, password, salt);
        
        chrome.storage.local.set({
          [STORAGE_KEYS.BACKEND_URL_ENCRYPTED]: encryptedBackendUrl,
          [STORAGE_KEYS.API_KEY_ENCRYPTED]: encryptedApiKey
        }, function() {
          setStatus('updateCredentialsStatus', 'success', 'Credentials updated successfully!');
          setTimeout(() => showScreen('mainScreen'), 1500);
        });
        
      } catch (error) {
        setStatus('updateCredentialsStatus', 'error', 'Error: ' + error.message);
      }
    });
  });

  document.getElementById('updateCredentialsCancelBtn').addEventListener('click', function() {
    showScreen('mainScreen');
  });

  // --- RESET SCREENS ---
  document.getElementById('resetConfirmBtn').addEventListener('click', function() {
    showScreen('resetPasswordScreen');
    document.getElementById('resetPassword').value = '';
    document.getElementById('resetPasswordStatus').innerHTML = '';
  });

  document.getElementById('resetCancelBtn').addEventListener('click', function() {
    showScreen('mainScreen');
  });

  document.getElementById('resetPasswordSubmitBtn').addEventListener('click', async function() {
    const password = document.getElementById('resetPassword').value;
    
    if (!password) {
      setStatus('resetPasswordStatus', 'error', 'Please enter your password');
      return;
    }
    
    setStatus('resetPasswordStatus', '', 'Verifying password...');
    
    chrome.storage.local.get([STORAGE_KEYS.PASSWORD_HASH, STORAGE_KEYS.SALT], async function(result) {
      try {
        const salt = result[STORAGE_KEYS.SALT];
        const storedHash = result[STORAGE_KEYS.PASSWORD_HASH];
        const inputHash = await hashPassword(password, salt);
        
        if (inputHash !== storedHash) {
          setStatus('resetPasswordStatus', 'error', 'Incorrect password');
          return;
        }
        
        // Password is correct, proceed with reset
        setStatus('resetPasswordStatus', '', 'Resetting extension...');
        
        chrome.storage.local.clear(function() {
          setStatus('resetPasswordStatus', 'success', 'Extension reset successfully!');
          setTimeout(() => {
            showScreen('setupScreen');
          }, 1500);
        });
        
      } catch (error) {
        setStatus('resetPasswordStatus', 'error', 'Error: ' + error.message);
      }
    });
  });

  document.getElementById('resetPasswordCancelBtn').addEventListener('click', function() {
    showScreen('mainScreen');
  });

  // --- COOKIE SYNC FUNCTION ---
  async function syncCookies(backendUrl, apiKey) {
    const loader = document.getElementById('loader');
    const statusDiv = document.getElementById('status');
    
    loader.style.display = 'block';
    setStatus('passwordStatus', '', 'Scanning TradingView cookies...');
    
    chrome.cookies.getAll({ domain: "tradingview.com" }, function(cookies) {
      if (!cookies || cookies.length === 0) {
        loader.style.display = 'none';
        setStatus('passwordStatus', 'error', "No TradingView cookies found. Are you logged in?");
        return;
      }

      console.log(`Found ${cookies.length} cookies. Sending to backend...`);
      
      const payload = {
        source: "extension_secure",
        timestamp: new Date().toISOString(),
        total_count: cookies.length,
        cookies: cookies
      };
      
      fetch(backendUrl + '/update-cookies', {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "X-Admin-Key": apiKey
        },
        body: JSON.stringify(payload)
      })
      .then(response => {
        if (response.ok) {
          return response.json().then(data => {
            loader.style.display = 'none';
            setStatus('status', 'success', `Success: ${data.message || 'Cookies Updated'}`);
            showScreen('mainScreen');
          });
        } else {
          return response.json().then(data => {
            loader.style.display = 'none';
            setStatus('passwordStatus', 'error', `Error ${response.status}: ${data.detail || response.statusText}`);
          }).catch(() => {
            loader.style.display = 'none';
            setStatus('passwordStatus', 'error', `HTTP Error ${response.status}`);
          });
        }
      })
      .catch(err => {
        console.error(err);
        loader.style.display = 'none';
        setStatus('passwordStatus', 'error', "Backend Unreachable. Check URL.");
      });
    });
  }

  // Initialize on load
  checkSetupStatus();
});