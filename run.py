import os
from fulfillment import process

from dotenv import load_dotenv
load_dotenv()

SMS_SENDER_MOB_NO = "8448492299"

#POST_URL = "https://vahan.parivahan.gov.in/eTransPgi/vahanPGIWebService"
#ENCRYPTED_DATA = "6847fb4d1d0520b34fcd0370aec81212d024b55ccebc09d3bb21de149a5940eb3752d93646ce85d93595a0dc4ae0fdde9ba8306ff9edba9a84f9f58f84c83c2c7bdd360c6da8f5e12ae5b1bf2c8a76bec6bc085b24df95a7273454cc03cf28a282308c547c0081f3f75f3cdcce8e2d61352d0ae5712fde5535949c14a87dc5fbd6b38cf3f56cfd191447acacee8e18f3bbc240f6509ac2c16dc5f454024077d782536f9027db759ea08ef303143d60ec200044337d3bf6f297dad81da6bc379ecc4a316dbcab3f93dca4bc2059a1eb420ce2d57af1892353d754cff7d95ce69419c6a82b6c8f9424cc70368caf1098a1a8791152f4735a29fa7a119bc11c38d1ff1cf636083fbd98609f026ee46d229c9f907eec662f87f3ed5ba5ecc3a947da1f6f4b1f7ab051271a62243fd99d7828f0097e32a6d190ee07d40ee178fc45aaa1944533f7d6632a1b229dc865f1d27a43c2a8cefcb53ce43a530e2f719509fc8b0bbbe9b9a449fb0d25105941822b8ffda3e96fb706ba7539ac59453aa7ac8d695b81c2703260ecf6eda04951795cdceb046342e6a96aae4b291634afb7e1aad70d65420d63a8eaa482c646628d972287d34a00c1718a96fbc9e3948850edd38b43cacff9369400a37f2a07bad9dee595f3e0e5504d92ccba10bbe93665e6635efb666f0ba8f67fe029af2f7f129a667b1d34d0e30be48538a4bf19fa964d9541c6596da59063a717c448b27d5ef83000e9ec93d319bf0069c542f2a60c5b0214174b2caccb69daab7d861d35d61430e97ecbd709b5b8d4d90de2f369c53ec76db409816019ca02f572a186f908ec50d928300b9320015792ae3acc43efb3c5579cfd252db8dc0a1c4830c258fdc54b830cc861125fae2f2ae97d87183bc30e1355da4669ff223b1e4dd31e647893216aa4872f34f15036"

# icici_user_id = os.getenv("ICICI_NETBANKING_USER_ID")
# icici_password = os.getenv("ICICI_NETBANKING_PASSWORD")
# mob_no_for_otp = os.getenv("MOB_NO_FOR_OTP")
# FW_BASE_URL = os.getenv("FW_BASE_URL")

# print("NETBANKING USER ID", icici_user_id)
# print("NETBANKING PASSWORD", icici_password.replace("", "*"))
# print("MOB NO FOR OTP", mob_no_for_otp)
# print("FW BASE URL", FW_BASE_URL)
# print("-" * 50)
# proxy=None
    
def main():
    
    APP_ID = input("Enter Appointment ID: ")
    CHALLAN_NO = input("Enter Challan No: ")
    PMT_REMARKS = input("Enter Payment Remarks: ")
    
    result = process(order_item_id=APP_ID, type="C2B", reg_no=None, challan_no=CHALLAN_NO, payment_remarks=PMT_REMARKS)
    print("result", result)

if __name__ == "__main__":
    #try:
    main()
    #except Exception as e:
    #    print("main failed", e)
