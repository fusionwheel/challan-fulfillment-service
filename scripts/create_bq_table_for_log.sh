# bq mk --location=asia-south2 payment_automation

bq mk --table \
--expiration 259200 \
--description "Temporary Payment logs storage before Parquet export" \
--time_partitioning_type DAY \
--time_partitioning_expiration 259200 \
payment_automation.payment_logs \
subscription_name:STRING,message_id:STRING,publish_time:TIMESTAMP,attributes:JSON,data:JSON