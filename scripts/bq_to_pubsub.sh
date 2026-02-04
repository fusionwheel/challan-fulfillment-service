gcloud pubsub subscriptions create bq-payment-logs-sub \
    --topic=payment-logs-topic \
    --bigquery-table=fusion-wheel:payment_automation.payment_logs \
    --use-topic-schema \
    --write-metadata