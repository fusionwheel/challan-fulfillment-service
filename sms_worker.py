from fastapi import FastAPI, Request, HTTPException
from challan_workflow.sms.adb_manager import ADBOTPManager
import gc

app = FastAPI()

@app.post("/get-otp")
async def get_otp(request: Request):
    data = await request.json()
    
    sender = data.get("sender", "VAAHAN")
    body_contains = data.get("body_contains", "")

    manager = ADBOTPManager(sender_name=sender)
    otp_details = manager.get_otp_details(body_contains=body_contains)

    if not otp_details:
        raise HTTPException(status_code=404, detail="OTP_NOT_FOUND")
    del manager
    gc.collect()
    return otp_details

# if __name__ == "__main__":
#     import uvicorn, os
#     HOST = os.environ.get("SMS_HOST", "0.0.0.0")
#     PORT = os.environ.get("SMS_PORT", "9090")
#     # You must specify the host and port explicitly for the subprocess to find it
#     uvicorn.run(app, host=HOST, port=int(PORT))
