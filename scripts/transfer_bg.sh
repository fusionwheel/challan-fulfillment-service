bq mk --transfer_config \
--data_source=google_cloud_storage \
--display_name="challan_auto_payment_logs" \
--target_dataset=payment_automation \
--location=asia-south2 \
--params='{
  "data_path_template":"gs://challan-pmt-auto-logs/Year=*/Month=*/Date=*/*.json",
  "file_format":"JSON",
  "write_disposition":"MIRROR",
  "destination_table_name_template":"challan_auto_payment_logs",
  "max_bad_records":"10"
}' \
--schedule="every 24 hours"
