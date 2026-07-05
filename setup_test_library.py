import os

def main():
    # Folder structure to create under test_images/
    subfolders = [
        "01_ai_generated_faces",
        "02_real_photographs",
        "03_political_misinfo",
        "04_financial_fraud",
        "05_disaster_misinfo",
        "06_identity_impersonation",
        "07_satire_low_risk",
        "claims"
    ]

    # Create directories and print confirmation
    for folder in subfolders:
        path = os.path.join("test_images", folder)
        os.makedirs(path, exist_ok=True)
        print(f"Created: test_images/{folder}/")

    # Content for test_images/README.md
    readme_content = """# TruthGuard Test Image Library

This folder is excluded from Git. Never commit images to the repository.

## Folders

| Folder | Use Case | Expected Risk |
|--------|----------|---------------|
| 01_ai_generated_faces | Visual forensics calibration | High |
| 02_real_photographs | Baseline false-positive check | Low |
| 03_political_misinfo | Election misinformation — primary demo case | Critical |
| 04_financial_fraud | UPI and banking fraud scenarios | Critical |
| 05_disaster_misinfo | Real image with false claim — context layer test | High |
| 06_identity_impersonation | Celebrity and corporate impersonation | High |
| 07_satire_low_risk | Satire and clearly labelled synthetic content | Low |

## How to Run a Test
1. Open Streamlit: streamlit run streamlit_app.py
2. Open test_images/claims/test_claims.json
3. Find the test_id you want to run
4. Upload the image listed in image_file
5. Paste the claim_text exactly as written
6. Click Run Investigation
7. Compare actual output to expected_risk_level and expected_harm_category
8. Download the evidence bundle and confirm 5 files are inside the ZIP

## Demo Video Order
1. PM-01 — political misinformation, highest impact, run this first
2. DM-01 — real image with false claim, proves context layer works
3. RP-01 — real photo cleared correctly, proves no false positives
4. FF-01 — UPI fraud, most recognisable scenario for Indian audience

## Image Sources
- AI faces: https://100k-faces.vercel.app (free AI faces API)
- Real, disaster, and art photos: https://loremflickr.com (free placeholder API)
- Never use screenshots or images of real named individuals"""

    readme_path = os.path.join("test_images", "README.md")
    
    # Write the README.md
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
        
    print("Created: test_images/README.md")
    print("Test image library structure created successfully.")

if __name__ == "__main__":
    main()
