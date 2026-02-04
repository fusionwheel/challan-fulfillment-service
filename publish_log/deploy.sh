gcloud functions deploy publish_payment_log \
--gen2 \
--runtime python311 \
--region asia-south2 \
--source=. \
--entry-point publish_payment_log \
--trigger-http \
--allow-unauthenticated \
--max-instances 1 \
--set-env-vars GOOGLE_CLOUD_PROJECT=fusion-wheel,TOPIC_ID=payment-logs-topic