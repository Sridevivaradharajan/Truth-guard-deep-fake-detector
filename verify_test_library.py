import os
import json

def main():
    # STEP 1 — Verify folder structure
    folders = [
        "test_images/01_ai_generated_faces/",
        "test_images/02_real_photographs/",
        "test_images/03_political_misinfo/",
        "test_images/04_financial_fraud/",
        "test_images/05_disaster_misinfo/",
        "test_images/06_identity_impersonation/",
        "test_images/07_satire_low_risk/",
        "test_images/claims/"
    ]
    
    print("=== STEP 1: Verifying Folders ===")
    folders_present = 0
    for folder in folders:
        # Normalize path separators for os.path.exists
        normalized = folder.replace('/', os.sep)
        if os.path.exists(normalized):
            print(f"OK: {folder}")
            folders_present += 1
        else:
            print(f"MISSING: {folder}")

    print("\n=== STEP 2: Verifying Image Files ===")
    images = [
        "test_images/01_ai_generated_faces/face_01.jpg",
        "test_images/01_ai_generated_faces/face_02.jpg",
        "test_images/01_ai_generated_faces/face_03.jpg",
        "test_images/01_ai_generated_faces/face_04.jpg",
        "test_images/01_ai_generated_faces/face_05.jpg",
        "test_images/02_real_photographs/real_01.jpg",
        "test_images/02_real_photographs/real_02.jpg",
        "test_images/02_real_photographs/real_03.jpg",
        "test_images/03_political_misinfo/politician_fake_01.jpg",
        "test_images/03_political_misinfo/politician_fake_02.jpg",
        "test_images/04_financial_fraud/bank_official_fake_01.jpg",
        "test_images/04_financial_fraud/bank_official_fake_02.jpg",
        "test_images/05_disaster_misinfo/disaster_real_01.jpg",
        "test_images/05_disaster_misinfo/disaster_real_02.jpg",
        "test_images/06_identity_impersonation/impersonation_01.jpg",
        "test_images/06_identity_impersonation/impersonation_02.jpg",
        "test_images/07_satire_low_risk/satire_01.jpg",
        "test_images/07_satire_low_risk/satire_02.jpg"
    ]
    
    images_present = 0
    empty_files = 0
    
    for img in images:
        normalized = img.replace('/', os.sep)
        if os.path.exists(normalized):
            size = os.path.getsize(normalized)
            if size == 0:
                print(f"EMPTY: {img} — file downloaded but has no content")
                empty_files += 1
            else:
                size_kb = size / 1024.0
                print(f"OK: {img} ({size_kb:.1f}KB)")
                images_present += 1
        else:
            print(f"MISSING: {img}")

    print("\n=== STEP 3: Verifying test_claims.json ===")
    json_path = os.path.join("test_images", "claims", "test_claims.json")
    json_valid_cases = 0
    json_all_fields_valid = False
    
    if not os.path.exists(json_path):
        print("MISSING: test_claims.json")
    else:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            case_count = len(data)
            print(f"OK: test_claims.json contains {case_count} test cases")
            
            required_fields = [
                "test_id", "folder", "image_file", "claim_text",
                "expected_risk_level", "expected_harm_category", "purpose"
            ]
            
            all_valid = True
            valid_count = 0
            for case in data:
                test_id = case.get("test_id", "UNKNOWN")
                case_valid = True
                for field in required_fields:
                    val = case.get(field)
                    if val is None or val == "":
                        print(f"INVALID: {test_id} missing field {field}")
                        all_valid = False
                        case_valid = False
                if case_valid:
                    valid_count += 1
            
            json_valid_cases = valid_count
            if all_valid and case_count == 14:
                print("OK: All 14 test cases have complete fields")
                json_all_fields_valid = True
            else:
                if case_count != 14:
                    print(f"INVALID: test_claims.json has {case_count} cases, expected 14")
        except Exception as e:
            print(f"INVALID: Failed to load/verify JSON: {e}")

    # STEP 4 — Print summary
    # STATUS is READY if Folders == 8, Images == 18, Empty == 0, JSON cases == 14
    if folders_present == 8 and images_present == 18 and empty_files == 0 and json_valid_cases == 14:
        status_text = "READY"
    else:
        status_text = "ISSUES FOUND — run download_test_images.py again"
        
    print("\n  ========================================")
    print("  TRUTHGUARD TEST LIBRARY VERIFICATION")
    print("  ========================================")
    print(f"  Folders   : {folders_present}/8 present")
    print(f"  Images    : {images_present}/18 present")
    print(f"  Empty     : {empty_files} files have 0 bytes")
    print(f"  JSON cases: {json_valid_cases}/14 valid")
    print("  ----------------------------------------")
    print(f"  STATUS: {status_text}")
    print("  ========================================")

    # STEP 5 — Print the first test case to run
    print("\n  ----------------------------------------")
    print("  FIRST TEST CASE TO RUN IN STREAMLIT")
    print("  ----------------------------------------")
    print("  Test ID  : PM-01")
    print("  Image    : test_images/03_political_misinfo/politician_fake_01.jpg")
    print("  Claim    : This image shows a state minister accepting cash from a")
    print("             contractor in Chennai. The video is going viral on")
    print("             WhatsApp groups across Tamil Nadu ahead of the election.")
    print("  Expected : Critical — Political Misinformation")
    print("  ----------------------------------------")

if __name__ == "__main__":
    main()
