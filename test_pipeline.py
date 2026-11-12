"""Quick dry-run test for the data pipeline (cleaner + exporter)."""
from pipeline.cleaner import clean_leads
from utils.exporter import export

mock = [
    {"company_name": "TechNova Pvt Ltd", "phone": "+91-9876543210",
     "address": "A-12, Okhla Industrial Area, Phase 2, New Delhi 110020",
     "website": "https://www.technova.in", "domain": "technova.in",
     "category": "IT Services", "email": "info@technova.in; sales@technova.in",
     "social_links": "", "pincode": "110020"},
    {"company_name": "FinServe Solutions", "phone": "011-41234567",
     "address": "B-45 Nehru Place, New Delhi 110019",
     "website": "https://finserve.co.in", "domain": "finserve.co.in",
     "category": "Fintech", "email": "contact@finserve.co.in",
     "social_links": "linkedin: https://linkedin.com/company/finserve",
     "pincode": "110019"},
    {"company_name": "No Address Corp", "phone": "9988776655",
     "address": "Mumbai 400001", "website": "", "domain": "",
     "category": "Consulting", "email": "", "social_links": "",
     "pincode": "400001"},
    {"company_name": "Dupe of TechNova", "phone": "9876543210",
     "address": "Okhla Phase 2, Delhi 110020",
     "website": "https://technova.in", "domain": "technova.in",
     "category": "IT", "email": "", "social_links": "", "pincode": "110020"},
    {"company_name": "", "phone": "", "address": "", "website": "",
     "domain": "", "category": "", "email": "", "social_links": "",
     "pincode": ""},
]

cleaned = clean_leads(mock)
print(f"Cleaned: {len(cleaned)} leads (expect 2)")
for l in cleaned:
    print(f"  - {l['company_name']} | {l['phone']} | {l['email']}")

csv_p, xlsx_p = export(cleaned)
print(f"CSV:  {csv_p}")
print(f"XLSX: {xlsx_p}")
print("DRY-RUN PASSED")
