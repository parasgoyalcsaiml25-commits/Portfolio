/**
 * AI Resume Portfolio Generator - Frontend Controller (Multi-Template Support)
 * ============================================================================
 * Handles PDF, TXT and image resume upload, text extraction, validation,
 * Template selection (Simple vs Designer), FormData API communication with Flask backend,
 * live 8-step progress workflow, instant template switching, and result presentation.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Dynamic API Base URL: When hosted (HTTP/HTTPS e.g. Vercel or local Flask), uses same-origin relative URLs.
  // When running standalone via local file:// protocol, falls back to http://127.0.0.1:5000.
  const API_BASE = (window.location.protocol === 'http:' || window.location.protocol === 'https:')
    ? ''
    : 'http://127.0.0.1:5000';

  // DOM Elements - File Input & Browse Controls
  const browseBtn = document.getElementById('browseBtn');
  const resumeFile = document.getElementById('resumeFile');
  const dropZone = document.getElementById('dropZone');
  const resumeSelectedBox = document.getElementById('resumeSelectedBox');
  const fileNameEl = document.getElementById('fileName');
  const charCountDisplay = document.getElementById('charCountDisplay');
  const changeFileBtn = document.getElementById('changeFileBtn');
  const generateBtn = document.getElementById('generateBtn');

  // DOM Elements - Template / Customization
  const templateCards = Array.from(document.querySelectorAll('#templateCardsGrid .template-card'));
  const modalTemplateCards = Array.from(document.querySelectorAll('[data-modal-template]'));
  const profileImageFile = document.getElementById('profileImageFile');
  const uploadPhotoBtn = document.getElementById('uploadPhotoBtn');
  const removeProfilePhotoBtn = document.getElementById('removeProfilePhotoBtn');
  const profilePhotoPreviewWrap = document.getElementById('profilePhotoPreviewWrap');
  const profilePhotoPreview = document.getElementById('profilePhotoPreview');
  const themeSwatches = Array.from(document.querySelectorAll('.theme-swatch'));
  const customAccentColor = document.getElementById('customAccentColor');
  const customAccentHex = document.getElementById('customAccentHex');
  const autoStyleBtn = document.getElementById('autoStyleBtn');
  const autoStyleNote = document.getElementById('autoStyleNote');
  const enhanceContent = document.getElementById('enhanceContent');
  const overrideName = document.getElementById('overrideName');
  const overrideHeadline = document.getElementById('overrideHeadline');
  const overrideEmail = document.getElementById('overrideEmail');
  const overridePhone = document.getElementById('overridePhone');
  const overrideLinkedin = document.getElementById('overrideLinkedin');
  const overrideGithub = document.getElementById('overrideGithub');
  const overrideSummary = document.getElementById('overrideSummary');
  const missingInfoHint = document.getElementById('missingInfoHint');

  // DOM Elements - Optional Paste Controls
  const pasteToggleBtn = document.getElementById('pasteToggleBtn');
  const pasteDrawer = document.getElementById('pasteDrawer');
  const rawTextarea = document.getElementById('rawTextarea');
  const usePastedTextBtn = document.getElementById('usePastedTextBtn');

  // DOM Elements - Cards & Screens
  const uploadCard = document.getElementById('uploadCard');
  const progressCard = document.getElementById('progressCard');
  const resultCard = document.getElementById('resultCard');

  // DOM Elements - Result Screen
  const resultCandidateName = document.getElementById('resultCandidateName');
  const resultResumeFileName = document.getElementById('resultResumeFileName');
  const resultTemplateDisplay = document.getElementById('resultTemplateDisplay');
  const statSkills = document.getElementById('statSkills');
  const statProjects = document.getElementById('statProjects');
  const statEducation = document.getElementById('statEducation');
  const statExperience = document.getElementById('statExperience');
  const viewPortfolioBtn = document.getElementById('viewPortfolioBtn');
  const downloadPortfolioBtn = document.getElementById('downloadPortfolioBtn');
  const downloadZipBtn = document.getElementById('downloadZipBtn');
  const savePdfBtn = document.getElementById('savePdfBtn');
  const downloadToast = document.getElementById('downloadToast');
  const changeTemplateBtn = document.getElementById('changeTemplateBtn');
  const generateAgainBtn = document.getElementById('generateAgainBtn');
  const viewJsonBtn = document.getElementById('viewJsonBtn');

  // DOM Elements - Change Template Modal
  const changeTemplateModal = document.getElementById('changeTemplateModal');
  const closeSwitchModalBtn = document.getElementById('closeSwitchModalBtn');
  const closeModalSwitchBtn = document.getElementById('closeModalSwitchBtn');
  const modalTemplateSimple = document.getElementById('modalTemplateSimple');
  const modalTemplateDesigner = document.getElementById('modalTemplateDesigner');
  const modalSelectSimpleBtn = document.getElementById('modalSelectSimpleBtn');
  const modalSelectDesignerBtn = document.getElementById('modalSelectDesignerBtn');
  const applyTemplateSwitchBtn = document.getElementById('applyTemplateSwitchBtn');

  // DOM Elements - Alerts & JSON Modal
  const errorAlert = document.getElementById('errorAlert');
  const errorAlertTitle = document.getElementById('errorAlertTitle');
  const errorAlertText = document.getElementById('errorAlertText');
  const closeAlertBtn = document.getElementById('closeAlertBtn');
  const jsonModal = document.getElementById('jsonModal');
  const closeJsonModalBtn = document.getElementById('closeJsonModalBtn');
  const closeModalActionBtn = document.getElementById('closeModalActionBtn');
  const copyJsonBtn = document.getElementById('copyJsonBtn');
  const jsonContent = document.getElementById('jsonContent');

  // DOM Elements - Backend Health & Connectivity
  const backendStatusPill = document.getElementById('backendStatusPill');
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');
  const backendOfflineBanner = document.getElementById('backendOfflineBanner');
  const backendOfflineTitle = document.getElementById('backendOfflineTitle');
  const backendOfflineText = document.getElementById('backendOfflineText');
  const retryBackendBtn = document.getElementById('retryBackendBtn');

    // --------------------------------------------------------------------------
  // Theme Toggle - Light / Dark Mode
  // --------------------------------------------------------------------------

  const themeToggle = document.getElementById('themeToggle');
  const themeIcon = document.getElementById('themeIcon');
  const themeLabel = document.getElementById('themeLabel');

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);

    const isLight = theme === 'light';

    if (themeIcon) {
      themeIcon.textContent = isLight ? '🌙' : '☀️';
    }

    if (themeLabel) {
      themeLabel.textContent = isLight ? 'Dark' : 'Light';
    }

    if (themeToggle) {
      themeToggle.setAttribute(
        'aria-label',
        isLight ? 'Switch to dark mode' : 'Switch to light mode'
      );
    }

    localStorage.setItem('resume-generator-theme', theme);
  }

  // Restore previously selected theme
  const savedTheme = localStorage.getItem('resume-generator-theme');

  applyTheme(savedTheme === 'light' ? 'light' : 'dark');

  // Toggle theme
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const currentTheme =
        document.documentElement.getAttribute('data-theme') || 'dark';

      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

      applyTheme(newTheme);
    });
  }
  // State Variables
  let extractedResumeText = "";
  let selectedFile = null;
  let currentFileName = "";
  let selectedTemplate = "simple";
  let modalSelectedTemplate = "simple";
  let selectedThemeColor = "#06b6d4";
  let profileImageData = "";
  let currentExtractedData = null;
  let isBackendOnline = false;
  let isCheckingHealth = false;
  let isGenerating = false;

  // --------------------------------------------------------------------------
  // 1. Backend Health Check & Auto-Wait Management
  // --------------------------------------------------------------------------
  function updateBackendStatusUI(state, text) {
    if (backendStatusPill) {
      backendStatusPill.className = `backend-status-pill ${state}`;
    }
    if (statusDot) {
      statusDot.className = `status-indicator-dot ${state}`;
    }
    if (statusText) {
      statusText.textContent = text;
    }
  }

  async function checkBackendHealth(silent = false) {
    if (isCheckingHealth) return isBackendOnline;
    isCheckingHealth = true;

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3500);

      const res = await fetch(`${API_BASE}/health`, {
        method: 'GET',
        cache: 'no-store',
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (res.ok) {
        isBackendOnline = true;
        updateBackendStatusUI('connected', 'Backend Active');
        if (backendOfflineBanner) backendOfflineBanner.style.display = 'none';
        return true;
      } else {
        throw new Error(`Health check returned HTTP ${res.status}`);
      }
    } catch (err) {
      isBackendOnline = false;
      updateBackendStatusUI('disconnected', 'Backend Offline');
      if (!silent && backendOfflineBanner) {
        backendOfflineBanner.className = 'backend-offline-banner error-state';
        if (backendOfflineTitle) backendOfflineTitle.textContent = 'Backend Server Offline';
        if (backendOfflineText) {
          backendOfflineText.textContent = window.location.protocol.startsWith('http')
            ? 'Backend server is not responding. Please check your deployment logs or refresh the page.'
            : 'Flask backend at http://127.0.0.1:5000 is not reachable. Run start.bat or start main.py to reconnect.';
        }
        backendOfflineBanner.style.display = 'flex';
      }
      return false;
    } finally {
      isCheckingHealth = false;
    }
  }

  async function waitForBackendReady(maxWaitMs = 6000, intervalMs = 600) {
    const startTime = Date.now();
    updateBackendStatusUI('connecting', 'Connecting...');
    if (backendOfflineBanner) {
      backendOfflineBanner.className = 'backend-offline-banner';
      if (backendOfflineTitle) backendOfflineTitle.textContent = 'Connecting to Backend...';
      if (backendOfflineText) backendOfflineText.textContent = 'Waiting for backend server to become ready...';
      backendOfflineBanner.style.display = 'flex';
    }

    while (Date.now() - startTime < maxWaitMs) {
      const ready = await checkBackendHealth(true);
      if (ready) {
        if (backendOfflineBanner) backendOfflineBanner.style.display = 'none';
        return true;
      }
      await delay(intervalMs);
    }
    return await checkBackendHealth(false);
  }

  if (retryBackendBtn) {
    retryBackendBtn.addEventListener('click', async () => {
      retryBackendBtn.disabled = true;
      retryBackendBtn.textContent = 'Checking...';
      updateBackendStatusUI('connecting', 'Connecting...');
      const ready = await checkBackendHealth(false);
      if (ready && backendOfflineBanner) {
        backendOfflineBanner.style.display = 'none';
      }
      retryBackendBtn.disabled = false;
      retryBackendBtn.textContent = 'Retry Now';
    });
  }

  // Initial backend health check
  checkBackendHealth(false);

  // Periodic health polling every 8s when idle
  setInterval(() => {
    if (!isGenerating && document.visibilityState === 'visible') {
      checkBackendHealth(true);
    }
  }, 8000);

  // --------------------------------------------------------------------------
  // 2. Error & Notification Helpers
  // --------------------------------------------------------------------------
  function showError(msg, title = "Generation Error") {
    console.error(`[Portfolio Generator Error] ${title}:`, msg);
    if (errorAlertTitle) errorAlertTitle.textContent = title;
    if (errorAlertText) errorAlertText.textContent = msg;
    if (errorAlert) {
      errorAlert.style.display = 'flex';
      errorAlert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  function hideError() {
    if (errorAlert) errorAlert.style.display = 'none';
  }

  if (closeAlertBtn) {
    closeAlertBtn.addEventListener('click', hideError);
  }

  function resetFileSelection() {
    resumeFile.value = '';
    rawTextarea.value = '';
    selectedFile = null;
    extractedResumeText = '';
    currentFileName = '';
    dropZone.style.display = 'block';
    resumeSelectedBox.style.display = 'none';
    generateBtn.disabled = true;
  }

  // --------------------------------------------------------------------------
  // 2. Template Selection + Profile Photo + Theme
  // --------------------------------------------------------------------------
  const templateNames = {
    simple: 'Simple Portfolio',
    designer: 'Designer Portfolio',
    developer: 'Developer Portfolio',
    corporate: 'Corporate Portfolio'
  };

  function setMainTemplate(tpl) {
    selectedTemplate = tpl;
    templateCards.forEach(card => card.classList.toggle('active', card.dataset.template === tpl));
  }

  templateCards.forEach(card => {
    card.addEventListener('click', () => setMainTemplate(card.dataset.template));
    const button = card.querySelector('.btn-select-template');
    if (button) button.addEventListener('click', (e) => {
      e.stopPropagation();
      setMainTemplate(card.dataset.template);
    });
  });

  function setAccentColor(color) {
    if (!/^#[0-9a-fA-F]{6}$/.test(color || '')) return false;
    selectedThemeColor = color.toLowerCase();
    themeSwatches.forEach(el => el.classList.toggle('active', el.dataset.color.toLowerCase() === selectedThemeColor));
    if (customAccentColor) customAccentColor.value = selectedThemeColor;
    if (customAccentHex) customAccentHex.value = selectedThemeColor;
    return true;
  }

  if (themeSwatches.length) {
    themeSwatches.forEach(swatch => {
      swatch.addEventListener('click', () => setAccentColor(swatch.dataset.color));
    });
  }
  customAccentColor?.addEventListener('input', () => setAccentColor(customAccentColor.value));
  customAccentHex?.addEventListener('input', () => {
    const value = customAccentHex.value.trim();
    if (/^#[0-9a-fA-F]{6}$/.test(value)) setAccentColor(value);
  });
  customAccentHex?.addEventListener('blur', () => {
    if (!/^#[0-9a-fA-F]{6}$/.test(customAccentHex.value.trim())) customAccentHex.value = selectedThemeColor;
  });

  function autoRecommendStyle(text) {
    const t = (text || '').toLowerCase();
    const score = (words) => words.reduce((n,w) => n + (t.includes(w) ? 1 : 0), 0);
    const tech = score(['python','java','javascript','typescript','react','node','sql','machine learning','tensorflow','pytorch','github','developer','software engineer','data engineer','ai/ml']);
    const creative = score(['figma','ui/ux','graphic design','designer','dribbble','behance','branding','illustrator','photoshop']);
    const corp = score(['manager','management','consultant','finance','operations','sales','business development','strategy','director','executive','mba']);
    let template = 'simple', color = '#10b981', reason = 'Balanced professional profile';
    if (tech >= Math.max(creative, corp, 2)) { template='developer'; color='#06b6d4'; reason='Technical / AI / software profile'; }
    else if (creative >= Math.max(tech, corp, 2)) { template='designer'; color='#f43f5e'; reason='Creative / design profile'; }
    else if (corp >= Math.max(tech, creative, 2)) { template='corporate'; color='#3b82f6'; reason='Business / management profile'; }
    setMainTemplate(template); setAccentColor(color);
    if (autoStyleNote) autoStyleNote.textContent = `Recommended: ${templateNames[template]} + ${color.toUpperCase()} — ${reason}.`;
    return {template,color};
  }
  autoStyleBtn?.addEventListener('click', () => autoRecommendStyle(extractedResumeText));

  function clearProfilePhoto() {
    profileImageData = '';
    if (profileImageFile) profileImageFile.value = '';
    if (profilePhotoPreviewWrap) profilePhotoPreviewWrap.style.display = 'none';
    if (profilePhotoPreview) profilePhotoPreview.removeAttribute('src');
  }

  if (uploadPhotoBtn && profileImageFile) {
    uploadPhotoBtn.addEventListener('click', () => profileImageFile.click());
    profileImageFile.addEventListener('change', () => {
      const file = profileImageFile.files[0];
      if (!file) return;
      if (!/^image\/(jpeg|png|webp)$/.test(file.type) && !/\.(jpe?g|png|webp)$/i.test(file.name)) {
        showError('Please choose a JPG, JPEG, PNG or WEBP image.', 'Invalid Profile Photo');
        clearProfilePhoto();
        return;
      }
      if (file.size > 5 * 1024 * 1024) {
        showError('Profile photo is too large. Maximum size is 5 MB.', 'Profile Photo Too Large');
        clearProfilePhoto();
        return;
      }
      const reader = new FileReader();
      reader.onload = e => {
        profileImageData = e.target.result || '';
        if (profilePhotoPreview) profilePhotoPreview.src = profileImageData;
        if (profilePhotoPreviewWrap) profilePhotoPreviewWrap.style.display = 'flex';
      };
      reader.readAsDataURL(file);
    });
  }
  if (removeProfilePhotoBtn) removeProfilePhotoBtn.addEventListener('click', clearProfilePhoto);

  // --------------------------------------------------------------------------
  // 3. Browse Files & Native File Picker Integration
  // --------------------------------------------------------------------------
  browseBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    resumeFile.click();
  });

  resumeFile.addEventListener('change', () => {
    const file = resumeFile.files[0];
    if (!file) return;
    handleSelectedFile(file);
  });

  // Drag and Drop support
  dropZone.addEventListener('click', () => {
    resumeFile.click();
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.add('drag-over');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove('drag-over');
    });
  });

  dropZone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleSelectedFile(files[0]);
    }
  });

  // --------------------------------------------------------------------------
  // 4. File Extraction & Validation (PDF & TXT Support)
  // --------------------------------------------------------------------------
  async function handleSelectedFile(file) {
    hideError();
    const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB

    if (file.size > MAX_FILE_SIZE) {
      alert("File size must be less than 5 MB.");
      resumeFile.value = "";
      return;
    }

    if (!file) {
      showError('Please select a valid resume file.');
      resetFileSelection();
      return;
    }

    const lowerName = file.name.toLowerCase();
    const isPdf = lowerName.endsWith('.pdf') || file.type === 'application/pdf';
    const isTxt = lowerName.endsWith('.txt') || lowerName.endsWith('.text') || lowerName.endsWith('.md') || file.type.startsWith('text/');
    const isImage = /\.(jpe?g|png|webp)$/i.test(lowerName) || /image\/(jpeg|png|webp)/.test(file.type);

    if (!isPdf && !isTxt && !isImage) {
      showError('Please select a valid resume file (.pdf, .txt, .jpg, .jpeg, .png or .webp).');
      resetFileSelection();
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      showError('File size is too large (maximum 25 MB). Please select a smaller resume file.');
      resetFileSelection();
      return;
    }

    selectedFile = file;
    currentFileName = file.name;

    if (isPdf) {
      // Step A: Try high-performance client-side extraction using PDF.js
      let clientExtractedText = "";
      if (window.pdfjsLib) {
        try {
          if (pdfjsLib.GlobalWorkerOptions) {
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
          }
          const arrayBuffer = await file.arrayBuffer();
          const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
          const pdfDoc = await loadingTask.promise;
          let fullText = '';
          for (let i = 1; i <= pdfDoc.numPages; i++) {
            const page = await pdfDoc.getPage(i);
            const textContent = await page.getTextContent();
            const pageText = textContent.items.map(item => item.str).join(' ');
            fullText += pageText + '\n';
          }
          clientExtractedText = fullText.trim();
        } catch (pdfJsErr) {
          console.warn('PDF.js client extraction encountered an issue, falling back to server extraction:', pdfJsErr);
        }
      }

      if (clientExtractedText && clientExtractedText.length >= 50) {
        extractedResumeText = clientExtractedText;
        displayExtractedReadyState(file.name, extractedResumeText.length);
        return;
      }

      // Step B: Server-side extract fallback via /api/extract
      try {
        const formData = new FormData();
        formData.append('resume', file);

        const res = await fetch(`${API_BASE}/api/extract`, {
          method: 'POST',
          body: formData
        });

        if (res.ok) {
          const data = await res.json();
          if (data.success && data.text && data.text.trim().length >= 50) {
            extractedResumeText = data.text.trim();
            displayExtractedReadyState(file.name, extractedResumeText.length);
            return;
          }
        }
      } catch (err) {
        console.warn('Server-side PDF extract endpoint offline/unreachable:', err);
      }

      // If both client & server failed to extract selectable text
      showError('This PDF does not contain selectable text. Please use a text-based PDF or an image resume.');
      resetFileSelection();

    } else if (isImage) {
      // Image resumes are OCR-extracted by Gemini on the Flask backend.
      try {
        const formData = new FormData();
        formData.append('resume', file);
        const res = await fetch(`${API_BASE}/api/extract`, { method: 'POST', body: formData });
        const data = await res.json().catch(() => ({}));
        if (!res.ok || !data.success || !data.text) {
          throw new Error(data.message || data.error || 'Could not read the resume image.');
        }
        extractedResumeText = data.text.trim();
        if (extractedResumeText.length < 100) {
          throw new Error(`Only ${extractedResumeText.length} characters were detected. Please use a clearer resume image.`);
        }
        displayExtractedReadyState(file.name, extractedResumeText.length);
      } catch (err) {
        showError(err.message || 'Image resume extraction failed.', 'Image Resume Error');
        resetFileSelection();
      }

    } else {
      // Plain text extraction via FileReader
      const reader = new FileReader();

      reader.onload = function(event) {
        const text = (event.target.result || '').trim();

        if (!text) {
          showError('Could not extract enough text from the resume.');
          resetFileSelection();
          return;
        }

        if (text.length < 100) {
          showError(`Could not extract enough text from the resume. (${text.length} characters extracted, minimum 100 required).`);
          resetFileSelection();
          return;
        }

        extractedResumeText = text;
        displayExtractedReadyState(file.name, text.length);
      };

      reader.onerror = function() {
        showError('Resume upload failed.');
        resetFileSelection();
      };

      reader.readAsText(file);
    }
  }

  function displayExtractedReadyState(filename, charCount) {
    fileNameEl.textContent = filename;
    charCountDisplay.textContent = charCount.toLocaleString();

    dropZone.style.display = 'none';
    resumeSelectedBox.style.display = 'block';
    generateBtn.disabled = false;
    autoRecommendStyle(extractedResumeText);
  }

  // Change Selection Button
  changeFileBtn.addEventListener('click', () => {
    resetFileSelection();
    hideError();
  });

  // --------------------------------------------------------------------------
  // 5. Paste Option
  // --------------------------------------------------------------------------
  pasteToggleBtn.addEventListener('click', () => {
    const isHidden = pasteDrawer.style.display === 'none';
    pasteDrawer.style.display = isHidden ? 'block' : 'none';
  });

  usePastedTextBtn.addEventListener('click', () => {
    hideError();
    const text = (rawTextarea.value || '').trim();
    if (!text) {
      showError('Please paste your resume text before clicking "Use This Text".');
      return;
    }

    if (text.length < 100) {
      showError(`Could not extract enough text from the resume. (${text.length} characters provided, minimum 100 required).`);
      return;
    }

    extractedResumeText = text;
    currentFileName = 'Pasted_Resume.txt';
    selectedFile = new File([text], 'Pasted_Resume.txt', { type: 'text/plain' });
    displayExtractedReadyState(currentFileName, text.length);
  });

  // --------------------------------------------------------------------------
  // 6. 8-Step Animated Stepper Workflow
  // --------------------------------------------------------------------------
  const stepIds = ['step1', 'step2', 'step3', 'step4', 'step5', 'step6', 'step7', 'step8'];

  function resetStepper() {
    stepIds.forEach((id, idx) => {
      const el = document.getElementById(id);
      el.className = 'step-row';
      el.querySelector('.step-indicator').innerHTML = `<span class="step-num">${idx + 1}</span>`;
    });
  }

  function setStepActive(idx) {
    const el = document.getElementById(stepIds[idx]);
    if (el) {
      el.className = 'step-row active';
      el.querySelector('.step-indicator').innerHTML = `<span class="step-num">${idx + 1}</span>`;
    }
  }

  function setStepCompleted(idx) {
    const el = document.getElementById(stepIds[idx]);
    if (el) {
      el.className = 'step-row completed';
      el.querySelector('.step-indicator').innerHTML = `✓`;
    }
  }

  const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  // --------------------------------------------------------------------------
  // 7. Generate Portfolio Request (Sending Extracted Resume Text & Template)
  // --------------------------------------------------------------------------
  generateBtn.addEventListener('click', async () => {
    hideError();

    if (!extractedResumeText || extractedResumeText.length < 100) {
      showError('Could not extract enough text from the resume.');
      return;
    }

    // Auto-wait for backend server readiness if it's currently offline / starting
    if (!isBackendOnline) {
      const ready = await waitForBackendReady(6000);
      if (!ready) {
        showError('Flask backend server on http://127.0.0.1:5000 is not responding. Please start the backend using start.bat.', 'Backend Offline');
        return;
      }
    }

    isGenerating = true;

    // Transition to Progress View
    uploadCard.style.display = 'none';
    progressCard.style.display = 'block';
    resetStepper();

    try {
      // Step 1: Resume uploaded
      setStepActive(0);
      await delay(200);
      setStepCompleted(0);

      // Step 2: Resume text extracted
      setStepActive(1);
      await delay(200);
      setStepCompleted(1);

      // Step 3: Resume cleaned
      setStepActive(2);
      await delay(200);
      setStepCompleted(2);

      // Step 4: Sending to Gemini...
      setStepActive(3);
      console.log('[Step 4: Gemini Request Started]', {
        endpoint: `${API_BASE}/api/generate`,
        filename: selectedFile ? selectedFile.name : (currentFileName || "resume.txt"),
        template: selectedTemplate,
        charCount: extractedResumeText.length
      });

      // Construct FormData with extracted resume text, filename, and selected template
      const formData = new FormData();
      formData.append("resume_text", extractedResumeText);
      formData.append("filename", selectedFile ? selectedFile.name : (currentFileName || "resume.txt"));
      formData.append("template", selectedTemplate);
      formData.append("theme_color", selectedThemeColor);
      formData.append("enhance_content", enhanceContent?.checked ? "true" : "false");
      formData.append("profile_overrides", JSON.stringify({
        name: overrideName?.value || '', headline: overrideHeadline?.value || '', summary: overrideSummary?.value || '',
        email: overrideEmail?.value || '', phone: overridePhone?.value || '', linkedin: overrideLinkedin?.value || '', github: overrideGithub?.value || ''
      }));
      if (profileImageData) formData.append("profile_image", profileImageData);
      if (selectedFile) {
        formData.append("resume", selectedFile);
      }

      // Add 45-second timeout controller so UI never hangs indefinitely
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 45000);

      let response;
      try {
        response = await fetch(`${API_BASE}/api/generate`, {
          method: 'POST',
          body: formData,
          signal: controller.signal
        });
      } catch (fetchErr) {
        clearTimeout(timeoutId);
        if (fetchErr.name === 'AbortError') {
          throw new Error('Portfolio generation timed out while waiting for Gemini API response. Please check your network and try again.');
        }
        checkBackendHealth(false);
        throw new Error('Cannot connect to the generator server on http://127.0.0.1:5000. Please start main.py or run start.bat.');
      } finally {
        clearTimeout(timeoutId);
      }

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        const serverMsg = errJson.message || errJson.error;
        console.error('[Step 4: Server returned error status]', response.status, serverMsg);
        if (serverMsg) {
          throw new Error(serverMsg);
        } else if (response.status === 404) {
          throw new Error('API endpoint /api/generate not found. Please verify main.py is running.');
        } else {
          throw new Error(`Server error (${response.status}). Portfolio generation failed.`);
        }
      }

      const resData = await response.json();
      console.log('[Step 4: Gemini Response Successfully Received]', resData);

      if (!resData.success) {
        throw new Error(resData.message || resData.error || 'Portfolio generation failed.');
      }

      // Step 4 Complete
      setStepCompleted(3);

      // Step 5: Generating structured data...
      setStepActive(4);
      await delay(300);
      setStepCompleted(4);

      // Step 6: Validating JSON...
      setStepActive(5);
      await delay(300);
      setStepCompleted(5);

      // Step 7: Applying selected design template...
      setStepActive(6);
      await delay(300);
      setStepCompleted(6);

      // Step 8: Portfolio generated successfully!
      setStepActive(7);
      await delay(250);
      setStepCompleted(7);

      // Display Result Card
      await delay(300);
      showResultCard(resData);

    } catch (err) {
      console.error('[Step 4: Generation Failed]', err);
      progressCard.style.display = 'none';
      uploadCard.style.display = 'block';

      // Preserve existing resume selection and selected template
      if (extractedResumeText && extractedResumeText.length >= 100) {
        displayExtractedReadyState(currentFileName || "resume.txt", extractedResumeText.length);
        setMainTemplate(selectedTemplate);
      }

      let displayMsg = err.message || 'Portfolio generation failed.';
      if (err.name === 'TypeError' && (err.message.includes('fetch') || err.message.includes('NetworkError') || err.message.includes('Failed to fetch'))) {
        displayMsg = 'Cannot connect to the generator server. Please start main.py or run start.bat.';
        checkBackendHealth(false);
      }
      showError(displayMsg, "Generation Error");
    } finally {
      isGenerating = false;
    }
  });

  // --------------------------------------------------------------------------
  // 8. Result Screen Population
  // --------------------------------------------------------------------------
  function showResultCard(res) {
    currentExtractedData = res.data || {};
    const metrics = res.metrics || res.data || {};

    const candidateName = currentExtractedData.name || 'Candidate Portfolio';
    resultCandidateName.textContent = candidateName;
    resultResumeFileName.textContent = currentFileName || 'resume.txt';

    const tplName = res.template_name || templateNames[selectedTemplate] || 'Simple Portfolio';
    resultTemplateDisplay.textContent = tplName;

    statSkills.textContent = (metrics.skills_count !== undefined ? metrics.skills_count : (currentExtractedData.skills || []).length).toString();
    statProjects.textContent = (metrics.projects_count !== undefined ? metrics.projects_count : (currentExtractedData.projects || []).length).toString();
    statEducation.textContent = (metrics.education_count !== undefined ? metrics.education_count : (currentExtractedData.education || []).length).toString();
    statExperience.textContent = (metrics.experience_count !== undefined ? metrics.experience_count : (currentExtractedData.experience || []).length).toString();

    // Cache-busting URL to open freshly generated portfolio.html directly
    viewPortfolioBtn.href = `portfolio.html?t=${Date.now()}`;
    if (missingInfoHint) {
      const missing = res.missing_fields || [];
      missingInfoHint.textContent = missing.length ? `Missing / not detected: ${missing.join(', ')}. You can add them above and regenerate.` : 'Great! Core profile and contact details were detected.';
    }
    if (autoStyleNote && res.recommended_template) {
      autoStyleNote.textContent = `AI recommendation: ${templateNames[res.recommended_template] || res.recommended_template} + ${(res.recommended_color || selectedThemeColor).toUpperCase()}.`;
    }

    progressCard.style.display = 'none';
    resultCard.style.display = 'block';
  }

  // --------------------------------------------------------------------------
  // 9. Download Portfolio Handler
  // --------------------------------------------------------------------------
  let toastTimer = null;
  function showDownloadToast() {
    if (downloadToast) {
      downloadToast.style.display = 'flex';
      void downloadToast.offsetWidth; // Force reflow
      downloadToast.classList.add('show');
      if (toastTimer) clearTimeout(toastTimer);
      toastTimer = setTimeout(() => {
        downloadToast.classList.remove('show');
        setTimeout(() => {
          downloadToast.style.display = 'none';
        }, 350);
      }, 3500);
    }
  }

  if (downloadPortfolioBtn) {
    downloadPortfolioBtn.addEventListener('click', () => {
      // Trigger file download from /api/download without reloading page
      const downloadUrl = `${API_BASE}/api/download?t=${Date.now()}`;
      const tempLink = document.createElement('a');
      tempLink.href = downloadUrl;
      tempLink.setAttribute('download', '');
      document.body.appendChild(tempLink);
      tempLink.click();
      document.body.removeChild(tempLink);

      showDownloadToast();
    });
  }

  if (downloadZipBtn) {
    downloadZipBtn.addEventListener('click', () => {
      const link = document.createElement('a');
      link.href = `${API_BASE}/api/download-zip?t=${Date.now()}`;
      link.setAttribute('download', '');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });
  }

  if (savePdfBtn) {
    savePdfBtn.addEventListener('click', () => {
      const pdfWindow = window.open(`portfolio.html?t=${Date.now()}`, '_blank');
      if (!pdfWindow) {
        showError('Please allow pop-ups for this app, then click Save as PDF again.', 'PDF Export');
        return;
      }
      pdfWindow.addEventListener('load', () => {
        setTimeout(() => pdfWindow.print(), 500);
      });
    });
  }

  // --------------------------------------------------------------------------
  // 10. Change Template Feature (Fast Re-render Without Re-calling Gemini)
  // --------------------------------------------------------------------------
  function setModalTemplate(tpl) {
    modalSelectedTemplate = tpl;
    modalTemplateCards.forEach(card => card.classList.toggle('active', card.dataset.modalTemplate === tpl));
  }

  changeTemplateBtn.addEventListener('click', () => {
    setModalTemplate(selectedTemplate);
    changeTemplateModal.style.display = 'flex';
  });

  function closeTemplateSwitchModal() { changeTemplateModal.style.display = 'none'; }
  closeSwitchModalBtn.addEventListener('click', closeTemplateSwitchModal);
  closeModalSwitchBtn.addEventListener('click', closeTemplateSwitchModal);
  modalTemplateCards.forEach(card => card.addEventListener('click', () => setModalTemplate(card.dataset.modalTemplate)));

  applyTemplateSwitchBtn.addEventListener('click', async () => {
    closeTemplateSwitchModal();
    selectedTemplate = modalSelectedTemplate;
    setMainTemplate(selectedTemplate);

    hideError();
    applyTemplateSwitchBtn.disabled = true;
    applyTemplateSwitchBtn.textContent = 'Applying...';

    try {
      if (!isBackendOnline) {
        const ready = await waitForBackendReady(4000);
        if (!ready) throw new Error('Flask backend server on http://127.0.0.1:5000 is not responding.');
      }

      const payload = {
        template: selectedTemplate,
        resume_text: extractedResumeText,
        filename: currentFileName || "resume.txt",
        parsed_data: currentExtractedData,
        profile_image: profileImageData,
        theme_color: selectedThemeColor
      };

      const response = await fetch(`${API_BASE}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.message || errJson.error || 'Failed to switch template.');
      }
      const resData = await response.json();
      showResultCard(resData);
    } catch (err) {
      showError(err.message || 'Failed to change template.');
    } finally {
      applyTemplateSwitchBtn.disabled = false;
      applyTemplateSwitchBtn.textContent = 'Apply & Regenerate Portfolio';
    }
  });

  // --------------------------------------------------------------------------
  // 10. Generate Another Portfolio (Reset All State)
  // --------------------------------------------------------------------------
  generateAgainBtn.addEventListener('click', () => {
    resetFileSelection();
    clearProfilePhoto();
    selectedThemeColor = "#06b6d4";
    themeSwatches.forEach((el, idx) => el.classList.toggle('active', idx === 0));
    pasteDrawer.style.display = 'none';
    currentExtractedData = null;
    resultCard.style.display = 'none';
    hideError();
    uploadCard.style.display = 'block';
  });

  // --------------------------------------------------------------------------
  // 11. JSON Viewer Modal
  // --------------------------------------------------------------------------
  viewJsonBtn.addEventListener('click', () => {
    if (currentExtractedData) {
      jsonContent.textContent = JSON.stringify(currentExtractedData, null, 2);
    } else {
      jsonContent.textContent = '// No JSON data extracted';
    }
    jsonModal.style.display = 'flex';
  });

  function closeModal() {
    jsonModal.style.display = 'none';
  }

  closeJsonModalBtn.addEventListener('click', closeModal);
  closeModalActionBtn.addEventListener('click', closeModal);
  jsonModal.addEventListener('click', (e) => {
    if (e.target === jsonModal) closeModal();
  });

  copyJsonBtn.addEventListener('click', () => {
    if (currentExtractedData) {
      navigator.clipboard.writeText(JSON.stringify(currentExtractedData, null, 2)).then(() => {
        copyJsonBtn.textContent = 'Copied!';
        setTimeout(() => { copyJsonBtn.textContent = 'Copy JSON'; }, 2000);
      });
    }
  });

});
