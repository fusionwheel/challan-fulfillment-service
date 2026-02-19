gcloud functions deploy automation-logs-pusub-to-gcs-bridge \
--gen2 \
--runtime=python312 \
--region=asia-south2 \
--source=. \
--entry-point=save_to_gcs \
--trigger-topic=payment-logs-topic \
--memory=256Mi
