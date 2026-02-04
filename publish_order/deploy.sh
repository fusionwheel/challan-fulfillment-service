gcloud functions deploy ch_order_to_pubsub_stage \
--gen2 \
--runtime python311 \
--region asia-south2 \
--entry-point main \
--trigger-http \
--allow-unauthenticated \
--max-instances 1 \
--set-env-vars GOOGLE_CLOUD_PROJECT=fusion-wheel,TOPIC_ID=fusionwheel.fulfillment.stage