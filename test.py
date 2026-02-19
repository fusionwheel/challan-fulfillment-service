import os
import subprocess
from fulfillment import process_from_queue


# VAS CHALLAN
ORDER_ITEM_ID = None
APPOINTMENT_ID = "OVS-0004814288"
REG_NO = "TN01BQ3115"
CHALLAN_NO = "TN413998231014020645"
payment_remarks = "092cI"

if __name__ == "__main__":
    from dotenv import load_dotenv
    import signal
    load_dotenv()

    import psutil

    def kill_port(port):
        """Finds and kills all processes listening on a specific port."""
        found = False
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                # Check all network connections for this process
                connections = proc.net_connections()
                for conn in connections:
                    if conn.laddr.port == port:
                        print(f"Found {proc.info['name']} (PID: {proc.info['pid']}) on port {port}")
                        # Force kill the process
                        proc.send_signal(signal.SIGKILL) 
                        print(f"Successfully killed PID {proc.info['pid']}")
                        found = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if not found:
            print(f"No processes found running on port {port}")
    
    # start sms worker
    from sms_worker import app
    HOST = os.environ.get("SMS_HOST", "0.0.0.0")
    PORT = os.environ.get("SMS_PORT", "9090")
    # You must specify the host and port explicitly for the subprocess to find it
    try:
        kill_port(PORT)
        proc = subprocess.Popen(["uvicorn", "sms_worker:app", "--host", HOST, "--port", PORT])
    
        data = {
            "order_item_id": ORDER_ITEM_ID,
            "appointment_id": APPOINTMENT_ID,
            "reg_no": REG_NO,
            "challan_no": CHALLAN_NO,
            "payment_remarks": payment_remarks,
            "owner_name": "NA",
            "owner_mobile_no": "9266882972" 
        }
        
        result = process_from_queue(**data)
        print("result", result)
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()
        