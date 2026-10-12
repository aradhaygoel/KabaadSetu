# ♻️ KabaadSetu (कबाड़सेतु)
### Bringing the Informal Collector into the Formal Recycling Chain

KabaadSetu is a vernacular, low-literacy, mobile-first web platform connecting informal scrap dealers and waste-pickers with local Micro-Hub collection points and CPCB-authorized industrial recyclers.

---

## 🚀 Quick Start & How to Run

Open **[https://kabaadsetu.onrender.com](http://kabaadsetu.onrender.com)** in any modern web browser (Google Chrome, Edge, Safari, or mobile browser).

## 🌟 Key Features & Implementation Highlights

### 1. Vernacular & Voice Engine
- **4 Languages**: 
  - 🟠 **मराठी (Marathi)**
  - 🟢 **हिंदी (Hindi)**
  - 🔵 **తెలుగు (Telugu)**
  - ⚪ **English**
- **Native Browser Audio (TTS)**: Spoken rate board ("भाव ऐका"), spoken estimated lot valuation, spoken 4-digit OTP, and audio passbook summaries.

### 2. Comprehensive Material Catalog & Dynamic Units
- Supports both **`per kg`** and **`per piece / नग / పీస్`**:
  - **E-Waste**: Motherboards / PCBs, Lithium-Ion Batteries, CRT TVs / Monitors, Mixed Cables & Wires, Motors & Transformers.
  - **Metals**: Pure Copper (तांबे/రాగి), Yellow Brass (पितळ/ఇత్తడి), Aluminium, Iron & Steel (लोखंड/ఇనుము).
  - **Paper & Cardboard**: Old Newspaper (रद्दी/వార్తాపత్రికలు), Corrugated Cardboard (पुठ्ठा/అట్టపెట్టెలు).
  - **Plastics**: PET Plastic Bottles, Rigid/Hard Plastic (Buckets/Crates).

### 3. Real Camera Capture & Instant Valuation
- Native in-app camera shutter with instant photo preview and server storage.
- Real-time calculator: `Quantity × Current Mandi Bhav = Estimated Fair Value` with spoken voice readout.

### 4. 2-Tier Hub-and-Spoke Logistics
- **Tier 1 (Collector ➔ Neighborhood Micro-Hub)**: Informal collectors drop scrap at a nearby collection point (e.g. Kothrud Ward Hub, Kukatpally Hub, Dharavi Hub), minimizing travel expenses.
- **Tier 2 (Micro-Hub ➔ Authorized Recycler)**: Scrap is pooled at the Micro-Hub. Once inventory reaches batch capacity, the industrial recycler sends a bulk logistics vehicle ("log picker") to transport the aggregated scrap to the formal plant.

### 5. Secure 4-Digit Handover OTP
- Upon lot submission, the collector's screen displays a high-contrast 4-digit OTP (e.g. `5829`).
- The Micro-Hub operator enters the OTP and the certified scale weight into their terminal to confirm the physical intake, record the cash payment, and update the ledger.

### 6. Earnings Passbook (Khata)
- Passbook format showing green positive credits, cash/UPI indicators, and running earnings totals.
- Audio button to hear the total verified earnings in the selected language.

### 7. Health & Safety Advisory
- Visual and audio guidance warning against hazardous practices:
  - ❌ No open burning of cables (prevents toxic fumes).
  - ❌ No battery crushing/puncturing (prevents thermal runaway and fires).
  - ❌ No CRT tube smashing (prevents implosions and lead phosphor dust).
  - ❌ No crude acid leaching on PCBs.
  - ✅ Proper segregation in dry containers.

### 8. End-to-End CPCB EPR Traceability Manifest
- Traceable chain of custody linking the informal collection point to certified scale measurements, transit vehicles, and the final recycling plant with formal **CPCB EPR Manifest numbers**.

---

## 🗂️ Project Structure

```
e:\KabaadSetu\
  ├── backend\
  │    ├── database.py       # SQLite database initialization & 7 seed datasets
  │    └── main.py           # FastAPI REST API endpoints
  ├── static\
  │    ├── css\
  │    │    └── styles.css   # Responsive vernacular styles
  │    ├── js\
  │    │    ├── translations.js # Multilingual dictionary (mr, hi, te, en)
  │    │    ├── audio.js        # Web Speech API TTS engine
  │    │    └── app.js          # Interactive frontend controller
  │    └── index.html        # Unified single-page interface
  ├── data\
  │    ├── kabaadsetu.db     # SQLite database
  │    └── uploads\          # Saved camera images & scale proofs
  ├── run_server.py          # Server launch script
  ├── test_flow.py           # End-to-end integration test
  └── README.md
```
