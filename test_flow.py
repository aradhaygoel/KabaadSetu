import urllib.request
import urllib.parse
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

def run_test():
    print("=== Testing KabaadSetu End-to-End Live Workflow ===")

    # 1. Fetch live rates for Pune
    req = urllib.request.Request(f"{BASE_URL}/api/prices?city=Pune")
    with urllib.request.urlopen(req) as res:
        prices = json.loads(res.read().decode('utf-8'))
        print(f"1. Prices fetched: {len(prices['prices'])} items available for {prices['city']}.")

    # 2. Collector creates a new scrap lot: 18 kg of Copper
    post_data = urllib.parse.urlencode({
        "collector_id": "COL-MH-8821",
        "collector_name": "Ramesh Bhai",
        "collector_phone": "+91 98231 44556",
        "material_id": "MAT_MET_COPPER",
        "declared_qty": "18.0",
        "unit": "kg",
        "micro_hub_id": "HUB_PUN_01",
        "city": "Pune"
    }).encode('utf-8')

    req = urllib.request.Request(f"{BASE_URL}/api/lots", data=post_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req) as res:
        lot_res = json.loads(res.read().decode('utf-8'))
        lot = lot_res["lot"]
        lot_id = lot["id"]
        otp = lot["otp_code"]
        print(f"2. Lot created: {lot_id} | Material: {lot['name_en']} | Est Value: ₹{lot['est_value']} | 4-Digit OTP: {otp}")

    # 3. Micro-Hub Operator verifies the lot using 4-digit OTP and physical scale weight
    verify_data = urllib.parse.urlencode({
        "lot_id": lot_id,
        "entered_otp": otp,
        "verified_qty": "17.8", # Actual scale reading
        "payment_mode": "CASH"
    }).encode('utf-8')

    req = urllib.request.Request(f"{BASE_URL}/api/micro-hubs/HUB_PUN_01/verify-lot", data=verify_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req) as res:
        v_res = json.loads(res.read().decode('utf-8'))
        print(f"3. Micro-Hub verification passed! Verified Weight: {v_res['verified_qty']} kg | Final Payout: ₹{v_res['final_payout']} ({v_res['payment_mode']})")

    # 4. Check Collector Passbook
    req = urllib.request.Request(f"{BASE_URL}/api/collector/COL-MH-8821/passbook")
    with urllib.request.urlopen(req) as res:
        pb = json.loads(res.read().decode('utf-8'))
        print(f"4. Collector Passbook updated! Total Earnings: ₹{pb['collector']['total_earnings']} | Recent Entry: {pb['entries'][0]['material_summary']} (+₹{pb['entries'][0]['amount']})")

    # 5. Micro-Hub inventory pooling & bulk pickup request
    req = urllib.request.Request(f"{BASE_URL}/api/micro-hubs/HUB_PUN_01/request-bulk-pickup", data=b'', method='POST')
    with urllib.request.urlopen(req) as res:
        bulk_res = json.loads(res.read().decode('utf-8'))
        batch_id = bulk_res["batch_id"]
        print(f"5. Bulk Pickup Triggered! Batch ID: {batch_id} | Pooled Weight: {bulk_res['total_weight_kg']} kg")

    # 6. Recycler dispatches log picker vehicle
    dispatch_payload = json.dumps({
        "vehicle_no": "MH-12-RN-7742",
        "driver_name": "Tukaram Shinde",
        "driver_phone": "+91 98221 55667"
    }).encode('utf-8')

    req = urllib.request.Request(f"{BASE_URL}/api/recycler/batches/{batch_id}/dispatch", data=dispatch_payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as res:
        d_res = json.loads(res.read().decode('utf-8'))
        print(f"6. Recycler Dispatched! {d_res['message']}")

    # 7. Recycler confirms receipt at formal industrial facility
    req = urllib.request.Request(f"{BASE_URL}/api/recycler/batches/{batch_id}/receive", data=b'', method='POST')
    with urllib.request.urlopen(req) as res:
        r_res = json.loads(res.read().decode('utf-8'))
        manifest_no = r_res["cpcb_manifest_no"]
        print(f"7. Facility Receipt Confirmed! Official CPCB EPR Manifest: {manifest_no}")

    # 8. Fetch complete verifiable end-to-end traceability dossier for the initial lot
    req = urllib.request.Request(f"{BASE_URL}/api/traceability/{lot_id}")
    with urllib.request.urlopen(req) as res:
        trace = json.loads(res.read().decode('utf-8'))
        d = trace["data"]
        print("\n8. End-to-End Chain of Custody Audit Trail:")
        print(f"   - Lot ID: {d['id']} ({d['name_en']})")
        print(f"   - Collector: {d['collector_name']} (Declared: {d['declared_qty']} {d['unit']})")
        print(f"   - Micro-Hub: {d['hub_name']} (Verified: {d['verified_qty']} {d['unit']} | Paid: ₹{d['final_payout']} {d['payment_mode']})")
        print(f"   - Bulk Logistics: Vehicle {d['log_picker_vehicle_no']} (Driver: {d['driver_name']})")
        print(f"   - Recycler Facility: {d['recycler_name']} ({d['cpcb_reg']})")
        print(f"   - CPCB Compliance Manifest: {d['cpcb_manifest_no']}")
        print(f"   - Final Lot Status: {d['status']}")

    print("\n✅ All 8 stages of KabaadSetu verified successfully with 100% operational fidelity!")

if __name__ == "__main__":
    run_test()
