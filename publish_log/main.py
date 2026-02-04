import os
import json
from google.cloud import pubsub_v1
import functions_framework
from flask import jsonify

# Initialize Publisher once outside the function for better performance
try:
    publisher = pubsub_v1.PublisherClient()
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
    TOPIC_ID = os.getenv("TOPIC_ID", "payment-logs-topic") 
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
except Exception as e:
    print(f"Global Init Error: {e}")

@functions_framework.http
def publish_payment_log(request):
    """HTTP Cloud Function to trigger the worker."""
    try:
        # 1. Get data from the incoming request (JSON)
        request_json = request.get_json(silent=True)
        if not request_json:
            return jsonify({"error": "No JSON payload provided"}), 400

        # 2. Convert payload to bytes for Pub/Sub
        message_bytes = json.dumps(request_json).encode("utf-8")
        origin = str(request_json.get('origin', '"cloud-function'))
        device_id = str(request_json.get('device_id', 'unknown_pc'))
        request_id = str(request_json.get('request_id', 'unknown_request'))
        state = str(request_json.get('state', 'unknown_state'))
        status = str(request_json.get('status', 'unknown_status'))
        env = os.getenv("ENV", "development")
        
        # 3. Publish message with optional attributes
        # Attributes are useful for BigQuery filtering without parsing the JSON
        future = publisher.publish(
            topic_path, 
            data=message_bytes,
            origin= origin or "cloud-function",
            priority="high",
            request_id=request_id,
            env=env,
            device_id=device_id,
            state=state,
            status=status
        )
        
        message_id = future.result()
        return jsonify({"status": "published", "message_id": message_id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500