import serial
import time
import re

# pip install pyserial

class HardwareOTPManager:
    
    
    def __init__(self, port="COM3", baudrate=115200):
        """
        port: The COM port assigned to your USB Modem (e.g., 'COM3' on Windows 
              or '/dev/ttyUSB0' on Linux)
        """
        self.ser = serial.Serial(port, baudrate, timeout=5)

    def send_command(self, cmd, wait_time=1):
        self.ser.write((cmd + "\r\n").encode())
        time.sleep(wait_time)
        return self.ser.read(self.ser.in_waiting).decode()

    def get_otp_from_modem(self, sender_name="ICICI"):
        print(f"Checking hardware modem for {sender_name} OTP...")
        
        response = self.send_command("AT")
        print("health check:", response)
        
        # 1. Set modem to Text Mode (standard for reading SMS)
        response = self.send_command("AT+CMGF=1")
        print("set text mode:", response)
        
        response = self.send_command('AT+CPMS="ME","ME","ME"')
        print("set memory:", response)
        
        # 2. List all received unread messages
        # "REC UNREAD" fetches new messages
        for _ in range(30):  # Poll for 30 seconds
            #response = self.send_command('AT+CMGL="REC UNREAD"')
            response = self.send_command('AT+CMGL="ALL"')
            print(response)
            if "ERROR: 302" in response:
                print("Modem Busy (302), waiting 3 seconds...")
                time.sleep(3)
                continue
            
            if sender_name.upper() in response.upper():
                print("New SMS detected from Bank!")
                # Extract 6-digit code
                otp_match = re.search(r'\d{6}', response)
                if otp_match:
                    otp = otp_match.group(0)
                    # 3. Optional: Delete message after reading to keep SIM clean
                    self.send_command('AT+CMGD=1,4') 
                    return otp
            
            #print(f"Scan {i+1}/15: No match yet...")
            time.sleep(2)
            
        return None

    def close(self):
        self.ser.close()

# Integration into your main loop
# otp_manager = HardwareOTPManager(port="COM4") # Update to your port
# otp = otp_manager.get_otp_from_modem()

# --- Execution Example ---
if __name__ == "__main__":
    otp_manager = HardwareOTPManager(port="/dev/cu.SAMSUNG_MDMRZ8R81C9N3E2")
    # Search for an OTP from a specific sender (e.g., 'Google', 'ICICI', 'Apple')
    otp = otp_manager.get_otp_from_modem(sender_name="ICICI")
    
    if otp:
        print(f"Your OTP is: {otp}")
    else:
        print("Failed to retrieve OTP.")
        
    otp_manager.close()