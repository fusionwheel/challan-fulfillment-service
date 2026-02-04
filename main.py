import os
import json
import requests
from workflow import config
from datetime import datetime, timedelta
import socket

from fulfillment import process_from_queue


hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
print(f"PC Worker Hostname: {hostname} | IP: {IPAddr}")

def acknowledge(uniq_id, order_item_id, status, state, data):
    url = "https://p376z7jfse.execute-api.ap-south-1.amazonaws.com/test/api/v1/c2b/vas/challan-item/status"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1.1 Safari/605.1.15",
        "Content-Type": "application/json"
    }
    payload = {
        "id_challan_item": uniq_id,
        "settlement_amount": data.get("settlement_amount"),
        "pg_charges": data.get("pg_charges"),
        "status": status,
        "state": state,
        "receipt_url": data.get("receipt_url")
    }
    print(f"Sending acknowledge for uniq_id: {uniq_id}, order_item_id: {order_item_id} | ack payload: {payload}")
    response = requests.post(url, headers=headers, json=payload)
    print("ack_ch_fulfillment", response.text)
    if response.status_code == 200:
        return True
    raise Exception(f"Challan fulfillment not acknowledged => order_item_id: {order_item_id} | uniq_id: {uniq_id}")

def publish_log(data:dict):
    try:
        url = "https://asia-south2-fusion-wheel.cloudfunctions.net/publish_payment_log"
        headers = {
            "Content-Type": "application/json"
        }
        extra = {
            "origin": f"pc-worker-{hostname or os.uname().nodename}",
            "device_id": f"device-{IPAddr}",
            "priority": "high",
            "env": os.getenv("ENV", "development")
        }
        data.update(extra)
        response = requests.post(url, headers=headers, json=data)
        print(f"Log published: {response.status_code}")
    except Exception as e:
        print(f"Failed to publish log: {e}")

def get_log_data(data:dict, extra):
    return {**data, **extra}
    

def process_fulfillment(data):
    uniq_id = data.get("id") or data.get("id_challan_item")
    reg_no = data.get("reg_no")
    challan_no = data.get("challan_no")
    st_cd = str(challan_no).upper()[:2]
    order_item_id = data.get("order_item_id")
    category = data.get("category")
    valid_till = data.get("valid_till") or data.get("tat")
    payment_remarks = data.get("challan_id") or order_item_id
    owner_name = data.get("owner_name")
    owner_mobile_no = data.get("mob_no")
    
    if not owner_name:
        owner_name = "NA"    
    
    print("-" * 50)
    print(f"Processing fulfillment for order item id {order_item_id} | uniq_id: {uniq_id}")
    print("-" * 50)
    print("Reg no\t\t:", reg_no)
    print("Challan no\t:", challan_no)
    print("Payment remarks\t:", payment_remarks)
    print("Category\t:", category)
    print("Valid till\t:", valid_till)
    print("Owner name\t:", owner_name)
    print("Owner Mob\t:", owner_mobile_no)
    
    print("-" * 50)
    
    status, state, pg_charges = None, None, 0
    try:
        if st_cd not in config.LIVE_ST_CODES:
            status = "FAILED"
            state = "INIT_FAILED"
            reason = f"Challan not live for this state {st_cd}"
            # ack to tech api
            acknowledge(uniq_id, order_item_id, status, state, {"reason": reason})
            # log data 
            log_data = get_log_data(data, extra={
                "status": status, "state": state, "step": "CALLBACK", "message": reason
            })    
            print(f"Challan not live for state codes => {st_cd}")
            publish_log(log_data)
            return
        
        if category not in config.LIVE_CATEGORY_CODES:
            status = "FAILED"
            state = "INIT_FAILED"
            reason = f"Challan not live for this category {category}"
            # ack to tech api
            acknowledge(uniq_id, order_item_id, status, state, {"reason": reason})
            # log data 
            log_data = get_log_data(data, extra={
                "status": status, "state": state, "step": "CALLBACK", "message": reason
            }) 
            print("Challan not live for category codes => {category}")
            publish_log(log_data)
            return
        
        if isinstance(valid_till, str):
            valid_till = datetime.fromisoformat(valid_till)
        
        if valid_till and valid_till < datetime.now() - timedelta(minutes=5): # 5 mins buffer
            status = "FAILED"
            state = "INIT_FAILED"
            reason = "Challan order expired"
            # ack to tech api (dont need to ack for expired challans)
            # acknowledge(uniq_id, order_item_id, status, state, {"reason": reason})
            # log data
            log_data = get_log_data(data, extra={
                "status": status, "state": state, "step": "CALLBACK", "message": reason
            }) 
            print(f"Challan order expired.. => {valid_till}")
            publish_log(log_data)
            return
        
        response = process_from_queue(
            order_item_id=order_item_id,
            reg_no=reg_no, 
            challan_no=challan_no,
            owner_name=owner_name,
            owner_mobile_no=owner_mobile_no,
            payment_remarks=payment_remarks
        )
        print(f"Challan fulfillment response => order_item_id: {order_item_id} | uniq_id: {uniq_id} | {response}")
        status = response.get("status")
        state = response.get("state")
        step = response.get("step")
        reason = response.get("message")
        exception = response.get("exception")
        
        ack_data = {}
        
        pg_charges = 0
        if str(status).upper() == "SUCCESS":
            pg_charges = response.get("pgi_amount") or 0
            print(f"pg_charges {order_item_id} | {data.get('amount')} | {pg_charges}")
            
            ack_data = {
                "settlement_amount": data.get("amount"),
                "pg_charges":  round(float(pg_charges) - float(data.get("amount")), 2),
                "receipt_url": response.get("receipt_url")
            }
        
        log_data = get_log_data(data, extra={
            "status": str(status).upper() if status else "FAILED",
            "state": state,
            "message": reason,
            "exception": exception,
            "step": step,
            "settlement_amount": data.get("amount"),
            "tx_amount": pg_charges,
            "pg_charges": round(float(pg_charges) - float(data.get("amount") or 0), 2) if pg_charges else 0,
            "receipt_url": ack_data.get("receipt_url")
        })
        try:
            # ack to tech api
            acknowledge(uniq_id, order_item_id, status, state, ack_data)
            # log data 
            publish_log(log_data)
        except Exception as e:
            print(f"Challan fulfillment tech ack api call failed => uniq_id: {uniq_id}, order_item_id: {order_item_id} | {e}")
            # log data 
            log_data['exception'] = str(e)
            publish_log(log_data)
        finally:
            # logs to bq
            print(f"Challan fulfillment acknowledged => uniq_id: {uniq_id}, order_item_id: {order_item_id} | status: {status} | state: {state}")
        
    except Exception as e:
        # ack to tech api
        acknowledge(uniq_id, order_item_id, "FAILED", "LINK_FAILED", data)
        # log data 
        log_data = get_log_data(data, extra={
            "status": "FAILED",
            "state": "LINK_FAILED",
            "message": reason,
            "exception": str(e),
            "step": "CALLBACK",
            "settlement_amount": data.get("amount"),
            "tx_amount": pg_charges,
            "pg_charges": round(float(pg_charges) - float(data.get("amount") or 0), 2) if pg_charges else 0,
            "receipt_url": None
        })    
        publish_log(log_data)
        print(f"Challan fulfillment failed => {e}")
        return


def callback(message):
    print(f"[{datetime.now()}] Task Received: {message.data}")
    try:
        # --- BUSY STATE START ---
        # 1. Parse account data from Pub/Sub
        challan_data = json.loads(message.data.decode("utf-8"))
        
        print(challan_data)
        
        process_fulfillment(challan_data)
        print("Transaction Successful")
        
        # 3. Acknowledge the message (Removes it from queue)
        message.ack() 
        # --- READY STATE ---
        
    except Exception as e:
        print(f"Error occurred: {e}")
        log_data = get_log_data(challan_data, extra={
            "status": "failed",
            "state":  "PRE_CALLBACK_FAILED",
            "message": str(e),
            "step": "PRE_CALLBACK",
            "data": str(message.data)
        })  
        publish_log(log_data)
        # Message will reappear in the queue for another PC after 'visibility timeout'
        message.nack()


if __name__ == '__main__':
    # --- Subscriber Setup ---
    import os
    from dotenv import load_dotenv
    from google.cloud import pubsub_v1
    
    load_dotenv()
    
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
    SUBSCRIPTION_ID = os.getenv("SUBSCRIPTION_ID", "fusionwheel.fulfillment.stage-sub")
    NETBANKING_USERNAME = os.getenv("ICICI_NETBANKING_USER_ID")
    NETBANKING_PASSWORD = os.getenv("ICICI_NETBANKING_PASSWORD")
    MOB_NO_FOR_OTP = os.getenv("MOB_NO_FOR_OTP")

    if not PROJECT_ID:
        print("Error: GOOGLE_CLOUD_PROJECT not found in .env")
        exit(1)
        
    if not MOB_NO_FOR_OTP:
        print("Error: MOB_NO_FOR_OTP not found in .env")
        exit(1)
    
    if not (NETBANKING_USERNAME and NETBANKING_PASSWORD):
        print("Error: NETBANKING_USERNAME and NETBANKING_PASSWORD not found in .env")
        exit(1)
    
        
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    
    # CRITICAL: This ensures the PC only takes 1 task at a time
    flow_control = pubsub_v1.types.FlowControl(max_messages=1)

    streaming_pull_future = subscriber.subscribe(
        subscription_path, 
        callback=callback, 
        flow_control=flow_control
    )

    print(f"🚀 PC Worker Online | Project: {PROJECT_ID} | Sub: {SUBSCRIPTION_ID}")
    print(f"Status: READY - Waiting for messages...")

    with subscriber:
        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            streaming_pull_future.cancel()