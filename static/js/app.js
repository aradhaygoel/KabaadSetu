// KabaadSetu Core Application Controller
// Fully Dynamic Multilingual UI across English, Marathi, Hindi, and Telugu

const App = {
  state: {
    currentRole: 'collector', // 'collector' | 'microhub' | 'recycler' | 'traceability'
    currentLang: 'en',       // Default to 'en' (English) as requested by user
    collectorView: 'rates',  // 'rates' | 'create' | 'passbook' | 'safety'
    currentCity: 'Pune',
    materials: [],
    prices: [],
    microHubs: [],
    recyclers: [],
    collectorProfile: null,
    isCollectorVerified: false,
    authStep: 'phone',       // 'phone' | 'otp' | 'id_card'
    authPhone: '9823144556',
    authName: 'Ramesh Bhai',
    authCity: 'Pune',
    simulatedOtp: '',
    passbookEntries: [],
    selectedMaterialId: null,
    selectedQuantity: 10,
    selectedUnit: 'kg',
    capturedImageBlob: null,
    activeHubId: 'HUB_PUN_01',
    activeRecyclerId: 'REC_ECO_VIDYUT',
    hubInventory: null,
    recyclerBatches: [],
    streamTrack: null,
    categoryFilter: 'all'
  },

  async init() {
    console.log("Initializing KabaadSetu...");
    // Check if collector is already verified/saved in localStorage
    const saved = localStorage.getItem('kabaadsetu_collector');
    if (saved) {
      try {
        this.state.collectorProfile = JSON.parse(saved);
        this.state.isCollectorVerified = true;
      } catch (e) {
        console.error("Failed to parse saved collector:", e);
      }
    }

    this.bindEvents();
    await this.fetchInitialData();
    this.applyTranslations();
    this.renderCurrentView();
  },

  bindEvents() {
    // Top role switcher
    document.querySelectorAll('.role-tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const role = e.currentTarget.dataset.role;
        this.switchRole(role);
      });
    });

    // Language pills
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const lang = e.currentTarget.dataset.lang;
        this.setLanguage(lang);
      });
    });

    // Audio toggle
    const audioToggle = document.getElementById('audio-toggle-btn');
    if (audioToggle) {
      audioToggle.addEventListener('click', () => {
        const active = AudioEngine.toggleAudio();
        const t = this.getTranslation();
        audioToggle.innerHTML = active ? t.audioOn : t.audioOff;
        this.showToast(active ? t.audioToggledOn : t.audioToggledOff);
      });
    }

    // Collector subnav
    document.querySelectorAll('.subnav-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const view = e.currentTarget.dataset.view;
        this.switchCollectorView(view);
      });
    });

    // City Selector
    const citySelector = document.getElementById('city-selector');
    if (citySelector) {
      citySelector.addEventListener('change', (e) => {
        this.state.currentCity = e.target.value;
        this.fetchPrices();
        this.fetchMicroHubs();
      });
    }
  },

  getTranslation() {
    return TRANSLATIONS[this.state.currentLang] || TRANSLATIONS['en'];
  },

  cleanHubName(hubName) {
    if (!hubName) return '';
    // If English, return only the English portion before the parentheses
    if (this.state.currentLang === 'en') {
      return hubName.split('(')[0].trim();
    }
    // If regional language, return full or regional
    return hubName;
  },

  getMaterialName(item) {
    if (!item) return '';
    const langKey = `name_${this.state.currentLang}`;
    return item[langKey] || item.name_en || item.name_mr || '';
  },

  async fetchInitialData() {
    try {
      await Promise.all([
        this.fetchMaterials(),
        this.fetchPrices(),
        this.fetchMicroHubs(),
        this.fetchRecyclers(),
        this.fetchCollectorPassbook('COL-MH-8821')
      ]);
    } catch (err) {
      console.error("Error loading initial data:", err);
    }
  },

  async fetchMaterials() {
    const res = await fetch('/api/materials');
    const data = await res.json();
    this.state.materials = data.materials || [];
    if (this.state.materials.length > 0 && !this.state.selectedMaterialId) {
      this.state.selectedMaterialId = this.state.materials[0].id;
      this.state.selectedUnit = this.state.materials[0].unit;
    }
  },

  async fetchPrices() {
    const res = await fetch(`/api/prices?city=${encodeURIComponent(this.state.currentCity)}`);
    const data = await res.json();
    this.state.prices = data.prices || [];
    if (this.state.collectorView === 'rates' && this.state.currentRole === 'collector') {
      this.renderRates();
    }
  },

  async fetchMicroHubs() {
    const res = await fetch(`/api/micro-hubs?city=${encodeURIComponent(this.state.currentCity)}`);
    const data = await res.json();
    this.state.microHubs = data.micro_hubs || [];
    if (this.state.microHubs.length > 0) {
      this.state.activeHubId = this.state.microHubs[0].id;
    }
    this.populateHubSelects();
  },

  async fetchRecyclers() {
    const res = await fetch('/api/recyclers');
    const data = await res.json();
    this.state.recyclers = data.recyclers || [];
  },

  async fetchCollectorPassbook(collectorId = 'COL-MH-8821') {
    const res = await fetch(`/api/collector/${collectorId}/passbook`);
    const data = await res.json();
    this.state.collectorProfile = data.collector;
    this.state.passbookEntries = data.entries || [];
  },

  setLanguage(lang) {
    this.state.currentLang = lang;
    document.querySelectorAll('.lang-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.lang === lang);
    });
    this.applyTranslations();
    const t = this.getTranslation();
    AudioEngine.speak(t.audioWelcome, lang);
    this.populateHubSelects();
    this.renderCurrentView();
  },

  applyTranslations() {
    const t = this.getTranslation();
    document.documentElement.lang = this.state.currentLang;

    // Header & Brand
    const bTitle = document.getElementById('brand-title-text');
    if (bTitle) bTitle.innerText = t.brandTitle;
    const bBadge = document.getElementById('brand-badge');
    if (bBadge) bBadge.innerText = t.brandBadge;
    const bTag = document.getElementById('brand-tagline');
    if (bTag) bTag.innerText = t.tagline;

    // City Selector Options
    const optPune = document.getElementById('city-opt-pune');
    if (optPune) optPune.innerText = t.cityPune;
    const optHyd = document.getElementById('city-opt-hyderabad');
    if (optHyd) optHyd.innerText = t.cityHyderabad;
    const optMum = document.getElementById('city-opt-mumbai');
    if (optMum) optMum.innerText = t.cityMumbai;

    // Audio toggle button
    const aBtn = document.getElementById('audio-toggle-btn');
    if (aBtn) aBtn.innerHTML = AudioEngine.isAudioEnabled ? t.audioOn : t.audioOff;

    // Role Navigation
    const rColl = document.querySelector('.role-tab-btn[data-role="collector"]');
    if (rColl) rColl.innerHTML = t.navCollector;
    const rHub = document.querySelector('.role-tab-btn[data-role="microhub"]');
    if (rHub) rHub.innerHTML = t.navHub;
    const rRec = document.querySelector('.role-tab-btn[data-role="recycler"]');
    if (rRec) rRec.innerHTML = t.navRecycler;
    const rTra = document.querySelector('.role-tab-btn[data-role="traceability"]');
    if (rTra) rTra.innerHTML = t.navTrace;

    // Subnav labels
    const s1 = document.querySelector('.subnav-btn[data-view="rates"] .subnav-label');
    if (s1) s1.innerText = t.subnavRates;
    const s2 = document.querySelector('.subnav-btn[data-view="create"] .subnav-label');
    if (s2) s2.innerText = t.subnavCreate;
    const s3 = document.querySelector('.subnav-btn[data-view="passbook"] .subnav-label');
    if (s3) s3.innerText = t.subnavPassbook;
    const s4 = document.querySelector('.subnav-btn[data-view="safety"] .subnav-label');
    if (s4) s4.innerText = t.subnavSafety;

    // Modal texts
    const mTitle = document.getElementById('modal-verify-title');
    if (mTitle) mTitle.innerText = t.modalVerifyTitle;
    const mScale = document.getElementById('modal-scale-label');
    if (mScale) mScale.innerText = t.modalScaleWeightLabel;
    const mOtpL = document.getElementById('modal-otp-label');
    if (mOtpL) mOtpL.innerText = t.modalOtpLabel;
    const mOtpH = document.getElementById('modal-otp-helper');
    if (mOtpH) mOtpH.innerText = t.modalOtpHelper;
    const mPayT = document.getElementById('modal-payment-title');
    if (mPayT) mPayT.innerText = t.modalPaymentMethod;
    const mCashT = document.getElementById('modal-cash-text');
    if (mCashT) mCashT.innerText = t.modalCash;
    const mUpiT = document.getElementById('modal-upi-text');
    if (mUpiT) mUpiT.innerText = t.modalUpi;
    const mConfB = document.getElementById('modal-confirm-btn');
    if (mConfB) mConfB.innerText = t.btnConfirmHandover;
  },

  switchRole(role) {
    this.state.currentRole = role;
    document.querySelectorAll('.role-tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.role === role);
    });

    document.querySelectorAll('.view-section').forEach(sec => {
      sec.style.display = 'none';
    });

    const targetSec = document.getElementById(`view-${role}`);
    if (targetSec) {
      targetSec.style.display = 'block';
    }

    if (role === 'microhub') {
      this.loadHubInventory();
    } else if (role === 'recycler') {
      this.loadRecyclerPortal();
    } else if (role === 'traceability') {
      this.loadTraceabilityDefault();
    } else {
      this.renderCurrentView();
    }
  },

  switchCollectorView(view) {
    if (!this.state.isCollectorVerified) {
      this.renderCurrentView();
      return;
    }

    this.state.collectorView = view;
    document.querySelectorAll('.subnav-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.view === view);
    });

    document.querySelectorAll('.collector-screen').forEach(s => {
      s.style.display = 'none';
    });

    const activeScreen = document.getElementById(`collector-screen-${view}`);
    if (activeScreen) {
      activeScreen.style.display = 'block';
    }

    if (view === 'rates') {
      this.renderRates();
    } else if (view === 'create') {
      this.renderLotCreationForm();
    } else if (view === 'passbook') {
      this.renderPassbook();
    } else if (view === 'safety') {
      this.renderSafetyGuide();
    }
  },

  renderCurrentView() {
    if (this.state.currentRole === 'collector') {
      const authBox = document.getElementById('collector-screen-auth');
      const mainBox = document.getElementById('collector-main-workspace');

      if (!this.state.isCollectorVerified) {
        if (authBox) authBox.style.display = 'block';
        if (mainBox) mainBox.style.display = 'none';
        this.renderCollectorAuthScreen();
      } else {
        if (authBox) authBox.style.display = 'none';
        if (mainBox) mainBox.style.display = 'block';
        this.renderCollectorChip();
        this.switchCollectorView(this.state.collectorView);
      }
    } else if (this.state.currentRole === 'microhub') {
      this.loadHubInventory();
    } else if (this.state.currentRole === 'recycler') {
      this.loadRecyclerPortal();
    } else if (this.state.currentRole === 'traceability') {
      this.loadTraceabilityDefault();
    }
  },

  // ----------------- COLLECTOR ONBOARDING & UNIQUE ID -----------------
  renderCollectorAuthScreen() {
    const t = this.getTranslation();
    const container = document.getElementById('collector-screen-auth');
    if (!container) return;

    if (this.state.authStep === 'phone') {
      container.innerHTML = `
        <div class="auth-card">
          <div class="auth-icon-circle">🆔</div>
          <div class="auth-title">${t.authScreenTitle}</div>
          <div class="auth-subtitle">${t.authScreenSub}</div>

          <div class="auth-form-group">
            <label class="auth-label">${t.authPhoneLabel}</label>
            <input type="tel" id="auth-phone-input" class="auth-input" placeholder="${t.authPhonePlaceholder}" value="${this.state.authPhone}">
          </div>

          <div class="auth-form-group">
            <label class="auth-label">${t.authNameLabel}</label>
            <input type="text" id="auth-name-input" class="auth-input" placeholder="${t.authNamePlaceholder}" value="${this.state.authName}">
          </div>

          <div class="auth-form-group">
            <label class="auth-label">${t.authCityLabel}</label>
            <select id="auth-city-select" class="auth-input">
              <option value="Pune" ${this.state.authCity === 'Pune' ? 'selected' : ''}>📍 ${t.cityPune}</option>
              <option value="Hyderabad" ${this.state.authCity === 'Hyderabad' ? 'selected' : ''}>📍 ${t.cityHyderabad}</option>
              <option value="Mumbai" ${this.state.authCity === 'Mumbai' ? 'selected' : ''}>📍 ${t.cityMumbai}</option>
            </select>
          </div>

          <button class="btn-primary-large" id="btn-send-otp" onclick="App.sendCollectorOtp()">
            ${t.btnSendOtp}
          </button>
        </div>
      `;
    } else if (this.state.authStep === 'otp') {
      container.innerHTML = `
        <div class="auth-card">
          <div class="auth-icon-circle">📲</div>
          <div class="auth-title">${t.enterOtpPrompt}</div>
          <div class="auth-subtitle">${t.otpSentBanner} <b>+91 ${this.state.authPhone}</b></div>

          <!-- Realistic Simulated SMS Notification Banner -->
          <div class="sms-sim-banner">
            📩 <b>SMS Notification:</b> Your KabaadSetu Verification OTP is:
            <span class="sms-otp-highlight">${this.state.simulatedOtp}</span>
            <small style="display:block; opacity: 0.9;">(Auto-spoken aloud for low-literacy accessibility)</small>
          </div>

          <div class="auth-otp-row">
            <input type="text" id="auth-otp-code-input" class="auth-input" style="text-align: center; font-size: 1.8rem; font-weight: 900; letter-spacing: 8px; max-width: 220px;" maxlength="4" placeholder="----" value="${this.state.simulatedOtp}">
          </div>

          <button class="btn-primary-large" id="btn-verify-otp" onclick="App.verifyCollectorOtp()">
            ${t.btnVerifyAndRegister}
          </button>

          <div style="margin-top: 14px; display: flex; justify-content: center; gap: 10px; flex-wrap: wrap;">
            <button class="listen-btn" onclick="AudioEngine.speak('${t.otpSentSpoken} ${this.state.simulatedOtp.split('').join(' ')}', '${this.state.currentLang}')">
              🔊 Hear Code Again
            </button>
            <button class="listen-btn" onclick="App.resetAuthStep()">
              ✏️ Change Phone
            </button>
          </div>
        </div>
      `;
    } else if (this.state.authStep === 'id_card') {
      container.innerHTML = `
        <div class="auth-card" style="padding: 20px;">
          <div style="font-size: 2.2rem; margin-bottom: 4px;">🎉</div>
          <div class="auth-title" style="color: #065f46;">${t.idCardTitle}</div>
          
          <!-- Celebratory Digital Scrap Collector ID Card -->
          <div class="collector-id-card">
            <div class="id-card-top">
              <div class="id-card-brand">♻️ ${t.brandTitle}</div>
              <div class="id-card-status">${t.idCardStatus}</div>
            </div>
            <div class="id-card-body">
              <div class="id-avatar-box">👤</div>
              <div class="id-details">
                <div class="id-name">${this.state.collectorProfile.name}</div>
                <div class="id-phone">📞 ${this.state.collectorProfile.phone}</div>
                <div class="id-number-highlight">
                  ${this.state.collectorProfile.id}
                </div>
              </div>
            </div>
            <div class="id-card-footer">
              <span>📍 ${this.state.collectorProfile.city}</span>
              <span>🛡️ CPCB / Formal Recycler Linked</span>
            </div>
          </div>

          <button class="btn-primary-large" onclick="App.proceedToCollectorWorkspace()">
            ${t.btnProceedToApp}
          </button>
        </div>
      `;
    }
  },

  async sendCollectorOtp() {
    const t = this.getTranslation();
    const phoneInput = document.getElementById('auth-phone-input');
    const nameInput = document.getElementById('auth-name-input');
    const citySelect = document.getElementById('auth-city-select');

    const phone = phoneInput ? phoneInput.value.trim() : '';
    const name = nameInput ? nameInput.value.trim() : 'Collector';
    const city = citySelect ? citySelect.value : 'Pune';

    if (!phone || phone.length < 10) {
      alert("Please enter a valid 10-digit mobile phone number!");
      return;
    }

    this.state.authPhone = phone;
    this.state.authName = name;
    this.state.authCity = city;

    try {
      const res = await fetch('/api/collector/send-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, name, city })
      });
      const data = await res.json();

      if (res.ok) {
        this.state.simulatedOtp = data.otp;
        this.state.authStep = 'otp';
        this.renderCollectorAuthScreen();
        // Speak out the OTP code in active language
        AudioEngine.speak(`${t.otpSentSpoken} ${data.otp.split('').join(' ')}`, this.state.currentLang);
        this.showToast("OTP sent to your mobile!");
      }
    } catch (err) {
      console.error(err);
      alert("Error sending OTP. Please try again.");
    }
  },

  async verifyCollectorOtp() {
    const t = this.getTranslation();
    const otpInput = document.getElementById('auth-otp-code-input');
    const otp = otpInput ? otpInput.value.trim() : '';

    if (!otp || otp.length !== 4) {
      alert("Please enter the 4-digit verification code!");
      return;
    }

    try {
      const res = await fetch('/api/collector/verify-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: this.state.authPhone,
          otp: otp,
          name: this.state.authName,
          city: this.state.authCity
        })
      });
      const data = await res.json();

      if (res.ok) {
        this.state.collectorProfile = data.collector;
        this.state.isCollectorVerified = true;
        this.state.authStep = 'id_card';
        localStorage.setItem('kabaadsetu_collector', JSON.stringify(data.collector));
        
        this.renderCollectorAuthScreen();
        AudioEngine.speak(`Welcome ${data.collector.name}. Your scrap collector ID ${data.collector.id} is verified.`, this.state.currentLang);
        this.showToast("Identity verified successfully!");
      } else {
        alert(data.detail || "Invalid OTP code!");
      }
    } catch (err) {
      console.error(err);
      alert("Verification error.");
    }
  },

  resetAuthStep() {
    this.state.authStep = 'phone';
    this.renderCollectorAuthScreen();
  },

  proceedToCollectorWorkspace() {
    const authBox = document.getElementById('collector-screen-auth');
    const mainBox = document.getElementById('collector-main-workspace');

    if (authBox) authBox.style.display = 'none';
    if (mainBox) mainBox.style.display = 'block';

    this.renderCollectorChip();
    this.switchCollectorView('rates');
  },

  renderCollectorChip() {
    const t = this.getTranslation();
    const chipContainer = document.getElementById('collector-header-chip');
    if (!chipContainer || !this.state.collectorProfile) return;

    chipContainer.innerHTML = `
      <div class="collector-chip-left">
        <div class="collector-chip-avatar">👤</div>
        <div class="collector-chip-info">
          <div>${t.collectorChipLabel}: <span class="collector-chip-id">${this.state.collectorProfile.id}</span></div>
          <div class="collector-chip-name">${this.state.collectorProfile.name} • 📞 ${this.state.collectorProfile.phone} (${this.state.collectorProfile.city})</div>
        </div>
      </div>
      <button class="collector-chip-switch" onclick="App.logoutCollector()">${t.btnSwitchUser}</button>
    `;
  },

  logoutCollector() {
    if (confirm("Do you want to switch or register another collector?")) {
      localStorage.removeItem('kabaadsetu_collector');
      this.state.isCollectorVerified = false;
      this.state.collectorProfile = null;
      this.state.authStep = 'phone';
      this.renderCurrentView();
    }
  },

  // ----------------- 1. RATES (MANDI BHAV) -----------------
  renderRates() {
    const t = this.getTranslation();
    const container = document.getElementById('rates-container');
    if (!container) return;

    let filtered = this.state.prices;
    if (this.state.categoryFilter !== 'all') {
      filtered = filtered.filter(p => p.category === this.state.categoryFilter);
    }

    let html = `
      <div class="card-header">
        <div class="card-title">📈 ${t.ratesTitle} (${this.state.currentCity})</div>
        <button class="listen-btn" onclick="App.listenAllRates()">${t.listenRates}</button>
      </div>

      <div class="category-filter-chips">
        <button class="cat-chip ${this.state.categoryFilter === 'all' ? 'active' : ''}" onclick="App.setCategoryFilter('all')">${t.catAll}</button>
        <button class="cat-chip ${this.state.categoryFilter === 'ewaste' ? 'active' : ''}" onclick="App.setCategoryFilter('ewaste')">⚡ ${t.catEwaste}</button>
        <button class="cat-chip ${this.state.categoryFilter === 'metals' ? 'active' : ''}" onclick="App.setCategoryFilter('metals')">🔩 ${t.catMetals}</button>
        <button class="cat-chip ${this.state.categoryFilter === 'paper' ? 'active' : ''}" onclick="App.setCategoryFilter('paper')">📦 ${t.catPaper}</button>
        <button class="cat-chip ${this.state.categoryFilter === 'plastics' ? 'active' : ''}" onclick="App.setCategoryFilter('plastics')">🧴 ${t.catPlastics}</button>
      </div>

      <div class="rates-grid">
    `;

    filtered.forEach(p => {
      const name = this.getMaterialName(p);
      const unitText = p.unit === 'kg' ? t.perKg : t.perPiece;
      const trendIcon = p.trend_direction === 'UP' ? '▲' : (p.trend_direction === 'DOWN' ? '▼' : '▬');

      html += `
        <div class="rate-card">
          <div class="rate-left">
            <div class="rate-icon">${p.icon}</div>
            <div>
              <div class="rate-name">${name}</div>
              <div class="rate-sub">${t.marketRange}: ₹${p.market_min} - ₹${p.market_max}</div>
            </div>
          </div>
          <div class="rate-price">
            <div class="rate-val">₹${p.buying_rate}</div>
            <div class="rate-unit">${unitText}</div>
            <span class="rate-trend trend-${p.trend_direction}">${trendIcon} ${p.trend_percent}%</span>
          </div>
        </div>
      `;
    });

    html += `</div>`;
    container.innerHTML = html;
  },

  setCategoryFilter(cat) {
    this.state.categoryFilter = cat;
    this.renderRates();
  },

  listenAllRates() {
    const t = this.getTranslation();
    AudioEngine.speak(t.audioRatesIntro, this.state.currentLang);
  },

  // ----------------- 2. LOT CREATION WITH REAL CAMERA -----------------
  renderLotCreationForm() {
    const t = this.getTranslation();
    const container = document.getElementById('create-lot-container');
    if (!container) return;

    const currentPriceObj = this.state.prices.find(p => p.material_id === this.state.selectedMaterialId);
    const selectedMat = this.state.materials.find(m => m.id === this.state.selectedMaterialId) || this.state.materials[0];
    const rate = currentPriceObj ? currentPriceObj.buying_rate : (selectedMat ? selectedMat.default_rate : 100);
    const unitText = this.state.selectedUnit === 'kg' ? t.unitKg : t.unitPiece;
    const estTotal = Math.round(this.state.selectedQuantity * rate);

    let html = `
      <div class="card-header">
        <div class="card-title">📝 ${t.createLotTitle}</div>
      </div>

      <!-- Real Camera Box -->
      <div class="camera-box">
        <div class="camera-preview-container" id="camera-preview-box">
          ${this.state.capturedImageBlob ? 
            `<img src="${URL.createObjectURL(this.state.capturedImageBlob)}" alt="Captured Scrap" />` :
            `<div id="camera-placeholder" style="padding: 20px;">
              <div style="font-size: 3rem; margin-bottom: 8px;">📷</div>
              <p style="font-weight: 700;">${t.cameraHeading}</p>
              <p style="font-size: 0.75rem; color: #94a3b8;">${t.cameraSubheading}</p>
            </div>
            <video id="live-webcam-feed" autoplay playsinline style="display:none;"></video>
            <canvas id="photo-canvas" style="display:none;"></canvas>
            `
          }
        </div>

        <div class="camera-actions">
          <label class="cam-btn" for="camera-native-input" style="cursor: pointer;">
            ${t.btnSnap}
          </label>
          <input type="file" id="camera-native-input" accept="image/*" capture="environment" style="display: none;" onchange="App.handleNativeCameraCapture(event)">

          <button type="button" class="cam-btn secondary" id="webcam-toggle-btn" onclick="App.toggleLiveWebcam()">
            ${t.btnWebcam}
          </button>
        </div>
      </div>

      <!-- Material Selector Grid -->
      <p style="font-weight: 700; margin-bottom: 8px;">${t.selectMaterial}</p>
      <div class="material-selector-grid">
    `;

    this.state.materials.forEach(m => {
      const isSelected = m.id === this.state.selectedMaterialId;
      const name = this.getMaterialName(m);
      const pObj = this.state.prices.find(p => p.material_id === m.id);
      const mRate = pObj ? pObj.buying_rate : m.default_rate;

      html += `
        <div class="mat-select-card ${isSelected ? 'selected' : ''}" onclick="App.selectMaterial('${m.id}', '${m.unit}')">
          <div class="mat-select-icon">${m.icon}</div>
          <div class="mat-select-title">${name}</div>
          <div class="mat-select-price">₹${mRate} / ${m.unit === 'kg' ? t.unitKg : t.unitPiece}</div>
        </div>
      `;
    });

    html += `
      </div>

      <!-- Quantity Stepper -->
      <div class="qty-stepper-box">
        <p style="font-weight: 700; text-align: center; margin-bottom: 8px;">
          ${t.declaredQuantity} (${unitText})
        </p>
        <div class="qty-control-row">
          <button class="stepper-btn" onclick="App.adjustQuantity(-5)">−</button>
          <input type="number" class="qty-input" id="qty-input-box" value="${this.state.selectedQuantity}" min="1" max="1000" onchange="App.setManualQuantity(this.value)">
          <button class="stepper-btn" onclick="App.adjustQuantity(5)">+</button>
          <span class="unit-badge">${unitText}</span>
        </div>
        <div class="quick-chips">
          <button class="chip-add" onclick="App.setManualQuantity(5)">5 ${unitText}</button>
          <button class="chip-add" onclick="App.setManualQuantity(10)">10 ${unitText}</button>
          <button class="chip-add" onclick="App.setManualQuantity(25)">25 ${unitText}</button>
          <button class="chip-add" onclick="App.setManualQuantity(50)">50 ${unitText}</button>
        </div>
      </div>

      <!-- Instant Value Banner -->
      <div class="valuation-banner">
        <div>
          <div class="val-label">${t.estValueText}</div>
          <div class="val-amount">₹${estTotal.toLocaleString('en-IN')}</div>
          <div style="font-size: 0.75rem; opacity: 0.85;">(${this.state.selectedQuantity} ${unitText} × ₹${rate})</div>
        </div>
        <button class="val-speaker" onclick="App.listenValuation(${estTotal})">🔊</button>
      </div>

      <!-- Nearest Micro-Hub Selection -->
      <div style="margin-bottom: 16px;">
        <label style="font-weight: 700; font-size: 0.85rem; display: block; margin-bottom: 6px;">
          📍 ${t.selectHub}
        </label>
        <select id="hub-select-dropdown" style="width: 100%; padding: 12px; border-radius: 10px; border: 2px solid var(--gray-300); font-weight: 700; font-size: 0.9rem;">
    `;

    this.state.microHubs.forEach(h => {
      const isSelected = h.id === this.state.activeHubId ? 'selected' : '';
      const hCleanName = this.cleanHubName(h.name);
      html += `<option value="${h.id}" ${isSelected}>${hCleanName} - ${h.address}</option>`;
    });

    html += `
        </select>
      </div>

      <!-- Submit Button -->
      <button class="btn-primary-large" id="btn-submit-lot" onclick="App.submitScrapLot()">
        ${t.btnSubmitLot}
      </button>

      <!-- Container for generated 4-Digit OTP -->
      <div id="otp-container"></div>
    `;

    container.innerHTML = html;
  },

  selectMaterial(matId, unit) {
    this.state.selectedMaterialId = matId;
    this.state.selectedUnit = unit;
    this.renderLotCreationForm();
  },

  adjustQuantity(delta) {
    let newVal = this.state.selectedQuantity + delta;
    if (newVal < 1) newVal = 1;
    this.state.selectedQuantity = newVal;
    this.renderLotCreationForm();
  },

  setManualQuantity(val) {
    let v = parseFloat(val);
    if (isNaN(v) || v < 1) v = 1;
    this.state.selectedQuantity = v;
    this.renderLotCreationForm();
  },

  listenValuation(amount) {
    const t = this.getTranslation();
    const phrase = `${t.estValueText} ${amount} ${this.state.currentLang === 'en' ? 'rupees' : 'रुपये'}.`;
    AudioEngine.speak(phrase, this.state.currentLang);
  },

  handleNativeCameraCapture(event) {
    const t = this.getTranslation();
    const file = event.target.files[0];
    if (file) {
      this.state.capturedImageBlob = file;
      this.showToast(t.photoSavedToast);
      this.renderLotCreationForm();
    }
  },

  async toggleLiveWebcam() {
    const t = this.getTranslation();
    const video = document.getElementById('live-webcam-feed');
    const placeholder = document.getElementById('camera-placeholder');
    const btn = document.getElementById('webcam-toggle-btn');
    if (!video) return;

    if (this.state.streamTrack) {
      const canvas = document.getElementById('photo-canvas');
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      canvas.toBlob((blob) => {
        this.state.capturedImageBlob = blob;
        this.state.streamTrack.stop();
        this.state.streamTrack = null;
        this.renderLotCreationForm();
        this.showToast(t.webcamSavedToast);
      }, 'image/jpeg');

    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        this.state.streamTrack = stream.getVideoTracks()[0];
        video.srcObject = stream;
        video.style.display = 'block';
        if (placeholder) placeholder.style.display = 'none';
        btn.innerHTML = t.btnCaptureFrame;
        btn.classList.add('pulse');
      } catch (err) {
        console.error("Camera access error:", err);
        alert(this.state.currentLang === 'en' ? 
          "Could not open camera. Please check permissions or use 'Take Photo with Camera'." : 
          "कॅमेरा चालू होऊ शकला नाही. कृपया कॅमेरा परवानगी तपासा.");
      }
    }
  },

  async submitScrapLot() {
    const t = this.getTranslation();
    const submitBtn = document.getElementById('btn-submit-lot');
    if (submitBtn) {
      submitBtn.innerText = t.submitting;
      submitBtn.disabled = true;
    }

    const hubDropdown = document.getElementById('hub-select-dropdown');
    const hubId = hubDropdown ? hubDropdown.value : this.state.activeHubId;

    const collectorId = this.state.collectorProfile ? this.state.collectorProfile.id : 'COL-MH-8821';
    const collectorName = this.state.collectorProfile ? this.state.collectorProfile.name : 'Ramesh Bhai';
    const collectorPhone = this.state.collectorProfile ? this.state.collectorProfile.phone : '+91 98231 44556';

    const formData = new FormData();
    formData.append('collector_id', collectorId);
    formData.append('collector_name', collectorName);
    formData.append('collector_phone', collectorPhone);
    formData.append('material_id', this.state.selectedMaterialId);
    formData.append('declared_qty', this.state.selectedQuantity);
    formData.append('unit', this.state.selectedUnit);
    formData.append('micro_hub_id', hubId);
    formData.append('city', this.state.currentCity);

    if (this.state.capturedImageBlob) {
      formData.append('photo', this.state.capturedImageBlob, 'scrap_photo.jpg');
    }

    try {
      const res = await fetch('/api/lots', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();

      if (res.ok) {
        this.showToast(`${t.otpLotId} ${data.lot.id} registered!`);
        this.renderOtpCard(data.lot);
        
        const otpPhrase = `${t.audioLotSuccess} ${data.lot.otp_code.split('').join(' ')}`;
        AudioEngine.speak(otpPhrase, this.state.currentLang);

        this.state.capturedImageBlob = null;
      } else {
        alert("Registration failed: " + (data.detail || "Error"));
      }
    } catch (err) {
      console.error("Submit error:", err);
      alert("Network Error!");
    } finally {
      if (submitBtn) {
        submitBtn.innerText = t.btnSubmitLot;
        submitBtn.disabled = false;
      }
    }
  },

  renderOtpCard(lot) {
    const t = this.getTranslation();
    const container = document.getElementById('otp-container');
    if (!container) return;

    const digits = lot.otp_code.split('');
    const cleanHub = this.cleanHubName(lot.hub_name);

    container.innerHTML = `
      <div class="otp-display-card">
        <div class="otp-title">🎉 ${t.otpHeading}</div>
        <p style="font-size: 0.85rem; font-weight: 700; color: #713f12;">${t.otpLotId}: ${lot.id}</p>
        
        <div class="otp-digits">
          <div class="otp-digit">${digits[0] || '0'}</div>
          <div class="otp-digit">${digits[1] || '0'}</div>
          <div class="otp-digit">${digits[2] || '0'}</div>
          <div class="otp-digit">${digits[3] || '0'}</div>
        </div>

        <p class="otp-helper">${t.otpHelperText}</p>
        <p style="font-size: 0.8rem; margin-top: 8px; color: #475569;">
          ${t.otpHubAddress}: <b>${cleanHub}</b> (${lot.hub_address})
        </p>

        <button class="listen-btn" style="margin-top: 10px;" onclick="AudioEngine.speak('${t.audioLotSuccess} ${digits.join(' ')}', '${this.state.currentLang}')">
          ${t.btnReplayOtp}
        </button>
      </div>
    `;

    container.scrollIntoView({ behavior: 'smooth' });
  },

  // ----------------- 3. PASSBOOK (KHATA) -----------------
  async renderPassbook() {
    const colId = this.state.collectorProfile ? this.state.collectorProfile.id : 'COL-MH-8821';
    await this.fetchCollectorPassbook(colId);
    const t = this.getTranslation();
    const container = document.getElementById('passbook-container');
    if (!container) return;

    const total = this.state.collectorProfile ? this.state.collectorProfile.total_earnings : 0;
    const completedCount = this.state.collectorProfile ? this.state.collectorProfile.total_lots : 0;

    let html = `
      <div class="card-header">
        <div class="card-title">📖 ${t.passbookTitle}</div>
        <button class="listen-btn" onclick="AudioEngine.speak('${t.audioPassbookTotal} ${total}', '${this.state.currentLang}')">
          ${t.btnHearBalance}
        </button>
      </div>

      <div class="passbook-balance-banner">
        <div>
          <div class="pb-label">${t.totalEarningsLabel}</div>
          <div class="pb-total">₹${total.toLocaleString('en-IN')}</div>
          <div style="font-size: 0.75rem; color: #cbd5e1;">${t.completedLotsLabel}: ${completedCount}</div>
        </div>
        <div style="font-size: 2.5rem;">💰</div>
      </div>

      <p style="font-weight: 800; margin-bottom: 10px;">${t.recentTransactions}</p>
    `;

    if (this.state.passbookEntries.length === 0) {
      html += `<p style="text-align: center; color: var(--gray-600); padding: 20px;">${t.noEntries}</p>`;
    } else {
      this.state.passbookEntries.forEach(entry => {
        const isCash = entry.payment_mode === 'CASH';
        const cleanHub = this.cleanHubName(entry.hub_name);
        html += `
          <div class="passbook-item">
            <div>
              <div class="pb-title">${entry.material_summary}</div>
              <div class="pb-meta">📍 ${cleanHub} | 🕒 ${entry.timestamp}</div>
            </div>
            <div>
              <div class="pb-amount">+₹${entry.amount.toLocaleString('en-IN')}</div>
              <div style="text-align: right;">
                <span class="pb-badge">${isCash ? t.cashReceived : t.upiReceived}</span>
              </div>
            </div>
          </div>
        `;
      });
    }

    container.innerHTML = html;
  },

  // ----------------- 4. SAFETY GUIDELINES -----------------
  renderSafetyGuide() {
    const t = this.getTranslation();
    const container = document.getElementById('safety-container');
    if (!container) return;

    let html = `
      <div class="card-header">
        <div class="card-title">🛡️ ${t.safetyHeading}</div>
      </div>

      <div class="safety-alert-banner">
        ⚠️ ${t.safetyWarning}
      </div>

      <div class="safety-grid">
        <div class="safety-card danger">
          <div class="safety-card-title">${t.ruleCableTitle}</div>
          <div class="safety-card-desc">${t.ruleCableDesc}</div>
          <button class="listen-btn" style="margin-top: 8px;" onclick="AudioEngine.speak('${t.ruleCableTitle}. ${t.ruleCableDesc}', '${this.state.currentLang}')">${t.btnHearSafety}</button>
        </div>

        <div class="safety-card danger">
          <div class="safety-card-title">${t.ruleBatteryTitle}</div>
          <div class="safety-card-desc">${t.ruleBatteryDesc}</div>
          <button class="listen-btn" style="margin-top: 8px;" onclick="AudioEngine.speak('${t.ruleBatteryTitle}. ${t.ruleBatteryDesc}', '${this.state.currentLang}')">${t.btnHearSafety}</button>
        </div>

        <div class="safety-card danger">
          <div class="safety-card-title">${t.ruleCrtTitle}</div>
          <div class="safety-card-desc">${t.ruleCrtDesc}</div>
          <button class="listen-btn" style="margin-top: 8px;" onclick="AudioEngine.speak('${t.ruleCrtTitle}. ${t.ruleCrtDesc}', '${this.state.currentLang}')">${t.btnHearSafety}</button>
        </div>

        <div class="safety-card danger">
          <div class="safety-card-title">${t.ruleAcidTitle}</div>
          <div class="safety-card-desc">${t.ruleAcidDesc}</div>
          <button class="listen-btn" style="margin-top: 8px;" onclick="AudioEngine.speak('${t.ruleAcidTitle}. ${t.ruleAcidDesc}', '${this.state.currentLang}')">${t.btnHearSafety}</button>
        </div>
      </div>
    `;

    container.innerHTML = html;
  },

  // ----------------- 5. MICRO-HUB PORTAL -----------------
  async loadHubInventory() {
    const t = this.getTranslation();
    const hubId = this.state.activeHubId;
    const res = await fetch(`/api/micro-hubs/${hubId}/inventory`);
    const data = await res.json();
    this.state.hubInventory = data;

    const pendingRes = await fetch(`/api/lots?micro_hub_id=${hubId}&status=PENDING_DROP`);
    const pendingData = await pendingRes.json();
    const pendingLots = pendingData.lots || [];

    const container = document.getElementById('microhub-content');
    if (!container) return;

    const hub = data.hub;
    const poolKg = hub.current_pool_kg;
    const capKg = hub.capacity_kg;
    const pct = Math.min(100, Math.round((poolKg / capKg) * 100));
    const cleanHub = this.cleanHubName(hub.name);

    let html = `
      <div class="card-header">
        <div class="card-title">🏪 ${cleanHub} (${t.hubDashboardTitle})</div>
        <div>
          <select onchange="App.switchActiveHub(this.value)" style="padding: 6px 12px; border-radius: 8px; font-weight: 700;">
    `;

    this.state.microHubs.forEach(h => {
      const hClean = this.cleanHubName(h.name);
      html += `<option value="${h.id}" ${h.id === hubId ? 'selected' : ''}>${hClean}</option>`;
    });

    html += `
          </select>
        </div>
      </div>

      <!-- Stats Row -->
      <div class="hub-stats-row">
        <div class="stat-box">
          <div class="stat-val">${pendingLots.length}</div>
          <div class="stat-label">${t.statPendingDrops}</div>
        </div>
        <div class="stat-box">
          <div class="stat-val">${poolKg} kg</div>
          <div class="stat-label">${t.statPooledStock}</div>
        </div>
        <div class="stat-box">
          <div class="stat-val">${capKg} kg</div>
          <div class="stat-label">${t.statBatchCapacity}</div>
        </div>
        <div class="stat-box">
          <div class="stat-val">${pct}%</div>
          <div class="stat-label">${t.statBulkReadiness}</div>
        </div>
      </div>

      <!-- Bulk Transport Progress -->
      <div class="card" style="margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; font-weight: 700; font-size: 0.9rem;">
          <span>${t.progressTitle} (${poolKg} / ${capKg} kg)</span>
          <span>${pct}% ${t.progressFilled}</span>
        </div>
        <div class="progress-bar-container">
          <div class="progress-fill" style="width: ${pct}%;"></div>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; flex-wrap: wrap; gap: 10px;">
          <p style="font-size: 0.8rem; color: var(--gray-600); max-width: 600px;">
            ${t.progressHelper}
          </p>
          <button class="btn-primary-large" style="width: auto; padding: 8px 16px; font-size: 0.85rem;" onclick="App.triggerBulkPickupRequest('${hubId}')">
            ${t.btnRequestBulkPickup}
          </button>
        </div>
      </div>

      <!-- Incoming Lots Waiting for 4-Digit OTP & Scale Verification -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">📥 ${t.pendingDropsTitle}</div>
        </div>
    `;

    if (pendingLots.length === 0) {
      html += `<p style="color: var(--gray-600); padding: 10px;">${t.noPendingLots}</p>`;
    } else {
      html += `
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>${t.thLotId}</th>
                <th>${t.thPhoto}</th>
                <th>${t.thCollector}</th>
                <th>${t.thMaterial}</th>
                <th>${t.thQuantity}</th>
                <th>${t.thEstValue}</th>
                <th>${t.thAction}</th>
              </tr>
            </thead>
            <tbody>
      `;

      pendingLots.forEach(lot => {
        const matName = this.getMaterialName(lot);
        html += `
          <tr>
            <td><b>${lot.id}</b></td>
            <td>
              ${lot.photo_path ? 
                `<img src="${lot.photo_path}" style="width: 44px; height: 44px; object-fit: cover; border-radius: 8px;" />` : 
                `<span style="font-size: 1.5rem;">${lot.icon}</span>`}
            </td>
            <td>${lot.collector_name}<br><small style="color:var(--gray-600)">${lot.collector_phone}</small></td>
            <td>${lot.icon} ${matName}</td>
            <td><b>${lot.declared_qty} ${lot.unit === 'kg' ? t.unitKg : t.unitPiece}</b></td>
            <td>₹${lot.est_value}</td>
            <td>
              <button class="cam-btn" style="padding: 6px 12px; font-size: 0.8rem;" onclick="App.openHubVerifyModal('${lot.id}', '${lot.declared_qty}', '${lot.unit}', '${lot.est_value}')">
                ${t.btnWeighAndVerify}
              </button>
            </td>
          </tr>
        `;
      });

      html += `</tbody></table></div>`;
    }

    html += `</div>`;
    container.innerHTML = html;
  },

  switchActiveHub(hubId) {
    this.state.activeHubId = hubId;
    this.loadHubInventory();
  },

  openHubVerifyModal(lotId, declaredQty, unit, estValue) {
    const t = this.getTranslation();
    const modal = document.getElementById('hub-verify-modal');
    if (!modal) return;

    document.getElementById('modal-lot-id').value = lotId;
    document.getElementById('modal-lot-label').innerText = `${t.modalLotLabel}: ${lotId}`;
    const unitLabel = unit === 'kg' ? t.unitKg : t.unitPiece;
    document.getElementById('modal-declared-info').innerText = `${t.modalDeclaredInfo}: ${declaredQty} ${unitLabel} (${t.estValueText} ₹${estValue})`;
    document.getElementById('modal-scale-weight').value = declaredQty;
    document.getElementById('modal-otp-input').value = '';

    modal.style.display = 'flex';
  },

  closeHubVerifyModal() {
    const modal = document.getElementById('hub-verify-modal');
    if (modal) modal.style.display = 'none';
  },

  async confirmHubIntake() {
    const t = this.getTranslation();
    const hubId = this.state.activeHubId;
    const lotId = document.getElementById('modal-lot-id').value;
    const enteredOtp = document.getElementById('modal-otp-input').value.trim();
    const verifiedQty = parseFloat(document.getElementById('modal-scale-weight').value);
    const paymentMode = document.querySelector('input[name="payment-mode-radio"]:checked').value;

    if (!enteredOtp || enteredOtp.length !== 4) {
      alert(t.promptEnterOtp);
      return;
    }

    if (isNaN(verifiedQty) || verifiedQty <= 0) {
      alert(t.promptEnterWeight);
      return;
    }

    const formData = new FormData();
    formData.append('lot_id', lotId);
    formData.append('entered_otp', enteredOtp);
    formData.append('verified_qty', verifiedQty);
    formData.append('payment_mode', paymentMode);

    try {
      const res = await fetch(`/api/micro-hubs/${hubId}/verify-lot`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();

      if (res.ok) {
        alert(`✅ ${t.intakeSuccessToast}\nFinal Payout: ₹${data.final_payout} (${paymentMode})\nCredited to Passbook.`);
        this.closeHubVerifyModal();
        this.loadHubInventory();
      } else {
        alert("Verification failed: " + (data.detail || "Invalid OTP"));
      }
    } catch (err) {
      console.error("Intake verification error:", err);
      alert("Server Error!");
    }
  },

  async triggerBulkPickupRequest(hubId) {
    const t = this.getTranslation();
    if (!confirm(t.confirmBulkRequestPrompt)) {
      return;
    }

    try {
      const res = await fetch(`/api/micro-hubs/${hubId}/request-bulk-pickup`, {
        method: 'POST'
      });
      const data = await res.json();

      if (res.ok) {
        alert(`🚚 ${t.bulkRequestSuccess}\nBatch: ${data.batch_id} (${data.total_weight_kg} kg)`);
        this.loadHubInventory();
      } else {
        alert("Error: " + (data.detail || "Error"));
      }
    } catch (err) {
      console.error("Bulk pickup error:", err);
    }
  },

  // ----------------- 6. AUTHORIZED RECYCLER INDUSTRIAL PORTAL -----------------
  async loadRecyclerPortal() {
    const t = this.getTranslation();
    const res = await fetch('/api/recycler/batches');
    const data = await res.json();
    this.state.recyclerBatches = data.batches || [];

    const container = document.getElementById('recycler-content');
    if (!container) return;

    let html = `
      <div class="card-header">
        <div class="card-title">🏭 ${t.recyclerPortalTitle} (EcoVidyut Recycling)</div>
        <span class="badge badge-verified">${t.recyclerBadge}</span>
      </div>

      <div class="card">
        <div class="card-header">
          <div class="card-title">📦 ${t.batchesFeedTitle}</div>
        </div>
    `;

    if (this.state.recyclerBatches.length === 0) {
      html += `<p style="padding: 10px; color: var(--gray-600);">${t.noBatches}</p>`;
    } else {
      html += `
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>${t.thBatchId}</th>
                <th>${t.thHub}</th>
                <th>${t.thCategory}</th>
                <th>${t.thTotalWeight}</th>
                <th>${t.thStatus}</th>
                <th>${t.thLogistics}</th>
              </tr>
            </thead>
            <tbody>
      `;

      this.state.recyclerBatches.forEach(b => {
        let statusBadge = '';
        let actionBtn = '';
        const cleanHub = this.cleanHubName(b.hub_name);

        if (b.status === 'REQUESTED_PICKUP') {
          statusBadge = `<span class="badge badge-pending">${t.badgePickupRequested}</span>`;
          actionBtn = `<button class="cam-btn" style="padding: 6px 12px; font-size: 0.8rem;" onclick="App.dispatchPickerVehicle('${b.id}')">${t.btnDispatchVehicle}</button>`;
        } else if (b.status === 'LOG_PICKER_DISPATCHED') {
          statusBadge = `<span class="badge badge-transit">${t.badgeDispatched}: ${b.log_picker_vehicle_no}</span>`;
          actionBtn = `<button class="cam-btn" style="background: #047857; padding: 6px 12px; font-size: 0.8rem;" onclick="App.receiveAtFacility('${b.id}')">${t.btnReceiveAtFacility}</button>`;
        } else if (b.status === 'DELIVERED_TO_FACILITY') {
          statusBadge = `<span class="badge badge-recycled">${t.badgeRecycled}: ${b.cpcb_manifest_no}</span>`;
          actionBtn = `<button class="listen-btn" onclick="App.viewTraceability('${b.id}')">${t.btnViewCertificate}</button>`;
        }

        html += `
          <tr>
            <td><b>${b.id}</b></td>
            <td>${cleanHub}<br><small style="color:var(--gray-600)">${b.hub_address}</small></td>
            <td>${b.material_category}</td>
            <td><b>${b.total_weight_kg} kg</b> (${b.lot_count} lots)</td>
            <td>${statusBadge}</td>
            <td>${actionBtn}</td>
          </tr>
        `;
      });

      html += `</tbody></table></div>`;
    }

    html += `</div>`;
    container.innerHTML = html;
  },

  async dispatchPickerVehicle(batchId) {
    const t = this.getTranslation();
    const vehicle = prompt(t.promptVehicleNo, "MH-12-RN-7742");
    if (!vehicle) return;
    const driver = prompt(t.promptDriverName, "Tukaram Shinde");

    try {
      const res = await fetch(`/api/recycler/batches/${batchId}/dispatch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vehicle_no: vehicle, driver_name: driver || "Driver" })
      });
      const data = await res.json();
      if (res.ok) {
        this.showToast(`Logistics Vehicle ${vehicle} dispatched for Batch ${batchId}!`);
        this.loadRecyclerPortal();
      }
    } catch (err) {
      console.error(err);
    }
  },

  async receiveAtFacility(batchId) {
    const t = this.getTranslation();
    if (!confirm(t.confirmReceivePrompt)) {
      return;
    }

    try {
      const res = await fetch(`/api/recycler/batches/${batchId}/receive`, {
        method: 'POST'
      });
      const data = await res.json();
      if (res.ok) {
        alert(`✅ ${t.facilityIntakeSuccess}\nOfficial CPCB EPR Manifest: ${data.cpcb_manifest_no}`);
        this.loadRecyclerPortal();
      }
    } catch (err) {
      console.error(err);
    }
  },

  // ----------------- 7. END-TO-END TRACEABILITY DOSSIER -----------------
  loadTraceabilityDefault() {
    this.viewTraceability('LOT-2026-0891');
  },

  async viewTraceability(identifier) {
    this.switchRole('traceability');
    const t = this.getTranslation();
    const container = document.getElementById('traceability-content');
    if (!container) return;

    try {
      const res = await fetch(`/api/traceability/${identifier}`);
      const data = await res.json();

      let html = `
        <div class="card-header">
          <div class="card-title">📜 ${t.traceTitle}</div>
        </div>

        <div style="margin-bottom: 14px; display: flex; gap: 8px;">
          <input type="text" id="trace-search-input" value="${identifier}" style="flex:1; padding: 10px; border-radius: 8px; border: 1px solid var(--gray-300); font-weight: 700;" placeholder="${t.traceSearchPlaceholder}">
          <button class="cam-btn" onclick="App.viewTraceability(document.getElementById('trace-search-input').value)">${t.btnTrack}</button>
        </div>
      `;

      if (data.type === 'LOT_TRACEABILITY') {
        const lot = data.data;
        const matName = this.getMaterialName(lot);
        const cleanHub = this.cleanHubName(lot.hub_name);
        const unitLabel = lot.unit === 'kg' ? t.unitKg : t.unitPiece;

        html += `
          <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div>
                <h3>${t.otpLotId}: ${lot.id}</h3>
                <p style="color: var(--gray-600); font-size: 0.85rem;">${t.thMaterial}: ${lot.icon} ${matName} (${lot.category})</p>
              </div>
              <span class="badge badge-verified">${lot.status}</span>
            </div>

            <div class="timeline">
              <div class="timeline-step">
                <div class="step-time">${lot.created_at}</div>
                <div class="step-title">${t.step1Title}</div>
                <div class="step-desc">
                  <b>${t.thCollector}:</b> ${lot.collector_name} (${lot.collector_phone})<br>
                  <b>${t.modalDeclaredInfo}:</b> ${lot.declared_qty} ${unitLabel} | <b>${t.estValueText}</b> ₹${lot.est_value}<br>
                  ${t.step1Desc}
                </div>
              </div>

              <div class="timeline-step">
                <div class="step-time">${lot.verified_at || 'Pending'}</div>
                <div class="step-title">${t.step2Title}</div>
                <div class="step-desc">
                  <b>${t.thHub}:</b> ${cleanHub} (${lot.hub_address})<br>
                  <b>${t.modalScaleWeightLabel}:</b> ${lot.verified_qty || lot.declared_qty} ${unitLabel}<br>
                  <b>${t.modalPaymentMethod}:</b> ₹${lot.final_payout || lot.est_value} (${lot.payment_mode || 'CASH'})<br>
                  ${t.step2Desc}
                </div>
              </div>

              <div class="timeline-step">
                <div class="step-time">${lot.dispatched_at || 'In Transit'}</div>
                <div class="step-title">${t.step3Title}</div>
                <div class="step-desc">
                  <b>${t.thBatchId}:</b> ${lot.batch_id || 'BATCH-PUN-001'}<br>
                  <b>Logistics Vehicle:</b> ${lot.log_picker_vehicle_no || 'MH-12-RN-7742'} (${lot.driver_name || 'Tukaram Shinde'})<br>
                  ${t.step3Desc}
                </div>
              </div>

              <div class="timeline-step">
                <div class="step-time">${lot.delivered_at || 'Facility Step'}</div>
                <div class="step-title">${t.step4Title}</div>
                <div class="step-desc">
                  <b>Recycler:</b> ${lot.recycler_name || 'EcoVidyut Industrial Recycling Pvt Ltd'}<br>
                  <b>Facility:</b> ${lot.facility_address || 'MIDC Bhosari Industrial Area, Pune'}<br>
                  <b>CPCB EPR Manifest:</b> <b>${lot.cpcb_manifest_no || 'EPR-MNF-2026-0811'}</b><br>
                  ${t.step4Desc}
                </div>
              </div>
            </div>
          </div>
        `;
      } else if (data.type === 'BATCH_TRACEABILITY') {
        const b = data.batch;
        const cleanHub = this.cleanHubName(b.hub_name);
        html += `
          <div class="card">
            <h3>${t.thBatchId}: ${b.id}</h3>
            <p>${t.thHub}: ${cleanHub} | Recycler: ${b.recycler_name}</p>
            <p>${t.thTotalWeight}: <b>${b.total_weight_kg} kg</b> | ${t.thStatus}: <b>${b.status}</b></p>
            <p>CPCB EPR Manifest: <b>${b.cpcb_manifest_no || 'Pending'}</b></p>
          </div>
        `;
      }

      container.innerHTML = html;
    } catch (err) {
      console.error(err);
    }
  },

  populateHubSelects() {
    const dropdown = document.getElementById('hub-select-dropdown');
    if (!dropdown) return;
    dropdown.innerHTML = this.state.microHubs.map(h => {
      const hClean = this.cleanHubName(h.name);
      return `<option value="${h.id}" ${h.id === this.state.activeHubId ? 'selected' : ''}>${hClean} - ${h.address}</option>`;
    }).join('');
  },

  showToast(msg) {
    const t = document.getElementById('toast');
    if (!t) return;
    t.innerText = msg;
    t.style.display = 'block';
    setTimeout(() => { t.style.display = 'none'; }, 2600);
  }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
