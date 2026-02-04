import subprocess
import re
import time
from datetime import datetime

class ADBOTPManager:
    def __init__(self, sender_name="ICICI"):
        self.sender_name = sender_name
        self.sec_ago = 5  # look back window in minutes (matches your *60 math)
        self.poll_sec = 30 # total duration to keep checking
    
    def clear_inbox(self):
        subprocess.check_output("adb shell pm clear com.android.providers.telephony", shell=True)

    def get_connected_serials():
        output = subprocess.check_output("adb devices", shell=True).decode('utf-8')
        # Use regex to find all serials followed by 'device'
        return re.findall(r'^(\S+)\tdevice', output, re.MULTILINE)

    def get_otp_details(self, body_contains=""):
        """Reads the SMS inbox of a USB-connected Android phone"""
        print(f"Polling phone for {self.sender_name} OTP...")
        
        # 1. FIXED: Projection must include 'date' if you want to regex it later
        command_str = f'adb shell "content query --uri content://sms/inbox --projection address:body:date --where \'date > {int((time.time() - self.sec_ago) * 1000)}\'"'
        for _ in range(self.poll_sec // 2):
            sms_list = {}
            try:    
                raw_out = subprocess.check_output(command_str, shell=True, start_new_session=True).decode('utf-8')
                rows = raw_out.split('Row:')
                
                for row in reversed(rows):
                    if not row.strip(): continue
                    
                    # 2. Extract values using more flexible regex (handles commas or spaces)
                    address = re.search(r'address=([^,\s]+)', row)
                    body = re.search(r'body=(.+?)(?=,?\s\w+=|$)', row)
                    date_ms = re.search(r'date=(\d+)', row)
                    
                    if address and body and date_ms:
                        addr_val = address.group(1)
                        body_val = body.group(1)
                        print(f"{date_ms.group(1)} | {addr_val} | {body_val}")
                        
                        if self.sender_name.upper() in addr_val.upper() or self.sender_name.upper() in body_val.upper() or (body_contains and str(body_contains).upper() in body_val.upper()):
                            print(f"Found {self.sender_name} OTP in address: {addr_val} or body: {body_val}")
                            otp_match = re.search(r'\b\d{4,6}\b', body_val)
                            
                            if otp_match:
                                readable_date = datetime.fromtimestamp(int(date_ms.group(1))/1000).strftime('%Y-%m-%d %H:%M:%S')
                                sms_list[date_ms.group(1)] = {
                                    "address": addr_val,
                                    "body": body_val,
                                    "date": readable_date,
                                    "ts": date_ms.group(1),
                                    "otp": otp_match.group(0)
                                }
                if sms_list:
                    sorted_sms_list = sorted(sms_list.items(), key=lambda x: x[1]['ts'], reverse=True)
                    return sorted_sms_list[0][1]
                    
            except Exception as e:
                print(f"Error: {e}")   
            
            print("OTP not found, retrying...")
            time.sleep(2)
            
        return sms_list

# Example Usage:
# manager = ADBOTPManager("ICICI")
# print(manager.get_otp_details())

#if __name__ == "__main__":
#    manager = ADBOTPManager("ICICI")
#    print(manager.get_otp_details())
