import re
import time
import gc
import subprocess
from datetime import datetime
import signal
import os

class ADBOTPManager:
    def __init__(self, sender_name="ICICI"):
        self.sender_name = sender_name
        self.sec_ago = 4  # look back window in minutes (matches your *60 math)
        self.max_attempts = 12 # total duration to keep checking
        self.process_cleanup_counter = 0 
    
    def clear_inbox(self):
        """Clear SMS inbox with proper process cleanup"""
        process = None
        try:
            process = subprocess.Popen(
                ["adb", "shell", "pm", "clear", "com.android.providers.telephony"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                start_new_session=True
            )
            stdout, stderr = process.communicate(timeout=10)
            return process.returncode == 0
        except subprocess.TimeoutExpired:
            if process:
                process.kill()
                process.wait()
            raise
        except Exception as e:
            print(f"Error clearing inbox: {e}")
            return False
        finally:
            if process and process.poll() is None:
                process.terminate()
                process.wait(timeout=2)
            del process
            gc.collect()
    
    def _cleanup_adb_processes(self):
        """Kill zombie ADB processes periodically"""
        try:
            # Kill any hanging adb shell processes
            if os.name == 'posix':
                subprocess.run(
                    ["pkill", "-9", "-f", "adb shell"],
                    timeout=2,
                    capture_output=True,
                    check=False
                )
        except:
            pass
    
    def _restart_adb_server(self):
        """Restart ADB server to prevent memory leaks"""
        try:
            subprocess.run(
                ["adb", "kill-server"],
                timeout=5,
                capture_output=True,
                check=False
            )
            time.sleep(0.5)
            subprocess.run(
                ["adb", "start-server"],
                timeout=5,
                capture_output=True,
                check=False
            )
            print("ADB server restarted")
        except Exception as e:
            print(f"Error restarting ADB: {e}")
            
    @staticmethod
    def get_connected_serials():
        """Get connected devices with proper cleanup"""
        process = None
        try:
            process = subprocess.Popen(
                ["adb", "devices"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True
            )
            stdout, stderr = process.communicate(timeout=5)
            output = stdout.decode('utf-8')
            serials = re.findall(r'^(\S+)\tdevice', output, re.MULTILINE)
            return serials
        except Exception as e:
            print(f"Error getting devices: {e}")
            return []
        finally:
            if process:
                if process.poll() is None:
                    process.kill()
                    process.wait()
            del process
            gc.collect()

    def get_otp_details(self, body_contains=""):
        """Reads the SMS inbox of a USB-connected Android phone"""
        print(f"  SMS Service | Polling phone for {self.sender_name} OTP...")
        
        self.process_cleanup_counter += 1
        if self.process_cleanup_counter % 100 == 0:
            self._restart_adb_server()
        
        if self.process_cleanup_counter % 10 == 0:
            self._cleanup_adb_processes()
        
        timestamp_ms = int((time.time() - self.sec_ago) * 1000)
        
        # 1. FIXED: Projection must include 'date' if you want to regex it later
        #command_str = f'adb shell "content query --uri content://sms/inbox --projection address:body:date --where \'date > {int((time.time() - self.sec_ago) * 1000)}\'"'
        command = [
            "adb", "shell",
            f"content query --uri content://sms/inbox --projection address:body:date --where 'date > {timestamp_ms}'"
        ]
        for attempt in range(self.max_attempts):
            start_time = time.time()
            #print(f"Attempt {attempt + 1} of {self.max_attempts}")
            process = None
            sms_list = {}
            try:    
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    close_fds=True,
                    start_new_session=True,
                    preexec_fn=os.setpgrp if os.name != 'nt' else None
                )
                try:
                    stdout, stderr = process.communicate(timeout=15)
                except subprocess.TimeoutExpired:
                    print("  SMS Service |  => ADB command timeout, killing process...")
                    # Kill the process group
                    if os.name == 'posix':
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    else:
                        process.kill()
                    process.wait()
                    continue
                
                if process.returncode != 0:
                    print(f"  SMS Service |  => ADB command failed with return code {process.returncode}")
                    continue
                
                #raw_out = subprocess.check_output(command_str, shell=True, start_new_session=True).decode('utf-8')
                
                raw_out = stdout.decode('utf-8', errors='replace')
                rows = raw_out.split('Row:')
                del stdout, stderr
                
                
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
                            print(f"  SMS Service |  => Found {self.sender_name} OTP in address: {addr_val} or body: {body_val}")
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
                del raw_out, rows
                gc.collect()
                if sms_list:
                    sorted_sms_list = sorted(sms_list.items(), key=lambda x: x[1]['ts'], reverse=True)
                    result = sorted_sms_list[0][1]
                    del sorted_sms_list
                    gc.collect()
                    return result
                    
            except Exception as e:
                print(f"  SMS Service |  => Error: {e}")   
            
            finally:
                end_time = time.time()
                print(f"  SMS Service |  => Total time taken for attempt {attempt+1} / {self.max_attempts}: {end_time - start_time} seconds") 
                # Always cleanup the process
                if process:
                    try:
                        if process.poll() is None:
                            process.terminate()
                            process.wait(timeout=2)
                    except:
                        try:
                            process.kill()
                            process.wait()
                        except:
                            pass
                
                # Explicit cleanup
                del process, sms_list
                gc.collect()
                       
            #if attempt < (self.max_attempts) - 1:
            #    print(f"OTP not found, retrying in 2s... (attempt {attempt + 1})")
            #    time.sleep(2)
            
        print(f"  SMS Service |  => OTP not found after all attempts")
        return None

# Example Usage:
# manager = ADBOTPManager("ICICI")
# print(manager.get_otp_details())

# if __name__ == "__main__":
#    manager = ADBOTPManager("ICICI")
#    print("otp details:", manager.get_otp_details())
