import requests
from challan_workflow.base import exception
import os

def fetch_otp(sender="VAAHAN", body_contains=""):
    try: 
        SMS_HOST = os.getenv("SMS_HOST", "127.0.0.1")
        if SMS_HOST == "0.0.0.0":
            SMS_HOST = "localhost"
        SMS_PORT = os.getenv("SMS_PORT", 9090)
        resp = requests.post(
            "http://{}:{}/get-otp".format(SMS_HOST, SMS_PORT),
            json={
                "sender": sender,
                "body_contains": body_contains
            },
            timeout=30,
        )
        if resp.status_code != 200:
            raise exception.OTPNotFound("OTP not found")
        return resp.json()
    except Exception as e:
        raise exception.OTPNotFound("OTP not found")


import threading
print_lock = threading.Lock()

def safe_print(*args):
    with print_lock:
        print(*args)