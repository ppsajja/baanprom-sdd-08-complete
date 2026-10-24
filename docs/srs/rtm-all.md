# ตารางตามรอยทั้งระบบ (EV ถึง REQ ถึง UC ถึง AC ถึง test) Baseline B7

ไฟล์นี้สร้างโดย scripts/check_rtm.py ห้ามแก้ด้วยมือ รันใหม่ทุกครั้งที่ .feature catalogue หรือ test เปลี่ยน
rtm.md ของแต่ละ feature ยังเป็นที่ของการตามรอยถึง task โค้ด หน้าจอ ข้อค้นพบ และช่อง "ทีมตัดสิน" ไฟล์นี้ตรวจเฉพาะว่าสายไม่ขาด

สรุป: UC 14 จาก 14 | AC 146 ข้อ มี test 146 ข้อ | REQ ที่ AC อ้าง 70 ข้อ | สายขาด 0

## 1. ราย use case

| UC | AC | REQ ที่ AC อ้าง | ที่มา (EV) ของ REQ เหล่านั้น |
|---|---|---|---|
| UC-01 | 3 ข้อ (AC-01-01 ถึง AC-01-03) | REQ-FN-060, REQ-SEC-010, REQ-SEC-013, REQ-SEC-014 | EV-045, EV-051 |
| UC-02 | 14 ข้อ (AC-02-01 ถึง AC-02-14) | REQ-FN-008, REQ-FN-058, REQ-FN-059, REQ-FN-074, REQ-PRV-002, REQ-PRV-010, REQ-PRV-011, REQ-QA-010, REQ-SEC-010, REQ-SEC-012, REQ-SEC-013, REQ-SEC-014 | EV-004, EV-009, EV-045, EV-051, EV-053 |
| UC-03 | 2 ข้อ (AC-07-02, AC-07-08) | REQ-FN-008, REQ-QA-003 | EV-004, EV-007, EV-009, EV-048, EV-051 |
| UC-04 | 8 ข้อ (AC-04-01 ถึง AC-04-08) | REQ-FN-066, REQ-FN-067, REQ-SEC-010, REQ-SEC-014 | EV-045, EV-051, EV-053 |
| UC-05 | 6 ข้อ (AC-05-01 ถึง AC-05-06) | REQ-BR-001, REQ-FN-061, REQ-FN-062, REQ-FN-063, REQ-SEC-010 | EV-023, EV-045, EV-051 |
| UC-06 | 5 ข้อ (AC-07-01, AC-07-05, AC-07-06, AC-07-12, AC-07-13) | REQ-FN-008, REQ-FN-041, REQ-IF-001, REQ-IF-005, REQ-QA-010 | EV-004, EV-009, EV-045, EV-048 |
| UC-07 | 24 ข้อ (AC-07-01 ถึง AC-07-24) | REQ-BR-001, REQ-BR-002, REQ-FN-008, REQ-FN-012, REQ-FN-041, REQ-FN-057, REQ-FN-064, REQ-FN-065, REQ-IF-001, REQ-IF-005, REQ-OP-007, REQ-PRV-002, REQ-PRV-010, REQ-QA-003, REQ-QA-010, REQ-SEC-004, REQ-SEC-010, REQ-SEC-011, REQ-SEC-012 | EV-004, EV-007, EV-009, EV-012, EV-019, EV-023, EV-045, EV-048, EV-049, EV-051 |
| UC-08 | 12 ข้อ (AC-08-01 ถึง AC-08-12) | REQ-BR-001, REQ-CON-003, REQ-DAT-002, REQ-DAT-003, REQ-FN-054, REQ-FN-055, REQ-IF-010, REQ-OP-001, REQ-QA-010, REQ-SEC-010 | EV-012, EV-023, EV-044, EV-045, EV-048 |
| UC-09 | 16 ข้อ (AC-09-01 ถึง AC-09-16) | REQ-DAT-002, REQ-FN-050, REQ-FN-051, REQ-FN-052, REQ-FN-053, REQ-OP-001, REQ-PRV-002, REQ-QA-010, REQ-SEC-004, REQ-SEC-010 | EV-012, EV-019, EV-044, EV-045 |
| UC-10 | 7 ข้อ (AC-10-01 ถึง AC-10-07) | REQ-FN-072, REQ-FN-073, REQ-PRV-002, REQ-PRV-010, REQ-SEC-013 | EV-045, EV-051, EV-053 |
| UC-11 | 8 ข้อ (AC-11-01 ถึง AC-11-08) | REQ-FN-068, REQ-FN-069, REQ-PRV-012, REQ-SEC-010 | EV-045, EV-053 |
| UC-12 | 5 ข้อ (AC-12-01 ถึง AC-12-05) | REQ-FN-061, REQ-SEC-010 | EV-045, EV-051 |
| UC-13 | 8 ข้อ (AC-13-01 ถึง AC-13-08) | REQ-FN-070, REQ-FN-071, REQ-IF-010, REQ-SEC-015 | EV-044, EV-048, EV-053 |
| UC-14 | 19 ข้อ (AC-14-01 ถึง AC-14-19) | REQ-AI-005, REQ-AI-006, REQ-AI-007, REQ-AI-008, REQ-AI-009, REQ-AI-010, REQ-AI-011, REQ-AI-012, REQ-AI-013, REQ-AI-020, REQ-AI-021, REQ-AI-022, REQ-AI-023, REQ-DAT-010, REQ-FN-056, REQ-FN-075, REQ-SEC-010, REQ-SEC-015 | EV-012, EV-045, EV-046, EV-047, EV-053 |

AC-00 (ข้ามทุก feature) ไม่ใช่ของ use case ใด อยู่ในส่วน 2 ด้วย

## 2. ราย AC

| AC | UC | REQ | test |
|---|---|---|---|
| AC-00-01 | ข้ามทุก feature | REQ-OP-005 | test_cross_cutting.py::test_AC_00_01_metrics_per_endpoint_per_minute |
| AC-00-02 | ข้ามทุก feature | REQ-OP-005 | test_cross_cutting.py::test_AC_00_02_page_on_call_after_5_failing_minutes; test_cross_cutting_cr10.py::test_AC_00_02_webhook_pager_reaches_on_call; test_cross_cutting_cr10.py::test_AC_00_02_webhook_pager_retries_next_minute_when_service_fails |
| AC-00-03 | ข้ามทุก feature | REQ-OP-005, REQ-PRV-002 | test_cross_cutting.py::test_AC_00_03_structured_log_without_pii; test_cross_cutting_def02.py::test_AC_00_03_production_app_writes_structured_log_to_stdout |
| AC-00-04 | ข้ามทุก feature | REQ-OP-001 | test_cross_cutting.py::test_AC_00_04_health_and_ready |
| AC-00-05 | ข้ามทุก feature | REQ-OP-007 | test_cross_cutting.py::test_AC_00_05_backup_restore_drill_within_rpo |
| AC-00-06 | ข้ามทุก feature | REQ-SEC-012 | test_cross_cutting.py::test_AC_00_06_production_hides_docs_and_guards_ops_endpoints |
| AC-00-07 | ข้ามทุก feature | REQ-SEC-012 | test_cross_cutting.py::test_AC_00_07_now_parameter_ignored_outside_test_mode |
| AC-00-08 | ข้ามทุก feature | REQ-SEC-010 | test_cross_cutting.py::test_AC_00_08_page_when_one_actor_denied_over_20_in_10_minutes |
| AC-00-09 | ข้ามทุก feature | REQ-OP-008 | test_cross_cutting_cr13.py::test_AC_00_09_queued_messages_survive_restart |
| AC-00-10 | ข้ามทุก feature | REQ-OP-008 | test_cross_cutting_cr13.py::test_AC_00_10_one_process_holds_the_scheduler_lease |
| AC-00-11 | ข้ามทุก feature | REQ-OP-008, REQ-OP-005 | test_cross_cutting_cr13.py::test_AC_00_11_metrics_from_two_processes_add_up |
| AC-00-12 | ข้ามทุก feature | REQ-IF-012, REQ-OP-009 | test_cross_cutting_r2b.py::test_AC_00_12_adapters_switch_by_config |
| AC-00-13 | ข้ามทุก feature | REQ-IF-012, REQ-QA-010 | test_cross_cutting_r2b.py::test_AC_00_13_real_adapters_follow_contract_without_network; test_cross_cutting_r2b.py::test_AC_00_13_llm_down_assistant_uses_code_fallback |
| AC-00-14 | ข้ามทุก feature | REQ-QA-010 | test_cross_cutting_r2b.py::test_AC_00_14_map_down_search_uses_straight_line |
| AC-00-15 | ข้ามทุก feature | REQ-SEC-015 | test_cross_cutting_r2b.py::test_AC_00_15_role_keys |
| AC-00-16 | ข้ามทุก feature | REQ-OP-005 | test_cross_cutting_r2b.py::test_AC_00_16_metrics_count_real_searches |
| AC-01-01 | UC-01 | REQ-FN-060, REQ-SEC-014 | test_identity.py::test_AC_01_01_technician_logs_in_with_issued_account |
| AC-01-02 | UC-01 | REQ-FN-060, REQ-SEC-013 | test_identity.py::test_AC_01_02_unknown_technician_phone_gets_same_answer_but_no_sms |
| AC-01-03 | UC-01 | REQ-SEC-010, REQ-SEC-014 | test_identity.py::test_AC_01_03_technician_token_limited_to_own_menu_and_jobs; AC-02-06.test.jsx |
| AC-02-01 | UC-02 | REQ-FN-058, REQ-SEC-013, REQ-PRV-011 | test_identity.py::test_AC_02_01_new_customer_registers_with_phone_and_otp |
| AC-02-02 | UC-02 | REQ-FN-059, REQ-SEC-014 | test_identity.py::test_AC_02_02_registered_customer_logs_in |
| AC-02-03 | UC-02 | REQ-SEC-013 | test_identity.py::test_AC_02_03_otp_expires_after_5_minutes |
| AC-02-04 | UC-02 | REQ-SEC-013 | test_identity.py::test_AC_02_04_five_wrong_codes_lock_the_challenge |
| AC-02-05 | UC-02 | REQ-SEC-013 | test_identity.py::test_AC_02_05_resend_limits_and_old_code_replaced |
| AC-02-06 | UC-02 | REQ-SEC-014 | test_identity.py::test_AC_02_06_identity_comes_from_token_only; AC-02-06.test.jsx |
| AC-02-07 | UC-02 | REQ-SEC-010 | test_identity.py::test_AC_02_07_job_and_history_need_owner_assignee_or_call_center |
| AC-02-08 | UC-02 | REQ-SEC-013, REQ-PRV-002 | test_identity.py::test_AC_02_08_no_code_or_phone_in_log_or_db |
| AC-02-09 | UC-02 | REQ-PRV-010, REQ-SEC-014 | test_identity.py::test_AC_02_09_erasure_removes_account_and_sessions |
| AC-02-10 | UC-02 | REQ-FN-058, REQ-FN-008 | test_identity.py::test_AC_02_10_multiple_addresses_choose_when_searching; AC-07-20.test.jsx |
| AC-02-11 | UC-02 | REQ-SEC-012, REQ-SEC-013 | test_identity.py::test_AC_02_11_production_never_returns_the_code |
| AC-02-12 | UC-02 | REQ-FN-074, REQ-PRV-011 | test_addresses.py::test_AC_02_12_add_address_geocoded |
| AC-02-13 | UC-02 | REQ-FN-074, REQ-QA-010 | test_addresses.py::test_AC_02_13_address_not_found_or_map_down; UI-02-04.test.jsx |
| AC-02-14 | UC-02 | REQ-FN-074, REQ-SEC-010 | test_addresses.py::test_AC_02_14_delete_address_rules |
| AC-04-01 | UC-04 | REQ-FN-066 | test_schedule.py::test_AC_04_01_add_slot_visible_in_search; UI-04-01.test.jsx |
| AC-04-02 | UC-04 | REQ-FN-066 | test_schedule.py::test_AC_04_02_rules_reject |
| AC-04-03 | UC-04 | REQ-FN-066 | test_schedule.py::test_AC_04_03_close_free_slot_hidden_everywhere |
| AC-04-04 | UC-04 | REQ-FN-066 | test_schedule.py::test_AC_04_04_cannot_close_booked_or_held |
| AC-04-05 | UC-04 | REQ-FN-067 | test_schedule.py::test_AC_04_05_day_off_hides_slots_and_rematch |
| AC-04-06 | UC-04 | REQ-FN-067 | test_schedule.py::test_AC_04_06_day_off_refused_when_booked; UI-04-01.test.jsx |
| AC-04-07 | UC-04 | REQ-FN-067 | test_schedule.py::test_AC_04_07_remove_day_off_reopens_only_its_slots |
| AC-04-08 | UC-04 | REQ-SEC-010, REQ-SEC-014 | test_schedule.py::test_AC_04_08_other_technician_and_customer_denied |
| AC-05-01 | UC-05 | REQ-FN-062, REQ-SEC-010 | test_accept_rematch.py::test_AC_05_01_reject_rematches_to_nearest_free_technician_same_time; AC-12-01.test.jsx |
| AC-05-02 | UC-05 | REQ-FN-063, REQ-BR-001 | test_accept_rematch.py::test_AC_05_02_no_substitute_within_2_hours_cancels_with_full_refund |
| AC-05-03 | UC-05 | REQ-FN-061, REQ-FN-062 | test_accept_rematch.py::test_AC_05_03_no_response_in_30_minutes_counts_as_reject |
| AC-05-04 | UC-05 | REQ-FN-063, REQ-BR-001 | test_accept_rematch.py::test_AC_05_04_customer_declines_substitute_full_refund; UI-02-03.test.jsx |
| AC-05-05 | UC-05 | REQ-FN-062 | test_accept_rematch.py::test_AC_05_05_order_by_distance_skip_tried_and_wrong_skill |
| AC-05-06 | UC-05 | REQ-FN-062, REQ-FN-063 | test_accept_rematch.py::test_AC_05_06_out_of_range_and_too_close_to_start_not_matched |
| AC-07-01 | UC-07 | REQ-FN-008 | test_booking.py::test_AC_07_01_booking_success |
| AC-07-02 | UC-07 | REQ-FN-008 | test_booking.py::test_AC_07_02_slot_not_rebookable |
| AC-07-03 | UC-07 | REQ-FN-012 | test_booking.py::test_AC_07_03_notify_both_within_60s |
| AC-07-04 | UC-07 | REQ-FN-041 | test_booking.py::test_AC_07_04_no_charge_when_slot_taken; AC-07-04.test.jsx |
| AC-07-05 | UC-07 | REQ-IF-001, REQ-IF-005 | test_payment.py::test_AC_07_05_payment_timeout |
| AC-07-06 | UC-07 | REQ-IF-001 | test_payment.py::test_AC_07_06_payment_declined; AC-07-06.test.jsx |
| AC-07-07 | UC-07 | REQ-IF-005 | test_payment.py::test_AC_07_07_inquiry_approved_no_double_charge |
| AC-07-08 | UC-07 | REQ-QA-003 | test_load_scaled.py::test_AC_07_08_search_under_load_scaled |
| AC-07-09 | UC-07 | REQ-SEC-004, REQ-PRV-002 | test_privacy.py::test_AC_07_09_phone_hidden_until_2h |
| AC-07-10 | UC-07 | REQ-BR-001 | test_refund.py::test_AC_07_10_refund; test_refund.py::test_AC_07_10_refund_R6_not_allowed; test_refund.py::test_AC_07_10_refund_R3 |
| AC-07-11 | UC-07 | REQ-BR-002 | test_deposit.py::test_AC_07_11_deposit_shown_equals_charged; test_deposit.py::test_AC_07_11_unknown_category_has_no_guessed_deposit; AC-07-11.test.jsx |
| AC-07-12 | UC-07 | REQ-QA-010, REQ-FN-041 | test_booking_cr07.py::test_AC_07_12_gateway_unreachable_keeps_hold_as_pending; AC-07-12.test.jsx |
| AC-07-13 | UC-07 | REQ-QA-010, REQ-IF-005 | test_booking_cr07.py::test_AC_07_13_retry_uses_same_reference_no_double_charge; AC-07-12.test.jsx |
| AC-07-14 | UC-07 | REQ-SEC-011 | test_booking_cr07.py::test_AC_07_14_second_hold_rejected; AC-07-14.test.jsx |
| AC-07-15 | UC-07 | REQ-SEC-010, REQ-SEC-004 | test_booking_cr07.py::test_AC_07_15_technician_view_other_job_forbidden_and_logged |
| AC-07-16 | UC-07 | REQ-SEC-010, REQ-SEC-012 | test_booking_cr07.py::test_AC_07_16_legacy_cancel_endpoint_closed |
| AC-07-17 | UC-07 | REQ-PRV-010 | test_erasure.py::test_AC_07_17_erasure_removes_phone_keeps_anonymous_history; test_erasure.py::test_AC_07_17_erasure_waits_for_active_job |
| AC-07-18 | UC-07 | REQ-PRV-010, REQ-OP-007 | test_erasure.py::test_AC_07_18_restore_does_not_bring_back_erased_data |
| AC-07-19 | UC-07 | REQ-FN-057, REQ-BR-002 | test_booking_cr10.py::test_AC_07_19_estimate_and_deposit_from_same_table; AC-07-19.test.jsx |
| AC-07-20 | UC-07 | REQ-FN-064 | test_booking_cr08.py::test_AC_07_20_book_past_technician_when_free; AC-07-20.test.jsx |
| AC-07-21 | UC-07 | REQ-FN-064 | test_booking_cr08.py::test_AC_07_21_past_technician_not_free_in_7_days; AC-07-20.test.jsx |
| AC-07-22 | UC-07 | REQ-FN-064 | test_booking_cr08.py::test_AC_07_22_past_technician_out_of_range_for_chosen_address |
| AC-07-23 | UC-07 | REQ-FN-064, REQ-SEC-010 | test_booking_cr08.py::test_AC_07_23_only_own_done_jobs_count |
| AC-07-24 | UC-07 | REQ-FN-065 | test_booking_cr08.py::test_AC_07_24_no_technician_in_7_days; AC-07-20.test.jsx |
| AC-08-01 | UC-08 | REQ-FN-054, REQ-BR-001 | test_cancel.py::test_AC_08_01_quote_equals_actual_refund; test_cancel.py::test_AC_08_01_other_customer_cannot_see_or_cancel; AC-08-01.test.jsx |
| AC-08-02 | UC-08 | REQ-FN-054, REQ-DAT-002, REQ-DAT-003 | test_cancel.py::test_AC_08_02_cancel_sets_status_history_and_frees_slot |
| AC-08-03 | UC-08 | REQ-IF-010, REQ-CON-003 | test_cancel.py::test_AC_08_03_refund_sent_via_gateway_with_same_ref |
| AC-08-04 | UC-08 | REQ-IF-010 | test_cancel.py::test_AC_08_04_second_cancel_rejected_no_double_refund |
| AC-08-05 | UC-08 | REQ-FN-055 | test_cancel.py::test_AC_08_05_notify_customer_and_technician_within_60s |
| AC-08-06 | UC-08 | REQ-BR-001, REQ-FN-054 | test_cancel.py::test_AC_08_06_not_cancellable_returns_message; AC-08-06.test.jsx |
| AC-08-07 | UC-08 | REQ-IF-010, REQ-QA-010 | test_cancel_cr07.py::test_AC_08_07_two_concurrent_cancels_refund_once |
| AC-08-08 | UC-08 | REQ-QA-010, REQ-IF-010 | test_cancel_cr07.py::test_AC_08_08_refund_timeout_recorded_unknown_not_resent |
| AC-08-09 | UC-08 | REQ-OP-001, REQ-FN-054 | test_cancel_cr07.py::test_AC_08_09_cancel_under_load_scaled |
| AC-08-10 | UC-08 | REQ-SEC-010 | test_cancel_cr07.py::test_AC_08_10_customer_cannot_cancel_other_customers_job; AC-08-10.test.jsx |
| AC-08-11 | UC-08 | REQ-IF-010 | test_cancel_cr10.py::test_AC_08_11_gateway_declines_refund_no_retry_finance_follow_up; AC-08-11.test.jsx |
| AC-08-12 | UC-08 | REQ-BR-001, REQ-FN-054, REQ-FN-055 | test_cancel_cr10.py::test_AC_08_12_cancel_while_en_route_deducts_travel_fee; AC-08-12.test.jsx |
| AC-09-01 | UC-09 | REQ-FN-050 | test_job_status.py::test_AC_09_01_technician_sees_only_own_jobs |
| AC-09-02 | UC-09 | REQ-FN-051, REQ-DAT-002 | test_job_status.py::test_AC_09_02_en_route_recorded; AC-09-02.test.jsx |
| AC-09-03 | UC-09 | REQ-FN-051 | test_job_status.py::test_AC_09_03_check_in_then_AC_09_04_close |
| AC-09-04 | UC-09 | REQ-FN-051 | test_job_status.py::test_AC_09_03_check_in_then_AC_09_04_close |
| AC-09-05 | UC-09 | REQ-FN-051 | test_job_status.py::test_AC_09_05_transition_not_allowed; AC-09-05.test.jsx |
| AC-09-06 | UC-09 | REQ-FN-051 | test_job_status.py::test_AC_09_06_other_technician_cannot_change |
| AC-09-07 | UC-09 | REQ-FN-052 | test_job_status.py::test_AC_09_07_customer_and_call_center_see_same_status |
| AC-09-08 | UC-09 | REQ-FN-053 | test_job_status.py::test_AC_09_08_notify_customer_within_60s_on_each_change |
| AC-09-09 | UC-09 | REQ-SEC-004, REQ-PRV-002 | test_job_status_privacy.py::test_AC_09_09_phone_in_job_list_only_from_2h_until_closed |
| AC-09-10 | UC-09 | REQ-DAT-002 | test_job_status.py::test_AC_09_10_history_complete_in_order |
| AC-09-11 | UC-09 | REQ-FN-053, REQ-QA-010 | test_job_status_cr07.py::test_AC_09_11_messages_accepted_by_if02_within_60s |
| AC-09-12 | UC-09 | REQ-OP-001, REQ-FN-051 | test_job_status_cr07.py::test_AC_09_12_status_change_under_load_scaled |
| AC-09-13 | UC-09 | REQ-QA-010 | test_job_status_cr07.py::test_AC_09_13_if02_down_status_saved_message_resent_once; test_job_status_cr07.py::test_AC_09_13_if02_down_beyond_retries_gives_up_after_6 |
| AC-09-14 | UC-09 | REQ-SEC-010 | test_job_status_cr07.py::test_AC_09_14_denied_status_change_logged_without_leaking_existence |
| AC-09-15 | UC-09 | REQ-FN-051, REQ-FN-053 | test_job_status_cr10.py::test_AC_09_15_done_without_customer_confirm_and_message_tells_how_to_report |
| AC-09-16 | UC-09 | REQ-FN-050 | test_job_status_cr12.py::test_AC_09_16_closed_jobs_shown_30_days_back |
| AC-10-01 | UC-10 | REQ-FN-072 | test_notifications.py::test_AC_10_01_default_sms |
| AC-10-02 | UC-10 | REQ-FN-072 | test_notifications.py::test_AC_10_02_link_and_choose_line; UI-10-01.test.jsx |
| AC-10-03 | UC-10 | REQ-FN-072 | test_notifications.py::test_AC_10_03_line_requires_valid_link |
| AC-10-04 | UC-10 | REQ-FN-073 | test_notifications.py::test_AC_10_04_line_down_falls_back_to_sms |
| AC-10-05 | UC-10 | REQ-FN-072, REQ-SEC-013 | test_notifications.py::test_AC_10_05_otp_always_sms |
| AC-10-06 | UC-10 | REQ-FN-072 | test_notifications.py::test_AC_10_06_technician_line_and_new_job_text |
| AC-10-07 | UC-10 | REQ-FN-073, REQ-PRV-010, REQ-PRV-002 | test_notifications.py::test_AC_10_07_erasure_and_no_pii_in_delivery_log |
| AC-11-01 | UC-11 | REQ-FN-068 | test_rating.py::test_AC_11_01_rate_done_job |
| AC-11-02 | UC-11 | REQ-FN-068 | test_rating.py::test_AC_11_02_not_done_cannot_rate; test_rating.py::test_AC_11_02_stars_must_be_1_to_5 |
| AC-11-03 | UC-11 | REQ-FN-068 | test_rating.py::test_AC_11_03_only_once_per_job; UI-11-01.test.jsx |
| AC-11-04 | UC-11 | REQ-FN-068 | test_rating.py::test_AC_11_04_window_14_days |
| AC-11-05 | UC-11 | REQ-SEC-010 | test_rating.py::test_AC_11_05_other_customer_denied |
| AC-11-06 | UC-11 | REQ-FN-069 | test_rating.py::test_AC_11_06_average_shown_not_used_for_order; AC-11-06.test.jsx |
| AC-11-07 | UC-11 | REQ-PRV-012 | test_rating.py::test_AC_11_07_comment_masked_and_private |
| AC-11-08 | UC-11 | REQ-FN-068, REQ-PRV-012 | test_rating.py::test_AC_11_08_self_review_not_counted_and_erasure |
| AC-12-01 | UC-12 | REQ-FN-061 | test_accept_rematch.py::test_AC_12_01_new_job_offered_with_accept_and_reject; AC-12-01.test.jsx |
| AC-12-02 | UC-12 | REQ-FN-061 | test_accept_rematch.py::test_AC_12_02_accept_keeps_status_and_hides_accept_button; AC-12-01.test.jsx |
| AC-12-03 | UC-12 | REQ-FN-061 | test_accept_rematch.py::test_AC_12_03_departure_counts_as_accept |
| AC-12-04 | UC-12 | REQ-SEC-010 | test_accept_rematch.py::test_AC_12_04_other_technician_cannot_respond |
| AC-12-05 | UC-12 | REQ-FN-061 | test_accept_rematch.py::test_AC_12_05_cannot_reject_after_departure; AC-12-01.test.jsx |
| AC-13-01 | UC-13 | REQ-FN-070 | test_reconciliation.py::test_AC_13_01_all_matched |
| AC-13-02 | UC-13 | REQ-FN-070 | test_reconciliation.py::test_AC_13_02_03_04_differences_listed |
| AC-13-03 | UC-13 | REQ-FN-070 | test_reconciliation.py::test_AC_13_02_03_04_differences_listed |
| AC-13-04 | UC-13 | REQ-FN-070 | test_reconciliation.py::test_AC_13_02_03_04_differences_listed |
| AC-13-05 | UC-13 | REQ-FN-071, REQ-IF-010 | test_reconciliation.py::test_AC_13_05_unknown_refund_resolved_success |
| AC-13-06 | UC-13 | REQ-FN-071 | test_reconciliation.py::test_AC_13_06_unknown_refund_failed_or_absent |
| AC-13-07 | UC-13 | REQ-SEC-015 | test_reconciliation.py::test_AC_13_07_finance_key_only; UI-13-01.test.jsx |
| AC-13-08 | UC-13 | REQ-FN-070 | test_reconciliation.py::test_AC_13_08_bad_file_and_duplicate_import; UI-13-01.test.jsx |
| AC-14-01 | UC-14 | REQ-AI-005 | test_assistant_eval.py::test_AC_14_01_status_correct_on_eval_set |
| AC-14-02 | UC-14 | REQ-AI-005 | test_assistant_eval.py::test_AC_14_02_refuse_out_of_scope_not_answerable |
| AC-14-03 | UC-14 | REQ-AI-006 | test_assistant_eval.py::test_AC_14_03_grounded_or_says_no_data |
| AC-14-04 | UC-14 | REQ-AI-007 | test_assistant_eval.py::test_AC_14_04_forbidden_and_no_phone_anywhere |
| AC-14-05 | UC-14 | REQ-AI-008 | test_assistant.py::test_AC_14_05_output_guard_blocks_bad_answers; test_assistant_eval.py::test_AC_14_05_prompt_injection_30_of_30 |
| AC-14-06 | UC-14 | REQ-DAT-010 | test_assistant.py::test_AC_14_06_policy_matches_baseline; test_assistant.py::test_AC_14_06_facts_have_no_pii_and_are_fresh; test_assistant.py::test_AC_14_06_customer_text_masked_before_llm; test_assistant_eval.py::test_AC_14_06_rights_eta_and_context |
| AC-14-07 | UC-14 | REQ-AI-009 | test_assistant.py::test_AC_14_07_rate_and_length_limits |
| AC-14-08 | UC-14 | REQ-AI-010 | test_assistant.py::test_AC_14_08_closed_tool_list |
| AC-14-09 | UC-14 | REQ-AI-011 | test_assistant_eval.py::test_AC_14_09_reschedule_only_after_confirmation; AC-14-09.test.jsx |
| AC-14-10 | UC-14 | REQ-AI-012 | test_assistant.py::test_AC_14_10_stop_unclear_intent; test_assistant.py::test_AC_14_10_stop_tool_timeout_no_retry; test_assistant.py::test_AC_14_10_stop_after_two_declines; test_assistant.py::test_AC_14_10_stop_beyond_rule; test_assistant_r2b.py::test_AC_14_10_tool_timeout_after_effect_not_called_again |
| AC-14-11 | UC-14 | REQ-AI-013 | test_assistant.py::test_AC_14_11_action_log_complete_and_no_pii; test_assistant.py::test_AC_14_11_erasure_clears_customer_text |
| AC-14-12 | UC-14 | REQ-AI-020 | test_assistant.py::test_AC_14_12_greeting_and_sources; AC-14-12.test.jsx |
| AC-14-13 | UC-14 | REQ-AI-021 | test_assistant_eval.py::test_AC_14_13_fairness_by_group |
| AC-14-14 | UC-14 | REQ-AI-022 | test_assistant.py::test_AC_14_14_kill_switch_and_complaint; test_assistant.py::test_AC_14_14_switch_needs_ops_token_in_production; AC-14-14.test.jsx |
| AC-14-15 | UC-14 | REQ-AI-012, REQ-AI-005 | test_assistant.py::test_AC_14_15_ticket_has_context |
| AC-14-16 | UC-14 | REQ-FN-056, REQ-SEC-010 | test_assistant.py::test_AC_14_16_reschedule_api |
| AC-14-17 | UC-14 | REQ-AI-023 | test_assistant_r2b.py::test_AC_14_17_unaccepted_model_disables_assistant |
| AC-14-18 | UC-14 | REQ-AI-006 | test_assistant_r2b.py::test_AC_14_18_refund_timing_mentions_issuing_bank |
| AC-14-19 | UC-14 | REQ-FN-075, REQ-SEC-015 | test_assistant_r2b.py::test_AC_14_19_call_center_reverts_reschedule; UI-14-02.test.jsx |

## 3. ราย REQ (ที่มา และ AC)

| REQ | ที่มา | AC |
|---|---|---|
| REQ-AI-002 | SH-02 | Won't |
| REQ-AI-005 | EV-012, EV-046 | AC-14-01, AC-14-02, AC-14-15 |
| REQ-AI-006 | EV-046 | AC-14-03, AC-14-18 |
| REQ-AI-007 | EV-046 | AC-14-04 |
| REQ-AI-008 | OWASP LLM01:2026, LLM08:2026, LLM10:2026 | AC-14-05 |
| REQ-AI-009 | OWASP LLM06:2026 (ทีมเพิ่ม) | AC-14-07 |
| REQ-AI-010 | EV-046 | AC-14-08 |
| REQ-AI-011 | EV-046 | AC-14-09 |
| REQ-AI-012 | EV-046 | AC-14-10, AC-14-15 |
| REQ-AI-013 | EV-046 | AC-14-11 |
| REQ-AI-020 | EU AI Act มาตรา 50 | AC-14-12 |
| REQ-AI-021 | หน้าบทเรียนหัวข้อ 7.2 | AC-14-13 |
| REQ-AI-022 | หน้าบทเรียนหัวข้อ 7.4 | AC-14-14 |
| REQ-AI-023 | EV-053 | AC-14-17 |
| REQ-BR-001 | EV-023 | AC-05-02, AC-05-04, AC-07-10, AC-08-01, AC-08-06, AC-08-12 |
| REQ-BR-002 | EV-048 | AC-07-11, AC-07-19 |
| REQ-CMP-001 | EV-045 | ตรวจด้วย inspection ของ SH-05 |
| REQ-CON-001 | แผนโครงการ | ข้อจำกัดของแผนโครงการ ตรวจใน plan ข้อ 7 ของทุก feature |
| REQ-CON-003 | สัญญา | AC-08-03 |
| REQ-DAT-002 | Operations | AC-08-02, AC-09-02, AC-09-10 |
| REQ-DAT-003 | UC-07 postcondition, BR-02 (derived) | AC-08-02 |
| REQ-DAT-010 | EV-046, EV-047 | AC-14-06 |
| REQ-FN-008 | EV-004, EV-009 | AC-02-10, AC-07-01, AC-07-02 |
| REQ-FN-012 | EV-012 | AC-07-03 |
| REQ-FN-041 | EV-048 | AC-07-04, AC-07-12 |
| REQ-FN-050 | EV-044 | AC-09-01, AC-09-16 |
| REQ-FN-051 | EV-044 | AC-09-02, AC-09-03, AC-09-04, AC-09-05, AC-09-06, AC-09-12, AC-09-15 |
| REQ-FN-052 | EV-012 | AC-09-07 |
| REQ-FN-053 | EV-012 | AC-09-08, AC-09-11, AC-09-15 |
| REQ-FN-054 | EV-023, EV-044 | AC-08-01, AC-08-02, AC-08-06, AC-08-09, AC-08-12 |
| REQ-FN-055 | EV-012, EV-044 | AC-08-05, AC-08-12 |
| REQ-FN-056 | EV-046 | AC-14-16 |
| REQ-FN-057 | EV-048 | AC-07-19 |
| REQ-FN-058 | EV-051 | AC-02-01, AC-02-10 |
| REQ-FN-059 | EV-051 | AC-02-02 |
| REQ-FN-060 | EV-051 | AC-01-01, AC-01-02 |
| REQ-FN-061 | EV-051 | AC-05-03, AC-12-01, AC-12-02, AC-12-03, AC-12-05 |
| REQ-FN-062 | EV-051 | AC-05-01, AC-05-03, AC-05-05, AC-05-06 |
| REQ-FN-063 | EV-051 | AC-05-02, AC-05-04, AC-05-06 |
| REQ-FN-064 | EV-049, EV-051 | AC-07-20, AC-07-21, AC-07-22, AC-07-23 |
| REQ-FN-065 | EV-051 | AC-07-24 |
| REQ-FN-066 | EV-053 | AC-04-01, AC-04-02, AC-04-03, AC-04-04 |
| REQ-FN-067 | EV-053 | AC-04-05, AC-04-06, AC-04-07 |
| REQ-FN-068 | EV-053 | AC-11-01, AC-11-02, AC-11-03, AC-11-04, AC-11-08 |
| REQ-FN-069 | EV-053 | AC-11-06 |
| REQ-FN-070 | EV-053 | AC-13-01, AC-13-02, AC-13-03, AC-13-04, AC-13-08 |
| REQ-FN-071 | EV-053 | AC-13-05, AC-13-06 |
| REQ-FN-072 | EV-053 | AC-10-01, AC-10-02, AC-10-03, AC-10-05, AC-10-06 |
| REQ-FN-073 | EV-053 | AC-10-04, AC-10-07 |
| REQ-FN-074 | EV-053 | AC-02-12, AC-02-13, AC-02-14 |
| REQ-FN-075 | EV-053 | AC-14-19 |
| REQ-IF-001 | สัญญา gateway | AC-07-05, AC-07-06 |
| REQ-IF-005 | EV-048 | AC-07-05, AC-07-07, AC-07-13 |
| REQ-IF-010 | EV-044, EV-048 | AC-08-03, AC-08-04, AC-08-07, AC-08-08, AC-08-11, AC-13-05 |
| REQ-IF-012 | EV-053 | AC-00-12, AC-00-13 |
| REQ-OP-001 | EV-045 | AC-00-04, AC-08-09, AC-09-12 |
| REQ-OP-005 | EV-045 | AC-00-01, AC-00-02, AC-00-03, AC-00-11, AC-00-16 |
| REQ-OP-006 | EV-045 | ตรวจด้วย walkthrough ของคู่มือ (EV-045) และ OAT-3 |
| REQ-OP-007 | EV-045 | AC-00-05, AC-07-18 |
| REQ-OP-008 | EV-049, EV-051 | AC-00-09, AC-00-10, AC-00-11 |
| REQ-OP-009 | EV-053 | AC-00-12 |
| REQ-PRV-002 | PDPA | AC-00-03, AC-02-08, AC-07-09, AC-09-09, AC-10-07 |
| REQ-PRV-010 | EV-045 | AC-02-09, AC-07-17, AC-07-18, AC-10-07 |
| REQ-PRV-011 | EV-051 | AC-02-01, AC-02-12 |
| REQ-PRV-012 | EV-053 | AC-11-07, AC-11-08 |
| REQ-QA-003 | EV-007, EV-048, EV-051 | AC-07-08 |
| REQ-QA-010 | EV-045 | AC-00-13, AC-00-14, AC-02-13, AC-07-12, AC-07-13, AC-08-07, AC-08-08, AC-09-11, AC-09-13 |
| REQ-SEC-004 | EV-019 | AC-07-09, AC-07-15, AC-09-09 |
| REQ-SEC-010 | EV-045 | AC-00-08, AC-01-03, AC-02-07, AC-02-14, AC-04-08, AC-05-01, AC-07-15, AC-07-16, AC-07-23, AC-08-10, AC-09-14, AC-11-05, AC-12-04, AC-14-16 |
| REQ-SEC-011 | EV-045 | AC-07-14 |
| REQ-SEC-012 | EV-045 | AC-00-06, AC-00-07, AC-02-11, AC-07-16 |
| REQ-SEC-013 | EV-051 | AC-01-02, AC-02-01, AC-02-03, AC-02-04, AC-02-05, AC-02-08, AC-02-11, AC-10-05 |
| REQ-SEC-014 | EV-051 | AC-01-01, AC-01-03, AC-02-02, AC-02-06, AC-02-09, AC-04-08 |
| REQ-SEC-015 | EV-053 | AC-00-15, AC-13-07, AC-14-19 |

## 4. สายขาด

ไม่มี
