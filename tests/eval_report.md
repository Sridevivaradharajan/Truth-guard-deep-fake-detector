# TruthGuard Agent Evaluation Report

**Overall Criteria Pass Rate**: 100.0% (20/20 criteria passed)

## Evaluation Results Table

| Test ID | Description | Expected Category | Actual Category | Expected Risk | Actual Risk | Criteria Checked (1-4) | Status |
|---|---|---|---|---|---|---|---|
| TC01 | AI face image with political claim | Political Misinformation | Political Misinformation | Critical | Critical | risk_level: ✓, category: ✓, action: ✓, complete: ✓ | ✅ PASS |
| TC02 | Real photo with intact EXIF and true claim | Entertainment / Low Risk | Entertainment / Low Risk | Low | Low | risk_level: ✓, category: ✓, action: ✓, complete: ✓ | ✅ PASS |
| TC03 | Real photo with stripped metadata and identity claim | Identity Impersonation | Identity Impersonation | Medium | Medium | risk_level: ✓, category: ✓, action: ✓, complete: ✓ | ✅ PASS |
| TC04 | AI satire image with clear humorous label | Entertainment / Low Risk | Entertainment / Low Risk | Low | Low | risk_level: ✓, category: ✓, action: ✓, complete: ✓ | ✅ PASS |
| TC05 | Face-swap bank official with UPI fraud claim | Financial Fraud | Financial Fraud | Critical | Critical | risk_level: ✓, category: ✓, action: ✓, complete: ✓ | ✅ PASS |

## Failure Details

All cases successfully met expected risk, category classification, and actionable criteria guidelines.