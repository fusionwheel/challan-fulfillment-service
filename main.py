import os
import json
import requests
from challan_workflow import config
from datetime import datetime, timedelta
import socket
import gc
import sys

from fulfillment import process_from_queue
from challan_workflow.slack_alert import send_startup_alert, send_message_alert


hostname = socket.gethostname()
try:
    IPAddr = socket.gethostbyname(hostname)
except Exception:
    IPAddr = "localhost"
print(f"PC Worker Hostname: {hostname} | IP: {IPAddr}")

# Restart-after-N-messages safeguard
MAX_MESSAGES_PER_WORKER = int(os.getenv("MAX_MESSAGES_PER_WORKER", "500"))
_processed_messages = 0


def acknowledge(uniq_id, order_item_id, status, state, data):
    url = os.environ['C24_ACK_URL']
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1.1 Safari/605.1.15",
        "Content-Type": "application/json",
        "x-api-key": os.getenv("C24_ACK_API_KEY", "")
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
        payload = {**data, **extra}
        response = requests.post(url, headers=headers, json=payload, timeout=30)
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
    appointment_id = data.get("appointment_id")
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
    print("UNIQ ID\t\t:", uniq_id)
    print("Appointment ID\t:", appointment_id)
    print("Reg no\t\t:", reg_no)
    print("Challan no\t:", challan_no)
    print("Payment remarks\t:", payment_remarks)
    print("Category\t:", category)
    print("Valid till\t:", valid_till)
    print("Owner name\t:", owner_name)
    print("Owner Mob\t:", owner_mobile_no)
    print("RECEIVED AT\t:", datetime.now().isoformat())
    
    print("-" * 50)
    
    # status, state, pg_charges, reason = None, None, 0, None
    status = None; state = None; step = None; reason = None; pg_charges = 0
        
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
        
        if (category or "E_CHALLAN") not in config.LIVE_CATEGORY_CODES:
            status = "FAILED"
            state = "INIT_FAILED"
            reason = f"Challan not live for this category {category}"
            # ack to tech api
            acknowledge(uniq_id, order_item_id, status, state, {"reason": reason})
            # log data 
            log_data = get_log_data(data, extra={
                "status": status, "state": state, "step": "CALLBACK", "message": reason
            }) 
            print(f"Challan not live for category codes => {category}")
            publish_log(log_data)
            return
        
        if isinstance(valid_till, str):
            valid_till = datetime.fromisoformat(valid_till)
        
        if valid_till and valid_till < datetime.now() + timedelta(minutes=5): # 5 mins buffer
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
            appointment_id=appointment_id,
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
            "status": status or "FAILED",
            "state": state or "LINK_FAILED",
            "message": reason or str(e),
            "exception": str(e),
            "step": step or "CALLBACK",
            "settlement_amount": data.get("amount") or 0,
            "tx_amount": pg_charges,
            "pg_charges": round(float(pg_charges) - float(data.get("amount") or 0), 2) if pg_charges else 0,
            "receipt_url": None
        })    
        publish_log(log_data)
        print(f"Challan fulfillment failed => {e}")
        return

def callback(message):
    global _processed_messages
    challan_data = None
    try:
        gc.collect()

        print(f"[{datetime.now()}] Task Received: {message.data}")
        try:
            send_message_alert(
                text="Challan callback message received",
                extra={
                    "hostname": hostname,
                    "ip": IPAddr,
                    "received_at": datetime.now().isoformat(),
                    "raw_length": len(message.data) if getattr(message, "data", None) is not None else 0,
                },
            )
        except Exception:
            pass
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
        if challan_data is None:
            challan_data = {}
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
    finally:
        # Explicitly drop references to large per-message objects
        del challan_data
        gc.collect()

        _processed_messages += 1
        if _processed_messages >= MAX_MESSAGES_PER_WORKER:
            print(f"Max messages per worker reached ({MAX_MESSAGES_PER_WORKER}). Exiting for restart.")
            sys.stdout.flush()
            os._exit(0)

def validate_environment():
    required_vars = [
        "ENV",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GOOGLE_CLOUD_PROJECT",
        "SUBSCRIPTION_ID",
        "ICICI_NETBANKING_USER_ID",
        "ICICI_NETBANKING_PASSWORD",
        "MOB_NO_FOR_OTP",
        "FW_CLIENT_ID",
        "FW_CLIENT_SECRET",
        "C24_ACK_URL"
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # In onedir mode, this points to the _internal folder
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def get_executable_path(name):
        if getattr(sys, 'frozen', False):
            print("get_executable_path", name)
            return os.path.join(os.path.dirname(sys.executable), name)
        return sys.executable
    
if __name__ == '__main__':
    # --- Subscriber Setup ---
    import faulthandler
    import multiprocessing as mp
    import subprocess
    import sys
    
    from dotenv import load_dotenv
    from google.cloud import pubsub_v1

    faulthandler.enable(all_threads=True)
    gc.enable()

    mp.set_start_method("spawn", force=True)
    
    env_path = get_resource_path(".env")
    print("env_path", env_path)
    load_dotenv(env_path)

    validate_environment()
    
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
    SUBSCRIPTION_ID = os.getenv("SUBSCRIPTION_ID", "fusionwheel.fulfillment.stage-sub")
    NETBANKING_USERNAME = os.getenv("ICICI_NETBANKING_USER_ID")
    NETBANKING_PASSWORD = os.getenv("ICICI_NETBANKING_PASSWORD")
    MOB_NO_FOR_OTP = os.getenv("MOB_NO_FOR_OTP")
    C24_ACK_API_KEY = os.getenv("C24_ACK_API_KEY")
    
    if not C24_ACK_API_KEY:
        print("Error: C24_ACK_API_KEY not found in .env")
        exit(1)
    
    if not PROJECT_ID:
        print("Error: GOOGLE_CLOUD_PROJECT not found in .env")
        exit(1)
        
    if not MOB_NO_FOR_OTP:
        print("Error: MOB_NO_FOR_OTP not found in .env")
        exit(1)
    
    if not (NETBANKING_USERNAME and NETBANKING_PASSWORD):
        print("Error: NETBANKING_USERNAME and NETBANKING_PASSWORD not found in .env")
        exit(1)
    
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = get_resource_path(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    
    #with open("worker_log.txt", "w") as log_file:
    #    subprocess.Popen([get_executable_path("sms_worker")], stdout=log_file, stderr=log_file)

    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    
    # CRITICAL: This ensures the PC only takes 1 task at a time
    flow_control = pubsub_v1.types.FlowControl(max_messages=1)

    streaming_pull_future = subscriber.subscribe(
        subscription_path,
        callback=callback,
        flow_control=flow_control
    )

    try:
        send_startup_alert(
            text="PC Worker subscriber initialized",
            extra={
                "project_id": PROJECT_ID,
                "subscription_id": SUBSCRIPTION_ID,
                "env": os.getenv("ENV", "development"),
                "hostname": hostname,
                "ip": IPAddr,
            },
        )
    except Exception:
        pass

    print(f"🚀 PC Worker Online | Project: {PROJECT_ID} | Sub: {SUBSCRIPTION_ID}")
    print(f"Status: READY - Waiting for messages...")

    with subscriber:
        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            streaming_pull_future.cancel()