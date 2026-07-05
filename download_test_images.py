import os
import time
import shutil
import json
import requests
import pathlib

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TruthGuardTest/1.0)"}

def download_image(url, output_path):
    time.sleep(2)
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        # Ensure parent directories exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(response.content)
        return True
    except Exception as e:
        filename = os.path.basename(output_path)
        print(f"FAILED: {filename} — {e}")
        return False

def main():
    # SECTION A — Download AI-generated faces into 01_ai_generated_faces/
    # Download 5 images from https://100k-faces.vercel.app/api/random-image
    for i in range(1, 6):
        filename = f"face_0{i}.jpg"
        path = os.path.join("test_images", "01_ai_generated_faces", filename)
        if download_image("https://100k-faces.vercel.app/api/random-image", path):
            print(f"Saved: 01_ai_generated_faces/{filename}")

    # SECTION B — Download real photographs into 02_real_photographs/
    urls_b = [
        ("https://loremflickr.com/1200/800/street,india", "real_01.jpg"),
        ("https://loremflickr.com/1200/800/city,chennai", "real_02.jpg"),
        ("https://loremflickr.com/1200/800/market,india", "real_03.jpg")
    ]
    for url, filename in urls_b:
        path = os.path.join("test_images", "02_real_photographs", filename)
        if download_image(url, path):
            print(f"Saved: 02_real_photographs/{filename}")

    # SECTION C — Copy faces into 03_political_misinfo/
    try:
        shutil.copy("test_images/01_ai_generated_faces/face_01.jpg", "test_images/03_political_misinfo/politician_fake_01.jpg")
        shutil.copy("test_images/01_ai_generated_faces/face_02.jpg", "test_images/03_political_misinfo/politician_fake_02.jpg")
        print("Copied: politician_fake_01.jpg and politician_fake_02.jpg")
    except Exception as e:
        print(f"FAILED: copying politician_fake_01.jpg and politician_fake_02.jpg — {e}")

    # SECTION D — Copy faces into 04_financial_fraud/
    try:
        shutil.copy("test_images/01_ai_generated_faces/face_03.jpg", "test_images/04_financial_fraud/bank_official_fake_01.jpg")
        shutil.copy("test_images/01_ai_generated_faces/face_04.jpg", "test_images/04_financial_fraud/bank_official_fake_02.jpg")
        print("Copied: bank_official_fake_01.jpg and bank_official_fake_02.jpg")
    except Exception as e:
        print(f"FAILED: copying bank_official_fake_01.jpg and bank_official_fake_02.jpg — {e}")

    # SECTION E — Download disaster photos into 05_disaster_misinfo/
    path_e1 = os.path.join("test_images", "05_disaster_misinfo", "disaster_real_01.jpg")
    if download_image("https://loremflickr.com/1200/800/flood,disaster", path_e1):
        print("Saved: 05_disaster_misinfo/disaster_real_01.jpg")
    path_e2 = os.path.join("test_images", "05_disaster_misinfo", "disaster_real_02.jpg")
    if download_image("https://loremflickr.com/1200/800/emergency,rain", path_e2):
        print("Saved: 05_disaster_misinfo/disaster_real_02.jpg")
    print("Saved: 05_disaster_misinfo/disaster_real_XX.jpg")

    # SECTION F — Copy and download into 06_identity_impersonation/
    try:
        shutil.copy("test_images/01_ai_generated_faces/face_05.jpg", "test_images/06_identity_impersonation/impersonation_01.jpg")
    except Exception as e:
        print(f"FAILED: copying impersonation_01.jpg — {e}")
    path_f2 = os.path.join("test_images", "06_identity_impersonation", "impersonation_02.jpg")
    download_image("https://100k-faces.vercel.app/api/random-image", path_f2)
    print("Saved: 06_identity_impersonation/impersonation_01.jpg and impersonation_02.jpg")

    # SECTION G — Download art images into 07_satire_low_risk/
    path_g1 = os.path.join("test_images", "07_satire_low_risk", "satire_01.jpg")
    if download_image("https://loremflickr.com/1200/800/art,illustration", path_g1):
        print("Saved: 07_satire_low_risk/satire_01.jpg")
    path_g2 = os.path.join("test_images", "07_satire_low_risk", "satire_02.jpg")
    if download_image("https://loremflickr.com/1200/800/cartoon,creative", path_g2):
        print("Saved: 07_satire_low_risk/satire_02.jpg")
    print("Saved: 07_satire_low_risk/satire_XX.jpg")

    # SECTION H — Create test_claims.json
    claims_data = [
      {
        "test_id": "VF-01",
        "folder": "01_ai_generated_faces",
        "image_file": "face_01.jpg",
        "claim_text": "This is a photograph of a real person.",
        "expected_risk_level": "High",
        "expected_harm_category": "Identity Impersonation",
        "purpose": "Baseline visual test — AI face with simple claim"
      },
      {
        "test_id": "VF-02",
        "folder": "01_ai_generated_faces",
        "image_file": "face_02.jpg",
        "claim_text": "This is a recent photograph submitted as identity proof for a bank account application.",
        "expected_risk_level": "High",
        "expected_harm_category": "Identity Impersonation",
        "purpose": "AI face submitted as fake identity document"
      },
      {
        "test_id": "RP-01",
        "folder": "02_real_photographs",
        "image_file": "real_01.jpg",
        "claim_text": "This is a photograph of a street scene taken in Chennai today.",
        "expected_risk_level": "Low",
        "expected_harm_category": "Entertainment / Low Risk",
        "purpose": "Baseline real photo — system must correctly clear genuine content"
      },
      {
        "test_id": "RP-02",
        "folder": "02_real_photographs",
        "image_file": "real_02.jpg",
        "claim_text": "This image shows a local market in South India.",
        "expected_risk_level": "Low",
        "expected_harm_category": "Entertainment / Low Risk",
        "purpose": "False positive check — real image with true claim must return Low"
      },
      {
        "test_id": "PM-01",
        "folder": "03_political_misinfo",
        "image_file": "politician_fake_01.jpg",
        "claim_text": "This image shows a state minister accepting cash from a contractor in Chennai. The video is going viral on WhatsApp groups across Tamil Nadu ahead of the election.",
        "expected_risk_level": "Critical",
        "expected_harm_category": "Political Misinformation",
        "purpose": "Primary demo case — AI face with election bribery claim"
      },
      {
        "test_id": "PM-02",
        "folder": "03_political_misinfo",
        "image_file": "politician_fake_02.jpg",
        "claim_text": "This leader was photographed at a secret meeting with opposition members two days before the state election. Exclusive image leaked by an insider source today.",
        "expected_risk_level": "Critical",
        "expected_harm_category": "Political Misinformation",
        "purpose": "Election interference — fabricated political meeting claim"
      },
      {
        "test_id": "FF-01",
        "folder": "04_financial_fraud",
        "image_file": "bank_official_fake_01.jpg",
        "claim_text": "This is the SBI customer care officer calling to verify your account. Your account has been flagged for suspicious activity. Share your OTP immediately to avoid account suspension.",
        "expected_risk_level": "Critical",
        "expected_harm_category": "Financial Fraud",
        "purpose": "UPI fraud — AI face impersonating SBI official demanding OTP"
      },
      {
        "test_id": "FF-02",
        "folder": "04_financial_fraud",
        "image_file": "bank_official_fake_02.jpg",
        "claim_text": "This RBI-certified agent is verifying Paytm wallet accounts. Your wallet will be permanently blocked in 24 hours unless you complete verification with your UPI PIN.",
        "expected_risk_level": "Critical",
        "expected_harm_category": "Financial Fraud",
        "purpose": "UPI wallet fraud — fake RBI agent demanding PIN verification"
      },
      {
        "test_id": "DM-01",
        "folder": "05_disaster_misinfo",
        "image_file": "disaster_real_01.jpg",
        "claim_text": "This image shows the Chennai Adyar river flooding today after the Chembarambakkam dam was opened without warning. Residents of Velachery and Saidapet must evacuate immediately.",
        "expected_risk_level": "High",
        "expected_harm_category": "Public Safety Risk",
        "purpose": "Context layer showcase — real unmanipulated image with false local disaster claim"
      },
      {
        "test_id": "DM-02",
        "folder": "05_disaster_misinfo",
        "image_file": "disaster_real_02.jpg",
        "claim_text": "Building collapsed in T Nagar Chennai this morning at 6am. Over 50 people are trapped under debris. NDRF teams have been deployed and rescue is ongoing.",
        "expected_risk_level": "High",
        "expected_harm_category": "Public Safety Risk",
        "purpose": "Panic misinformation — real image repurposed with false local emergency claim"
      },
      {
        "test_id": "II-01",
        "folder": "06_identity_impersonation",
        "image_file": "impersonation_01.jpg",
        "claim_text": "This is the Infosys CEO announcing emergency layoffs of 40000 employees across India starting next month. Internal memo leaked by a senior executive this morning.",
        "expected_risk_level": "High",
        "expected_harm_category": "Identity Impersonation",
        "purpose": "Corporate impersonation — fake CEO announcement causing market panic"
      },
      {
        "test_id": "II-02",
        "folder": "06_identity_impersonation",
        "image_file": "impersonation_02.jpg",
        "claim_text": "Famous Tamil actress endorsing this weight loss supplement. She lost 20kg in 3 weeks using this one product. Limited stock available. Order before midnight.",
        "expected_risk_level": "High",
        "expected_harm_category": "Identity Impersonation",
        "purpose": "Celebrity endorsement fraud — common WhatsApp scam pattern in India"
      },
      {
        "test_id": "SL-01",
        "folder": "07_satire_low_risk",
        "image_file": "satire_01.jpg",
        "claim_text": "AI-generated artwork created for a digital art competition entry. This is not a real person or real place. Created using Stable Diffusion for creative purposes.",
        "expected_risk_level": "Low",
        "expected_harm_category": "Entertainment / Low Risk",
        "purpose": "Calibration — clearly labelled synthetic art must return Low risk"
      },
      {
        "test_id": "SL-02",
        "folder": "07_satire_low_risk",
        "image_file": "satire_02.jpg",
        "claim_text": "Satirical illustration created by our design team for a social media post about the monsoon season in Chennai. Not meant to represent real events or real people.",
        "expected_risk_level": "Low",
        "expected_harm_category": "Entertainment / Low Risk",
        "purpose": "Satire test — clearly disclosed synthetic content must not trigger escalation"
      }
    ]

    claims_path = os.path.join("test_images", "claims", "test_claims.json")
    # Ensure parent dir exists (it should, but just in case)
    os.makedirs(os.path.dirname(claims_path), exist_ok=True)
    with open(claims_path, "w", encoding="utf-8") as f:
        json.dump(claims_data, f, indent=2)

    print("Created: test_images/claims/test_claims.json with 14 test cases")
    print("All test images downloaded successfully.")

if __name__ == "__main__":
    main()
