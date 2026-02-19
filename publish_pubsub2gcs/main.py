import json
import base64
import functions_framework
from google.cloud import storage
import datetime
import uuid

# Initialize GCS client
storage_client = storage.Client()
BUCKET_NAME = "challan-pmt-auto-logs"

@functions_framework.cloud_event
def save_to_gcs(cloud_event):
    try:
        # 1. Decode Pub/Sub message
        pubsub_message = base64.b64decode(
            cloud_event.data["message"]["data"]
        ).decode("utf-8")

        # 2. Parse JSON safely
        json_data = json.loads(pubsub_message)

        # 3. Convert to single-line JSON (valid JSONL)
        single_line_json = json.dumps(json_data, separators=(",", ":"))

        # 4. Generate partitioned filename
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
        except Exception as e:
            now = datetime.datetime.utcnow()
            
        year = now.strftime("%Y")
        month = now.strftime("%m")
        dt = now.strftime("%Y%m%d")
        timestamp = now.strftime("%Y%m%d-%H%M%S")

        filename = f"Year={year}/Month={month}/Date={dt}/log-{timestamp}-{uuid.uuid4().hex}.json"

        # 5. Upload to GCS
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)

        blob.upload_from_string(
            single_line_json + "\n",  # newline makes it valid JSONL
            content_type="application/json"
        )

        print(f"Saved: {filename}")

    except Exception as e:
        print(f"Error saving to GCS: {e}")