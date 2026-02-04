import os
from workflow.core.fw import FWLink
from sms.adb_manager import ADBOTPManager


APP_ID = "10141409756"
CHALLAN_NO = "HR46416250914125073"




if __name__ == "__main__":
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("FW_CLIENT_ID", os.getenv("FW_CLIENT_ID"))
    print("FW_CLIENT_SECRET", os.getenv("FW_CLIENT_SECRET"))
    print("C24_API_KEY", os.getenv("C24_API_KEY"))
    print("C24_BASE_URL", os.getenv("C24_BASE_URL"))
    
    #otp_details = ADBOTPManager(sender_name="ICICI").get_otp_details()
    #print("otp =>", otp_details)
    
    fw_link = FWLink.from_appointment_id(app_id=APP_ID, challan_no=CHALLAN_NO)
    print(fw_link.reg_no)
    print(fw_link.challan_no)
    print(fw_link.owner_mobile_no)
    print(fw_link.owner_name)
    data = fw_link.send_otp(mobile_no="9266882972")
    print(data)
    
    adb_manager = ADBOTPManager(sender_name="VAAHAN")
    otp_details = adb_manager.get_otp_details(body_contains="getting challan detail at eChallan")
    print("otp =>", otp_details)
    
    verification_data = fw_link.verify_otp(otp=otp_details.get("otp"))
    print("verification_data =>", verification_data)
    
    # 2 for HR
    payment_data = fw_link.generate_payment_link(verify_payment=2)
    print("payment_data =>", payment_data)