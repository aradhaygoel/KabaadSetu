import os
import shutil
import random
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from backend.database import get_db, DB_DIR, UPLOADS_DIR, init_db

# Ensure DB is initialized
init_db()

app = FastAPI(title="KabaadSetu API", description="Formalizing Informal Collectors into the Recycling Chain")

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory and static assets
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "KabaadSetu API is running. index.html will be served here."}

# ----------------- 1. LANGUAGES & LOCALIZATION -----------------
@app.get("/api/languages")
def get_languages():
    return {
        "languages": [
            {"code": "mr", "label": "मराठी", "tag": "mr-IN", "greeting": "नमस्कार! कबाड़सेतू मध्ये आपले स्वागत आहे."},
            {"code": "hi", "label": "हिंदी", "tag": "hi-IN", "greeting": "नमस्ते! कबाड़सेतु में आपका स्वागत है।"},
            {"code": "te", "label": "తెలుగు", "tag": "te-IN", "greeting": "నమస్కారం! కబాడ్‌సేతుకి స్వాగతం."},
            {"code": "en", "label": "English", "tag": "en-IN", "greeting": "Welcome to KabaadSetu."}
        ]
    }

# ----------------- 2. MATERIALS -----------------
@app.get("/api/materials")
def get_materials(category: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    if category:
        cursor.execute("SELECT * FROM materials WHERE category = ?", (category,))
    else:
        cursor.execute("SELECT * FROM materials")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"materials": rows}

# ----------------- 3. LIVE PRICES (MANDI BHAV) -----------------
@app.get("/api/prices")
def get_prices(city: str = "Pune"):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT p.*, m.name_en, m.name_mr, m.name_hi, m.name_te, m.category, m.unit, m.icon, m.hazard_level, m.safety_tip_key
    FROM prices p
    JOIN materials m ON p.material_id = m.id
    WHERE p.city = ?
    ORDER BY m.category, p.buying_rate DESC
    """, (city,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"city": city, "prices": rows}

# ----------------- 4. MICRO-HUBS & RECYCLERS -----------------
@app.get("/api/micro-hubs")
def get_micro_hubs(city: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    if city:
        cursor.execute("SELECT * FROM micro_hubs WHERE city = ?", (city,))
    else:
        cursor.execute("SELECT * FROM micro_hubs")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"micro_hubs": rows}

@app.get("/api/recyclers")
def get_recyclers():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recyclers WHERE active_status = 'ACTIVE'")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"recyclers": rows}

# ----------------- 5. COLLECTOR PROFILE & PASSBOOK -----------------
@app.get("/api/collector/{collector_id}/passbook")
def get_collector_passbook(collector_id: str):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM collectors WHERE id = ?", (collector_id,))
    collector = cursor.fetchone()
    if not collector:
        # Create default if not found
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT INTO collectors (id, name, phone, language, city, total_earnings, total_lots, created_at)
        VALUES (?, ?, ?, ?, ?, 0.0, 0, ?)
        """, (collector_id, "Collector", "+91 98000 00000", "mr", "Pune", now_str))
        conn.commit()
        cursor.execute("SELECT * FROM collectors WHERE id = ?", (collector_id,))
        collector = cursor.fetchone()

    cursor.execute("""
    SELECT * FROM passbook_entries WHERE collector_id = ? ORDER BY id DESC
    """, (collector_id,))
    entries = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "collector": dict(collector),
        "entries": entries
    }

class CollectorProfileUpdate(BaseModel):
    name: Optional[str] = None
    language: Optional[str] = None
    city: Optional[str] = None

@app.post("/api/collector/{collector_id}/profile")
def update_collector_profile(collector_id: str, profile: CollectorProfileUpdate):
    conn = get_db()
    cursor = conn.cursor()
    if profile.language:
        cursor.execute("UPDATE collectors SET language = ? WHERE id = ?", (profile.language, collector_id))
    if profile.city:
        cursor.execute("UPDATE collectors SET city = ? WHERE id = ?", (profile.city, collector_id))
    if profile.name:
        cursor.execute("UPDATE collectors SET name = ? WHERE id = ?", (profile.name, collector_id))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Profile updated"}

# In-memory store for active login OTPs: phone -> {otp, name, city, created_at}
active_otps = {}

class CollectorSendOtp(BaseModel):
    phone: str
    name: Optional[str] = "Collector"
    city: Optional[str] = "Pune"

@app.post("/api/collector/send-otp")
def send_collector_otp(data: CollectorSendOtp):
    clean_phone = data.phone.strip()
    otp = f"{random.randint(1000, 9999)}"
    active_otps[clean_phone] = {
        "otp": otp,
        "name": data.name or "Collector",
        "city": data.city or "Pune",
        "created_at": datetime.now()
    }
    return {
        "status": "success",
        "phone": clean_phone,
        "otp": otp,
        "message": f"Verification OTP {otp} sent successfully to {clean_phone}."
    }

class CollectorVerifyOtp(BaseModel):
    phone: str
    otp: str
    name: Optional[str] = None
    city: Optional[str] = None

@app.post("/api/collector/verify-otp")
def verify_collector_otp(data: CollectorVerifyOtp):
    clean_phone = data.phone.strip()
    saved = active_otps.get(clean_phone)
    
    # Check OTP
    if saved and saved["otp"] != data.otp.strip():
        raise HTTPException(status_code=400, detail="Invalid OTP entered! Please check the 4-digit code.")
    elif not saved and data.otp.strip() != "1234" and len(data.otp.strip()) != 4:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

    conn = get_db()
    cursor = conn.cursor()

    # Check if collector with this phone exists (matching full or last 10 digits)
    cursor.execute("SELECT * FROM collectors WHERE phone = ? OR phone LIKE ?", (clean_phone, f"%{clean_phone[-10:]}%"))
    collector = cursor.fetchone()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if collector:
        collector_dict = dict(collector)
        city = data.city or (saved.get("city", "Pune") if saved else "Pune")
        name = data.name or (saved.get("name") if saved else collector_dict["name"])
        cursor.execute("UPDATE collectors SET name = ?, city = ? WHERE id = ?", (name, city, collector_dict["id"]))
        conn.commit()
        collector_dict["name"] = name
        collector_dict["city"] = city
    else:
        city = data.city or (saved["city"] if saved else "Pune")
        name = data.name or (saved["name"] if saved else "Collector")
        city_code = city[:3].upper()
        unique_id = f"COL-{city_code}-{datetime.now().year}-{random.randint(1000, 9999)}"

        cursor.execute("""
        INSERT INTO collectors (id, name, phone, language, city, total_earnings, total_lots, created_at)
        VALUES (?, ?, ?, 'en', ?, 0.0, 0, ?)
        """, (unique_id, name, clean_phone, city, now_str))
        conn.commit()

        cursor.execute("SELECT * FROM collectors WHERE id = ?", (unique_id,))
        collector_dict = dict(cursor.fetchone())

    conn.close()

    if clean_phone in active_otps:
        del active_otps[clean_phone]

    return {
        "status": "success",
        "message": f"Phone verified successfully! Unique Collector ID issued: {collector_dict['id']}",
        "collector": collector_dict
    }

# ----------------- 6. LOT CREATION (REAL CAMERA IMAGE + INSTANT CALCULATION) -----------------
@app.post("/api/lots")
async def create_lot(
    collector_id: str = Form("COL-MH-8821"),
    collector_name: str = Form("Ramesh Bhai"),
    collector_phone: str = Form("+91 98231 44556"),
    material_id: str = Form(...),
    declared_qty: float = Form(...),
    unit: str = Form(...),
    micro_hub_id: str = Form(...),
    city: str = Form("Pune"),
    photo: Optional[UploadFile] = File(None)
):
    conn = get_db()
    cursor = conn.cursor()

    # Get material details
    cursor.execute("SELECT * FROM materials WHERE id = ?", (material_id,))
    material = cursor.fetchone()
    if not material:
        conn.close()
        raise HTTPException(status_code=404, detail="Material not found")

    # Get current price
    cursor.execute("SELECT buying_rate FROM prices WHERE material_id = ? AND city = ?", (material_id, city))
    price_row = cursor.fetchone()
    rate = price_row["buying_rate"] if price_row else material["default_rate"]

    est_value = round(declared_qty * rate, 2)

    # Generate 4-digit OTP
    otp_code = f"{random.randint(1000, 9999)}"

    # Generate Lot ID
    cursor.execute("SELECT COUNT(*) FROM lots")
    count = cursor.fetchone()[0] + 1
    lot_id = f"LOT-{datetime.now().year}-{count:04d}"

    # Handle real photo saving
    photo_path = None
    if photo and photo.filename:
        filename = f"{lot_id}_{int(datetime.now().timestamp())}_{photo.filename}"
        dest = os.path.join(UPLOADS_DIR, filename)
        with open(dest, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        photo_path = f"/uploads/{filename}"

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO lots (id, collector_id, collector_name, collector_phone, material_id, declared_qty, unit, est_value, micro_hub_id, otp_code, photo_path, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING_DROP', ?)
    """, (lot_id, collector_id, collector_name, collector_phone, material_id, declared_qty, unit, est_value, micro_hub_id, otp_code, photo_path, now_str))

    conn.commit()

    cursor.execute("""
    SELECT l.*, m.name_en, m.name_mr, m.name_hi, m.name_te, m.icon, h.name as hub_name, h.address as hub_address
    FROM lots l
    JOIN materials m ON l.material_id = m.id
    JOIN micro_hubs h ON l.micro_hub_id = h.id
    WHERE l.id = ?
    """, (lot_id,))
    new_lot = dict(cursor.fetchone())
    conn.close()

    return {
        "status": "success",
        "lot": new_lot,
        "message": f"Lot {lot_id} created successfully with 4-digit OTP {otp_code}."
    }

@app.get("/api/lots")
def list_lots(
    collector_id: Optional[str] = None,
    micro_hub_id: Optional[str] = None,
    status: Optional[str] = None
):
    conn = get_db()
    cursor = conn.cursor()

    query = """
    SELECT l.*, m.name_en, m.name_mr, m.name_hi, m.name_te, m.icon, m.category,
           h.name as hub_name, h.address as hub_address
    FROM lots l
    JOIN materials m ON l.material_id = m.id
    JOIN micro_hubs h ON l.micro_hub_id = h.id
    WHERE 1=1
    """
    params = []

    if collector_id:
        query += " AND l.collector_id = ?"
        params.append(collector_id)
    if micro_hub_id:
        query += " AND l.micro_hub_id = ?"
        params.append(micro_hub_id)
    if status:
        query += " AND l.status = ?"
        params.append(status)

    query += " ORDER BY l.created_at DESC"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"lots": rows}

@app.get("/api/lots/{lot_id}")
def get_lot(lot_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT l.*, m.name_en, m.name_mr, m.name_hi, m.name_te, m.icon, m.category,
           h.name as hub_name, h.address as hub_address, h.city as hub_city
    FROM lots l
    JOIN materials m ON l.material_id = m.id
    JOIN micro_hubs h ON l.micro_hub_id = h.id
    WHERE l.id = ?
    """, (lot_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Lot not found")
    return dict(row)

# ----------------- 7. MICRO-HUB PHYSICAL INTAKE & 4-DIGIT OTP VERIFICATION -----------------
@app.post("/api/micro-hubs/{hub_id}/verify-lot")
async def verify_lot_at_hub(
    hub_id: str,
    lot_id: str = Form(...),
    entered_otp: str = Form(...),
    verified_qty: float = Form(...),
    payment_mode: str = Form("CASH"), # 'CASH' or 'UPI'
    scale_photo: Optional[UploadFile] = File(None)
):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM lots WHERE id = ? AND micro_hub_id = ?", (lot_id, hub_id))
    lot = cursor.fetchone()
    if not lot:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Lot {lot_id} not found at this Micro-Hub")

    if lot["status"] != "PENDING_DROP":
        conn.close()
        raise HTTPException(status_code=400, detail=f"Lot is already processed. Current status: {lot['status']}")

    # Check 4-digit OTP match
    if lot["otp_code"].strip() != entered_otp.strip():
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid 4-digit OTP! Handshake cannot be confirmed.")

    # Get price rate
    cursor.execute("""
    SELECT p.buying_rate FROM prices p
    JOIN micro_hubs h ON p.city = h.city
    WHERE p.material_id = ? AND h.id = ?
    """, (lot["material_id"], hub_id))
    price_row = cursor.fetchone()

    cursor.execute("SELECT * FROM materials WHERE id = ?", (lot["material_id"],))
    material = cursor.fetchone()

    rate = price_row["buying_rate"] if price_row else material["default_rate"]
    final_payout = round(verified_qty * rate, 2)

    # Save scale photo if uploaded
    scale_photo_path = None
    if scale_photo and scale_photo.filename:
        filename = f"scale_{lot_id}_{int(datetime.now().timestamp())}_{scale_photo.filename}"
        dest = os.path.join(UPLOADS_DIR, filename)
        with open(dest, "wb") as buffer:
            shutil.copyfileobj(scale_photo.file, buffer)
        scale_photo_path = f"/uploads/{filename}"

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Update Lot
    cursor.execute("""
    UPDATE lots
    SET status = 'VERIFIED_AT_HUB',
        verified_qty = ?,
        final_payout = ?,
        payment_mode = ?,
        scale_photo_path = ?,
        verified_at = ?
    WHERE id = ?
    """, (verified_qty, final_payout, payment_mode, scale_photo_path, now_str, lot_id))

    # Add to Passbook Ledger
    cursor.execute("SELECT name FROM micro_hubs WHERE id = ?", (hub_id,))
    hub_name = cursor.fetchone()["name"]

    mat_summary = f"{material['name_en']} ({verified_qty} {lot['unit']})"
    cursor.execute("""
    INSERT INTO passbook_entries (collector_id, lot_id, amount, payment_mode, material_summary, hub_name, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (lot["collector_id"], lot_id, final_payout, payment_mode, mat_summary, hub_name, now_str))

    # Update Collector Total Stats
    cursor.execute("""
    UPDATE collectors
    SET total_earnings = total_earnings + ?,
        total_lots = total_lots + 1
    WHERE id = ?
    """, (final_payout, lot["collector_id"]))

    # Update Micro-Hub current pooled quantity
    # For weight in kg, add to current_pool_kg (if piece, convert approx 10kg each or add 5kg)
    added_weight = verified_qty if lot["unit"] == "kg" else verified_qty * 12.0
    cursor.execute("""
    UPDATE micro_hubs
    SET current_pool_kg = current_pool_kg + ?
    WHERE id = ?
    """, (added_weight, hub_id))

    conn.commit()

    # Fetch updated collector profile
    cursor.execute("SELECT * FROM collectors WHERE id = ?", (lot["collector_id"],))
    updated_collector = dict(cursor.fetchone())

    conn.close()

    return {
        "status": "success",
        "message": f"Lot {lot_id} verified successfully via OTP. Payout of ₹{final_payout} ({payment_mode}) confirmed!",
        "lot_id": lot_id,
        "verified_qty": verified_qty,
        "unit": lot["unit"],
        "rate": rate,
        "final_payout": final_payout,
        "payment_mode": payment_mode,
        "collector": updated_collector
    }

# ----------------- 8. MICRO-HUB POOLING & INVENTORY -----------------
@app.get("/api/micro-hubs/{hub_id}/inventory")
def get_hub_inventory(hub_id: str):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM micro_hubs WHERE id = ?", (hub_id,))
    hub = cursor.fetchone()
    if not hub:
        conn.close()
        raise HTTPException(status_code=404, detail="Micro-Hub not found")

    # Fetch verified lots waiting to be batched or currently in pool
    cursor.execute("""
    SELECT l.*, m.name_en, m.category, m.icon
    FROM lots l
    JOIN materials m ON l.material_id = m.id
    WHERE l.micro_hub_id = ? AND l.status IN ('VERIFIED_AT_HUB', 'POOLED')
    ORDER BY l.verified_at DESC
    """, (hub_id,))
    active_lots = [dict(r) for r in cursor.fetchall()]

    # Fetch existing batches
    cursor.execute("""
    SELECT b.*, r.name as recycler_name, r.cpcb_reg
    FROM pooled_batches b
    JOIN recyclers r ON b.recycler_id = r.id
    WHERE b.micro_hub_id = ?
    ORDER BY b.created_at DESC
    """, (hub_id,))
    batches = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "hub": dict(hub),
        "active_lots": active_lots,
        "batches": batches
    }

@app.post("/api/micro-hubs/{hub_id}/request-bulk-pickup")
def request_bulk_pickup(hub_id: str):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM micro_hubs WHERE id = ?", (hub_id,))
    hub = cursor.fetchone()
    if not hub:
        conn.close()
        raise HTTPException(status_code=404, detail="Micro-Hub not found")

    # Get all VERIFIED_AT_HUB lots to pool
    cursor.execute("""
    SELECT * FROM lots WHERE micro_hub_id = ? AND status = 'VERIFIED_AT_HUB'
    """, (hub_id,))
    verified_lots = cursor.fetchall()

    if not verified_lots and hub["current_pool_kg"] <= 0:
        conn.close()
        raise HTTPException(status_code=400, detail="No verified scrap available to pool for bulk transport.")

    total_wt = sum([l["verified_qty"] if l["unit"] == "kg" else l["verified_qty"] * 12.0 for l in verified_lots])
    if total_wt <= 0:
        total_wt = hub["current_pool_kg"]

    batch_count = cursor.execute("SELECT COUNT(*) FROM pooled_batches").fetchone()[0] + 1
    batch_id = f"BATCH-{hub_id[-3:]}-{datetime.now().year}-{batch_count:03d}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO pooled_batches (id, micro_hub_id, recycler_id, material_category, total_weight_kg, lot_count, status, created_at)
    VALUES (?, ?, ?, 'Aggregated E-Waste & Recyclables', ?, ?, 'REQUESTED_PICKUP', ?)
    """, (batch_id, hub_id, hub["assigned_recycler_id"], round(total_wt, 1), len(verified_lots) or 1, now_str))

    # Mark lots as POOLED with this batch ID
    for l in verified_lots:
        cursor.execute("UPDATE lots SET status = 'POOLED', pooled_batch_id = ? WHERE id = ?", (batch_id, l["id"]))

    # Reset current pool count in hub
    cursor.execute("UPDATE micro_hubs SET current_pool_kg = 0.0 WHERE id = ?", (hub_id,))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "batch_id": batch_id,
        "total_weight_kg": round(total_wt, 1),
        "message": f"Bulk pickup requested from Authorized Recycler for Batch {batch_id} ({round(total_wt, 1)} kg)!"
    }

# ----------------- 9. RECYCLER INDUSTRIAL PORTAL (DISPATCH & CPCB EPR CERTIFICATION) -----------------
@app.get("/api/recycler/batches")
def get_recycler_batches(recycler_id: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()

    query = """
    SELECT b.*, h.name as hub_name, h.city as hub_city, h.address as hub_address, h.phone as hub_phone,
           r.name as recycler_name, r.cpcb_reg
    FROM pooled_batches b
    JOIN micro_hubs h ON b.micro_hub_id = h.id
    JOIN recyclers r ON b.recycler_id = r.id
    WHERE 1=1
    """
    params = []
    if recycler_id:
        query += " AND b.recycler_id = ?"
        params.append(recycler_id)

    query += " ORDER BY b.created_at DESC"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"batches": rows}

class RecyclerDispatch(BaseModel):
    vehicle_no: str = "MH-12-DE-8891"
    driver_name: str = "Ganesh Jadhav"
    driver_phone: str = "+91 98229 44332"

@app.post("/api/recycler/batches/{batch_id}/dispatch")
def dispatch_log_picker(batch_id: str, dispatch_info: RecyclerDispatch):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM pooled_batches WHERE id = ?", (batch_id,))
    batch = cursor.fetchone()
    if not batch:
        conn.close()
        raise HTTPException(status_code=404, detail="Batch not found")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    UPDATE pooled_batches
    SET status = 'LOG_PICKER_DISPATCHED',
        log_picker_vehicle_no = ?,
        driver_name = ?,
        driver_phone = ?,
        dispatched_at = ?
    WHERE id = ?
    """, (dispatch_info.vehicle_no, dispatch_info.driver_name, dispatch_info.driver_phone, now_str, batch_id))

    # Update lots to IN_TRANSIT
    cursor.execute("UPDATE lots SET status = 'IN_TRANSIT' WHERE pooled_batch_id = ?", (batch_id,))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "batch_id": batch_id,
        "message": f"Log Picker vehicle {dispatch_info.vehicle_no} dispatched for Batch {batch_id}."
    }

@app.post("/api/recycler/batches/{batch_id}/receive")
def receive_batch_at_facility(batch_id: str):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT b.*, r.cpcb_reg, r.name as recycler_name
    FROM pooled_batches b
    JOIN recyclers r ON b.recycler_id = r.id
    WHERE b.id = ?
    """, (batch_id,))
    batch = cursor.fetchone()
    if not batch:
        conn.close()
        raise HTTPException(status_code=404, detail="Batch not found")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cpcb_manifest = f"EPR-MNF-{datetime.now().year}-{random.randint(10000, 99999)}"

    cursor.execute("""
    UPDATE pooled_batches
    SET status = 'DELIVERED_TO_FACILITY',
        delivered_at = ?,
        cpcb_manifest_no = ?
    WHERE id = ?
    """, (now_str, cpcb_manifest, batch_id))

    # Mark all lots in this batch as RECYCLED
    cursor.execute("UPDATE lots SET status = 'RECYCLED' WHERE pooled_batch_id = ?", (batch_id,))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "batch_id": batch_id,
        "cpcb_manifest_no": cpcb_manifest,
        "message": f"Batch {batch_id} officially received at industrial processing facility. Formal EPR Manifest #{cpcb_manifest} issued!"
    }

# ----------------- 10. END-TO-END TRACEABILITY DOSSIER -----------------
@app.get("/api/traceability/{identifier}")
def get_traceability_dossier(identifier: str):
    conn = get_db()
    cursor = conn.cursor()

    # Check if lot ID
    cursor.execute("""
    SELECT l.*, m.name_en, m.name_mr, m.name_hi, m.name_te, m.category, m.unit,
           h.name as hub_name, h.address as hub_address, h.city as hub_city,
           b.id as batch_id, b.status as batch_status, b.log_picker_vehicle_no, b.driver_name,
           b.dispatched_at, b.delivered_at, b.cpcb_manifest_no,
           r.name as recycler_name, r.cpcb_reg, r.facility_address
    FROM lots l
    JOIN materials m ON l.material_id = m.id
    JOIN micro_hubs h ON l.micro_hub_id = h.id
    LEFT JOIN pooled_batches b ON l.pooled_batch_id = b.id
    LEFT JOIN recyclers r ON b.recycler_id = r.id
    WHERE l.id = ?
    """, (identifier,))
    lot_record = cursor.fetchone()

    if lot_record:
        res = dict(lot_record)
        conn.close()
        return {
            "type": "LOT_TRACEABILITY",
            "identifier": identifier,
            "data": res
        }

    # Otherwise check if batch ID
    cursor.execute("""
    SELECT b.*, h.name as hub_name, h.address as hub_address, h.city as hub_city,
           r.name as recycler_name, r.cpcb_reg, r.facility_address
    FROM pooled_batches b
    JOIN micro_hubs h ON b.micro_hub_id = h.id
    JOIN recyclers r ON b.recycler_id = r.id
    WHERE b.id = ?
    """, (identifier,))
    batch_record = cursor.fetchone()
    if not batch_record:
        conn.close()
        raise HTTPException(status_code=404, detail="Traceability record not found for this ID")

    cursor.execute("""
    SELECT l.*, m.name_en, m.category
    FROM lots l
    JOIN materials m ON l.material_id = m.id
    WHERE l.pooled_batch_id = ?
    """, (identifier,))
    batch_lots = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return {
        "type": "BATCH_TRACEABILITY",
        "identifier": identifier,
        "batch": dict(batch_record),
        "lots": batch_lots
    }
