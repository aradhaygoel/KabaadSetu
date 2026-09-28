import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "kabaadsetu.db")
UPLOADS_DIR = os.path.join(DB_DIR, "uploads")

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Materials Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materials (
        id TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        name_en TEXT NOT NULL,
        name_mr TEXT NOT NULL,
        name_hi TEXT NOT NULL,
        name_te TEXT NOT NULL,
        unit TEXT NOT NULL, -- 'kg' or 'piece'
        default_rate REAL NOT NULL,
        icon TEXT NOT NULL,
        hazard_level TEXT NOT NULL, -- 'LOW', 'MEDIUM', 'HIGH'
        safety_tip_key TEXT NOT NULL,
        description_en TEXT,
        description_mr TEXT,
        description_hi TEXT,
        description_te TEXT
    )
    """)

    # 2. Prices Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id TEXT NOT NULL,
        city TEXT NOT NULL,
        buying_rate REAL NOT NULL,
        market_min REAL NOT NULL,
        market_max REAL NOT NULL,
        trend_direction TEXT NOT NULL, -- 'UP', 'DOWN', 'STABLE'
        trend_percent REAL NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (material_id) REFERENCES materials(id)
    )
    """)

    # 3. Micro-Hubs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS micro_hubs (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        address TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        contact_person TEXT NOT NULL,
        phone TEXT NOT NULL,
        capacity_kg REAL NOT NULL,
        current_pool_kg REAL DEFAULT 0.0,
        assigned_recycler_id TEXT NOT NULL
    )
    """)

    # 4. Recyclers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recyclers (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        cpcb_reg TEXT NOT NULL,
        facility_address TEXT NOT NULL,
        city TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        accepted_categories TEXT NOT NULL,
        log_picker_fleet INTEGER NOT NULL,
        active_status TEXT DEFAULT 'ACTIVE',
        contact_phone TEXT NOT NULL
    )
    """)

    # 5. Collectors Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS collectors (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        language TEXT NOT NULL DEFAULT 'mr',
        city TEXT NOT NULL DEFAULT 'Pune',
        total_earnings REAL DEFAULT 0.0,
        total_lots INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """)

    # 6. Lots Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lots (
        id TEXT PRIMARY KEY,
        collector_id TEXT NOT NULL,
        collector_name TEXT NOT NULL,
        collector_phone TEXT NOT NULL,
        material_id TEXT NOT NULL,
        declared_qty REAL NOT NULL,
        unit TEXT NOT NULL,
        est_value REAL NOT NULL,
        micro_hub_id TEXT NOT NULL,
        otp_code TEXT NOT NULL,
        photo_path TEXT,
        status TEXT NOT NULL, -- 'PENDING_DROP', 'VERIFIED_AT_HUB', 'POOLED', 'IN_TRANSIT', 'RECYCLED'
        verified_qty REAL,
        final_payout REAL,
        payment_mode TEXT, -- 'CASH', 'UPI'
        scale_photo_path TEXT,
        created_at TEXT NOT NULL,
        verified_at TEXT,
        pooled_batch_id TEXT,
        FOREIGN KEY (material_id) REFERENCES materials(id),
        FOREIGN KEY (micro_hub_id) REFERENCES micro_hubs(id)
    )
    """)

    # 7. Pooled Batches Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pooled_batches (
        id TEXT PRIMARY KEY,
        micro_hub_id TEXT NOT NULL,
        recycler_id TEXT NOT NULL,
        material_category TEXT NOT NULL,
        total_weight_kg REAL NOT NULL,
        lot_count INTEGER NOT NULL,
        status TEXT NOT NULL, -- 'ACCUMULATING', 'REQUESTED_PICKUP', 'LOG_PICKER_DISPATCHED', 'DELIVERED_TO_FACILITY'
        log_picker_vehicle_no TEXT,
        driver_name TEXT,
        driver_phone TEXT,
        dispatched_at TEXT,
        delivered_at TEXT,
        cpcb_manifest_no TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (micro_hub_id) REFERENCES micro_hubs(id),
        FOREIGN KEY (recycler_id) REFERENCES recyclers(id)
    )
    """)

    # 8. Passbook Ledger Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS passbook_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        collector_id TEXT NOT NULL,
        lot_id TEXT NOT NULL,
        amount REAL NOT NULL,
        payment_mode TEXT NOT NULL,
        material_summary TEXT NOT NULL,
        hub_name TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (collector_id) REFERENCES collectors(id)
    )
    """)

    conn.commit()
    seed_initial_data(conn)
    conn.close()

def seed_initial_data(conn):
    cursor = conn.cursor()

    # Check if materials already exist
    cursor.execute("SELECT COUNT(*) FROM materials")
    if cursor.fetchone()[0] > 0:
        return

    print("Seeding initial datasets for KabaadSetu...")

    # Materials Dataset
    materials_data = [
        # E-WASTE
        ("MAT_PCB_HIGH", "ewaste", "Motherboard / PCB Scrap", "मदरबोर्ड / पीसीबी भंगार", "मदरबोर्ड / पीसीबी स्क्रैप", "మదర్‌బోర్డ్ / పిసిబి స్క్రాప్",
         "kg", 420.0, "💻", "MEDIUM", "SAFE_PCB",
         "High grade computer & telecom printed circuit boards rich in precious metals.",
         "मौल्यवान धातूंनी समृद्ध हाय-ग्रेड कॉम्प्युटर आणि टेलिकॉम पीसीबी.",
         "कीमती धातुओं से भरपूर उच्च श्रेणी के कंप्यूटर और टेलीकॉम पीसीबी।",
         "విలువైన లోహాలతో కూడిన కంప్యూటర్ మరియు టెలికాం పిసిబి బోర్డులు."),

        ("MAT_BAT_LION", "ewaste", "Lithium-Ion Batteries", "लिथियम-आयन बॅटरी", "लिथियम-आयन बैटरी", "లిథియం-అయాన్ బ్యాటరీలు",
         "kg", 130.0, "🔋", "HIGH", "SAFE_BATTERY",
         "Mobile phone and laptop lithium-ion battery packs. Highly flammable.",
         "मोबाईल आणि लॅपटॉप बॅटरी. ज्वलनशील - काळजीपूर्वक हाताळा.",
         "मोबाइल और लैपटॉप की बैटरी। अत्यधिक ज्वलनशील - सावधानी बरतें।",
         "మొబైల్ మరియు ల్యాప్‌టాప్ లిథియం బ్యాటరీలు. మండే స్వభావం కలవి."),

        ("MAT_CRT_TV", "ewaste", "CRT Monitor / TV Tube", "सीआरटी मॉनिटर / टीव्ही", "सीआरटी मॉनिटर / टीवी", "సిఆర్‌టి మానిటర్ / టీవీ",
         "piece", 220.0, "📺", "HIGH", "SAFE_CRT",
         "Intact cathode ray tube television or monitor unit. Contains vacuum and leaded glass.",
         "अखंड सीआरटी टीव्ही किंवा मॉनिटर. शिसे आणि व्हॅक्यूम असल्यामुळे फोडू नका.",
         "साबुत सीआरटी टीवी या मॉनिटर। सीसा और वैक्यूम युक्त - कभी न तोड़ें।",
         "సిఆర్‌టి టీవీ లేదా మానిటర్. సీసం కలిగి ఉంటుంది, పగలగొట్టవద్దు."),

        ("MAT_CABLE_MIX", "ewaste", "Copper Cables & Wires", "तांबे केबल्स आणि वायर्स", "कॉपर केबल्स और तार", "రాగి కేబుల్స్ మరియు వైర్లు",
         "kg", 240.0, "🔌", "HIGH", "SAFE_CABLE",
         "Insulated electronic and power wiring. Do NOT burn - sell with coating.",
         "इन्सुलेटेड तांब्याची वायर. जाळू नका - कोटिंगसह विका आणि योग्य भाव मिळवा.",
         "इन्सुलेटेड तांबे के तार। जलाएं नहीं - कोटिंग सहित बेचें और पूरा भाव पाएं।",
         "ఇన్సులేటెడ్ రాగి వైర్లు. కాల్చవద్దు - పూర్తి కోటింగ్‌తో విక్రయించండి."),

        ("MAT_MOTOR_EW", "ewaste", "Motors & Transformers", "इलेक्ट्रिक मोटर आणि ट्रान्सफॉर्मर", "इलेक्ट्रिक मोटर व ट्रांसफार्मर", "ఎలక్ట్రిక్ మోటార్లు & ట్రాన్స్‌ఫార్మర్లు",
         "kg", 160.0, "⚙️", "LOW", "SAFE_GENERAL",
         "Copper-bearing small motors, fan assemblies and step-down transformers.",
         "तांबे असलेले लहान मोटर्स, फॅन असेंब्ली आणि ट्रान्सफॉर्मर.",
         "तांबे युक्त छोटी मोटर, पंखे की असेंबली और ट्रांसफार्मर।",
         "రాగి ఉండే చిన్న మోటార్లు మరియు ట్రాన్స్‌ఫార్మర్లు."),

        # METALS
        ("MAT_MET_COPPER", "metals", "Pure Copper Scrap", "शुद्ध तांबे (कॉपर)", "शुद्ध तांबा (कॉपर)", "స్వచ్ఛమైన రాగి (కాపర్)",
         "kg", 560.0, "🪙", "LOW", "SAFE_GENERAL",
         "Bright stripped copper wire, pipes, utensils, and motor winding scrap.",
         "स्वच्छ तांब्याची वायर, पाईप्स आणि मोटर वाइंडिंग भंगार.",
         "चमकीला तांबे का तार, पाइप, बर्तन और मोटर वाइंडिंग स्क्रैप।",
         "మెరిసే రాగి వైర్లు, పైపులు మరియు మోటారు వైండింగ్ స్క్రాప్."),

        ("MAT_MET_BRASS", "metals", "Brass Scrap (Pital)", "पितळ भंगार", "पीतल स्क्रैप", "ఇత్తడి స్క్రాప్",
         "kg", 410.0, "🎺", "LOW", "SAFE_GENERAL",
         "Valves, taps, ornaments, and plumbing fittings made of yellow brass.",
         "पितळेचे नळ, व्हॉल्व्ह आणि जुनी भांडी.",
         "पीतल के नल, वाल्व, पुरानी फिटिंग और बर्तन।",
         "ఇత్తడి కుళాయిలు, వాల్వ్‌లు మరియు పాత పాత్రలు."),

        ("MAT_MET_ALUM", "metals", "Aluminium Scrap", "अ‍ॅल्युमिनियम भंगार", "एल्युमिनियम स्क्रैप", "అల్యూమినియం స్క్రాప్",
         "kg", 135.0, "🪟", "LOW", "SAFE_GENERAL",
         "Aluminium window sections, utensils, cans, and motor castings.",
         "अ‍ॅल्युमिनियम खिडकीच्या पट्ट्या, भांडी आणि कास्टिंग भाग.",
         "एल्युमिनियम खिड़की सेक्शन, बर्तन और कास्टिंग स्क्रैप।",
         "అల్యూమినియం విండో సెక్షన్లు మరియు పాత్రలు."),

        ("MAT_MET_IRON", "metals", "Iron & Steel (Loha)", "लोखंड व स्टील", "लोहा और स्टील", "ఇనుము మరియు స్టీల్",
         "kg", 32.0, "🔩", "LOW", "SAFE_GENERAL",
         "Heavy melting scrap, rods, grills, sheets, and discarded iron frames.",
         "जड लोखंडी सळ्या, ग्रील, पाईप आणि पत्रे.",
         "भारी लोहे की छड़ें, ग्रिल, पाइप और लोहे के फ्रेम।",
         "ఇనుప రాడ్లు, గ్రిల్స్ మరియు భారీ ఇనుప స్క్రాప్."),

        # PAPER & CARDBOARD
        ("MAT_PAP_NEWS", "paper", "Newspaper (Raddi)", "जुनी वर्तमानपत्रे (रद्दी)", "पुराना अखबार (रद्दी)", "వార్తాపత్రికలు (రద్దీ పేపర్లు)",
         "kg", 16.0, "📰", "LOW", "SAFE_GENERAL",
         "Dry, sorted daily newspapers in English, Marathi, Hindi, Telugu.",
         "कोरडी आणि स्वच्छ वर्तमानपत्रे.",
         "सूखे और साफ पुराने अखबार।",
         "పొడి వార్తాపత్రికలు."),

        ("MAT_PAP_CARD", "paper", "Corrugated Cardboard (Cartons)", "पुठ्ठा आणि खोके", "गत्ता और कार्टन बॉक्स", "కార్డ్‌బోర్డ్ & అట్టపెట్టెలు",
         "kg", 10.5, "📦", "LOW", "SAFE_GENERAL",
         "Packaging cartons, e-commerce brown delivery boxes, corrugated sheets.",
         "पॅकिंग बॉक्सेस, पुठ्ठा खोके आणि ब्राऊन कार्टन.",
         "पैकिंग डिब्बे, भूरे गत्ते और कार्टन बॉक्सेज।",
         "ప్యాకింగ్ అట్టపెట్టెలు మరియు డెలివరీ బాక్సులు."),

        # PLASTICS
        ("MAT_PLA_PET", "plastics", "PET Plastic Bottles", "पाण्याच्या बाटल्या (PET)", "पीईटी प्लास्टिक की बोतलें", "పిఇటి ప్లాస్టిక్ సీసాలు",
         "kg", 22.0, "🧴", "LOW", "SAFE_GENERAL",
         "Clear water, beverage, and soft drink bottles with caps removed.",
         "पारदर्शक पाण्याच्या आणि शीतपेयांच्या बाटल्या.",
         "पानी और कोल्ड-ड्रिंक की साफ प्लास्टिक बोतलें।",
         "నీటి మరియు శీతల పానీయాల ప్లాస్టిక్ సీసాలు."),

        ("MAT_PLA_HARD", "plastics", "Hard Plastic (Buckets/Crates)", "कडक प्लॅस्टिक (बादल्या/क्रॅट्स)", "कड़ा प्लास्टिक (बाल्टी/क्रेट्स)", "గట్టి ప్లాస్టిక్ (బకెట్లు/క్రేట్లు)",
         "kg", 26.0, "🪣", "LOW", "SAFE_GENERAL",
         "HDPE/PP broken buckets, milk crates, tubs, and rigid toy pieces.",
         "तुटलेल्या बादल्या, टब, प्लास्टिक क्रेट्स आणि टेबल-खुर्च्या.",
         "टूटी बाल्टियां, टब, प्लास्टिक के क्रेट्स और कुर्सियां।",
         "విరిగిన బకెట్లు, టబ్‌లు మరియు ప్లాస్టిక్ క్రేట్లు.")
    ]

    for m in materials_data:
        cursor.execute("""
        INSERT INTO materials VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, m)

    # Prices Dataset across Cities (Pune, Hyderabad, Mumbai)
    cities = ["Pune", "Hyderabad", "Mumbai"]
    for mat in materials_data:
        mat_id = mat[0]
        base = mat[7]
        for c in cities:
            adj = 1.0
            if c == "Mumbai":
                adj = 1.05
            elif c == "Hyderabad":
                adj = 0.98

            rate = round(base * adj, 1)
            min_r = round(rate * 0.92, 1)
            max_r = round(rate * 1.08, 1)
            trend = random.choice(["UP", "UP", "STABLE", "DOWN"])
            trend_pct = round(random.uniform(1.5, 6.5), 1)

            cursor.execute("""
            INSERT INTO prices (material_id, city, buying_rate, market_min, market_max, trend_direction, trend_percent, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (mat_id, c, rate, min_r, max_r, trend, trend_pct, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    # Recyclers Dataset
    recyclers_data = [
        ("REC_ECO_VIDYUT", "EcoVidyut Industrial Recycling Pvt Ltd", "CPCB/EPR-EW/2024/MH-0928",
         "Plot 44-A, MIDC Bhosari Industrial Area, PCMC, Pune", "Pune", 18.6276, 73.8344,
         "ewaste,metals,plastics,paper", 5, "ACTIVE", "+91 98220 11928"),

        ("REC_DECCAN_GREEN", "Deccan Green Circular Hub & Metals", "TSPCB/EPR-RE/2023/TG-4410",
         "Phase II, Pashamylaram Industrial Estate, Hyderabad", "Hyderabad", 17.5312, 78.1884,
         "ewaste,metals,plastics,paper", 4, "ACTIVE", "+91 94401 77319"),

        ("REC_MAHA_METALS", "Maharashtra Scrap & E-Processors Ltd", "MPCB/REG-IND/2024/MH-8812",
         "Plot 12, Taloja MIDC, Navi Mumbai", "Mumbai", 19.0435, 73.1189,
         "ewaste,metals,plastics,paper", 6, "ACTIVE", "+91 97690 33812")
    ]
    for r in recyclers_data:
        cursor.execute("INSERT INTO recyclers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", r)

    # Micro-Hubs Dataset (Accessible neighborhood points for collectors)
    hubs_data = [
        # Pune Hubs
        ("HUB_PUN_01", "Kothrud Ward Scrap Micro-Hub (कोथरुड प्रभाग केंद्र)", "Pune",
         "Near Paud Phata, Karve Road, Kothrud, Pune - 411038", 18.5074, 73.8077,
         "Suresh More", "+91 98501 23456", 600.0, 340.5, "REC_ECO_VIDYUT"),

        ("HUB_PUN_02", "Hadapsar Industrial Ward Micro-Hub (हडपसर प्रभाग केंद्र)", "Pune",
         "Survey 45, Gadital, Hadapsar, Pune - 411028", 18.4967, 73.9417,
         "Vilas Patil", "+91 98902 34567", 800.0, 520.0, "REC_ECO_VIDYUT"),

        # Hyderabad Hubs
        ("HUB_HYD_01", "Kukatpally Circular Scrap Hub (కూకట్‌పల్లి కలెక్షన్ హబ్)", "Hyderabad",
         "Beside Metro Pillar A742, Kukatpally, Hyderabad - 500072", 17.4875, 78.4067,
         "K. Srinivas Rao", "+91 94412 88990", 700.0, 410.0, "REC_DECCAN_GREEN"),

        ("HUB_HYD_02", "Secunderabad Scrap Aggregation Point (సికింద్రాబాద్ సేకరణ కేంద్రం)", "Hyderabad",
         "Opp. Railway Yard, Ranigunj, Secunderabad - 500003", 17.4399, 78.4983,
         "P. Venkatesh", "+91 99881 22334", 650.0, 215.0, "REC_DECCAN_GREEN"),

        # Mumbai Hubs
        ("HUB_MUM_01", "Dharavi Circular Micro-Hub (धारावी केंद्र)", "Mumbai",
         "90 Feet Road, Near Kumbharwada, Dharavi, Mumbai - 400017", 19.0416, 72.8536,
         "Baburao Shinde", "+91 98200 45678", 1000.0, 680.0, "REC_MAHA_METALS")
    ]
    for h in hubs_data:
        cursor.execute("INSERT INTO micro_hubs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", h)

    # Default Collector Profile
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO collectors (id, name, phone, language, city, total_earnings, total_lots, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ("COL-MH-8821", "Ramesh Bhai / వెంకట్ రావు", "+91 98231 44556", "mr", "Pune", 18450.0, 3, now_str))

    # Pre-seed some historical lots for demo realism
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    two_days_ago = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")

    historical_lots = [
        ("LOT-2026-0891", "COL-MH-8821", "Ramesh Bhai", "+91 98231 44556", "MAT_MET_COPPER",
         12.0, "kg", 6720.0, "HUB_PUN_01", "4921", None, "POOLED", 12.0, 6720.0, "CASH", None,
         two_days_ago, two_days_ago, "BATCH-PUN-001"),

        ("LOT-2026-0892", "COL-MH-8821", "Ramesh Bhai", "+91 98231 44556", "MAT_PAP_CARD",
         35.0, "kg", 367.5, "HUB_PUN_01", "7712", None, "POOLED", 35.0, 367.5, "CASH", None,
         yesterday, yesterday, "BATCH-PUN-001"),

        ("LOT-2026-0893", "COL-MH-8821", "Ramesh Bhai", "+91 98231 44556", "MAT_PCB_HIGH",
         27.0, "kg", 11340.0, "HUB_PUN_01", "8834", None, "VERIFIED_AT_HUB", 27.0, 11340.0, "CASH", None,
         yesterday, yesterday, None)
    ]
    for lot in historical_lots:
        cursor.execute("""
        INSERT INTO lots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, lot)

    # Passbook Entries corresponding to completed lots
    cursor.execute("""
    INSERT INTO passbook_entries (collector_id, lot_id, amount, payment_mode, material_summary, hub_name, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("COL-MH-8821", "LOT-2026-0891", 6720.0, "CASH", "Pure Copper (12.0 kg)", "Kothrud Ward Scrap Micro-Hub", two_days_ago))

    cursor.execute("""
    INSERT INTO passbook_entries (collector_id, lot_id, amount, payment_mode, material_summary, hub_name, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("COL-MH-8821", "LOT-2026-0892", 367.5, "CASH", "Cardboard Cartons (35.0 kg)", "Kothrud Ward Scrap Micro-Hub", yesterday))

    cursor.execute("""
    INSERT INTO passbook_entries (collector_id, lot_id, amount, payment_mode, material_summary, hub_name, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("COL-MH-8821", "LOT-2026-0893", 11340.0, "CASH", "Motherboard / PCB Scrap (27.0 kg)", "Kothrud Ward Scrap Micro-Hub", yesterday))

    # Pre-seed a pooled batch ready for Recycler Log Picker pickup
    cursor.execute("""
    INSERT INTO pooled_batches (id, micro_hub_id, recycler_id, material_category, total_weight_kg, lot_count, status, log_picker_vehicle_no, driver_name, driver_phone, dispatched_at, delivered_at, cpcb_manifest_no, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "BATCH-PUN-001", "HUB_PUN_01", "REC_ECO_VIDYUT", "Mixed E-Waste & Metals", 340.5, 8,
        "REQUESTED_PICKUP", None, None, None, None, None, None, yesterday
    ))

    cursor.execute("""
    INSERT INTO pooled_batches (id, micro_hub_id, recycler_id, material_category, total_weight_kg, lot_count, status, log_picker_vehicle_no, driver_name, driver_phone, dispatched_at, delivered_at, cpcb_manifest_no, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "BATCH-PUN-002", "HUB_PUN_02", "REC_ECO_VIDYUT", "Aggregated E-Waste & Plastics", 520.0, 14,
        "LOG_PICKER_DISPATCHED", "MH-12-RN-7742", "Tukaram Shinde", "+91 98221 55667",
        now_str, None, "EPR-MH-PUN-2026-0811", yesterday
    ))

    conn.commit()
    print("Seeding complete! Database initialized successfully.")

if __name__ == "__main__":
    init_db()
