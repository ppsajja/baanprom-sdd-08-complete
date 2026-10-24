# ตารางผล AC หลังรัน test ทั้งชุด (specs/000-shared/test-run.txt)

รันวันที่ 10 ธ.ค. 2569 (วันในเคส) จาก export สะอาด Python 3.11 และ 3.12 และ vitest

| AC หรือ UI | REQ ที่พิสูจน์ | test | task | ผล | หมายเหตุ |
|---|---|---|---|---|---|
| AC-13-01 | REQ-FN-070 | test_AC_13_01_all_matched | T-01 | ผ่าน | |
| AC-13-02, AC-13-03, AC-13-04 | REQ-FN-070 | test_AC_13_02_03_04_differences_listed | T-01 | ผ่าน | |
| AC-13-05 | REQ-FN-071 | test_AC_13_05_unknown_refund_resolved_success | T-02 | ผ่าน | พิสูจน์ชั้น 3 ใน T-02 |
| AC-13-06 | REQ-FN-071 | test_AC_13_06_unknown_refund_failed_or_absent | T-02 | ผ่าน | |
| AC-13-07 | REQ-SEC-015 | test_AC_13_07_finance_key_only, UI-13-01.test.jsx | T-03 | ผ่าน | |
| AC-13-08 | REQ-FN-070 | test_AC_13_08_bad_file_and_duplicate_import, UI-13-01.test.jsx | T-01, T-03 | ผ่าน | |
| UI-13-01 | REQ-FN-070 | UI-13-01.test.jsx (3 test) | T-04 | ผ่าน | |
