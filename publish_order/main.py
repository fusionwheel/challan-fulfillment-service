import os
import json
import uuid
from google.cloud import pubsub_v1
from flask import jsonify

# Global initialization for performance
publisher = pubsub_v1.PublisherClient()
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
TOPIC_ID = os.getenv("TOPIC_ID", "fusionwheel.fulfillment.stage") 
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

class ChallanOrderPublishView:
    """Class-based logic to handle Challan publishing"""

    def validate_data(self, data):
        """Manual validation logic (replaces DRF Serializer for Cloud Functions)"""
        errors = {}
        
        # Rule: Either app_id or order_item_id required
        if not data.get('app_id') and not data.get('order_item_id'):
            errors['id_error'] = "Either app_id or order_item_id is required."
            
        # Add other mandatory field checks here if necessary
        mandatory_fields = ['reg_no', 'challan_no', 'amount']
        for field in mandatory_fields:
            if not data.get(field):
                errors[field] = "This field is required."
                
        return len(errors) == 0, errors

    def post(self, request):
        request_id = str(uuid.uuid4())
        data = request.get_json(silent=True) or {}
        
        try:
            is_valid, errors = self.validate_data(data)
            
            if is_valid:
                # Prepare payload
                payload = data.copy()
                payload['request_id'] = request_id
                
                # Convert to bytes
                message_data = json.dumps(payload).encode("utf-8")
                
                # Publish to Pub/Sub
                # Note: .result() is a blocking call that ensures the message is sent
                future = publisher.publish(topic_path, message_data)
                message_id = future.result() 
                
                return jsonify({
                    "message": "Challan order publish endpoint",
                    "message_id": message_id,
                    "request_id": request_id
                }), 200
            else:
                return jsonify({
                    "message": "Error publishing message",
                    "request_id": request_id,
                    "details": errors
                }), 400
                
        except Exception as e:
            print(f"Error publishing message: {e}")
            return jsonify({
                "message": "Error publishing message",
                "details": str(e),
                "request_id": request_id
            }), 500

# Cloud Function Entry Point
def main(request):
    view = ChallanOrderPublishView()
    return view.post(request)