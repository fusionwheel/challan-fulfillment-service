import pprint
import os
import requests
import json
import base64
import time
import dateutil.parser
from urllib import parse
from challan_workflow.services.c24 import C24SearchChallanOrderServiceProvider
from challan_workflow.base import exception
from challan_workflow.services.redirections import handle_post_redirect

FW_BASE_URL = os.getenv("FW_BASE_URL")

class FWLink:
    base_url = None #"https://live.fusionwheel.co.in/api/"
    token_url = None
    refresh_token_url = None
    
    scope = "read write"
    client_id = None
    client_secret = None
    token_info = {}
    
    
    def __init__(self, reg_no: str, challan_no: str, mobile_no: str, **kwargs):
        print("FWLink __init__", os.getenv("FW_BASE_URL"))
        self.base_url =             os.getenv("FW_BASE_URL") or "http://localhost:8000" #"https://live.fusionwheel.co.in/api/"
        self.token_url =            f"{self.base_url}/api/oauth2/token/"
        self.refresh_token_url =    f"{self.base_url}/api/oauth2/token/"
        
        self.reg_no = reg_no
        self.challan_no = challan_no
        self.owner_mobile_no = mobile_no
        self.owner_name = kwargs.get("owner_name", "") or ""
        self._session = requests.Session()
        self.load_token_info()
        self.client_id = self.client_id  or os.getenv("FW_CLIENT_ID")
        self.client_secret = self.client_secret or os.getenv("FW_CLIENT_SECRET")
        self.__session_id = None
        self._is_internal = 0
    
    @classmethod
    def from_order_item_id(cls, order_item_id: int, challan_no: str):
        c24 = C24SearchChallanOrderServiceProvider()
        obj = cls(**c24.get_challan_details_by_order_item_id(order_item_id))
        obj.challan_no = obj.challan_no or challan_no
        obj._is_internal = 0
        return obj
    
    @classmethod
    def from_appointment_id(cls, app_id: int, challan_no: str):
        c24 = C24SearchChallanOrderServiceProvider()
        obj = cls(**c24.get_challan_details_by_app_id(app_id, challan_no))
        obj._is_internal = 1
        return obj
    
    def generate_token(self):
        print("Generating token...")
        if not self.client_id or not self.client_secret:
            raise Exception("Client ID or Client Secret not configured")

        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1.1 Safari/605.1.15",
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded}"
        }
        response = self._session.post(self.token_url, headers=headers, data={"grant_type": "client_credentials", "scope": self.scope})
        print(response, response.text)
        response.raise_for_status()
        self.token_info = response.json()
        if self.token_info:
            if self.token_info.get("expires_in"):
                self.token_info["expires_at"] = time.time() + self.token_info["expires_in"]
            
            self.save_token_info()
    
    def is_token_expired(self):
        if self.token_info:
            return time.time() > self.token_info.get("expires_at")
        return False
    
    def refresh_token(self):
        self.generate_token()
        # headers = {
        #     "Content-Type": "application/x-www-form-urlencoded",
        #     "Authorization": f"Basic {base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()}"
        # }
        # response = self._session.post(self.refresh_token_url, headers=headers, data={"grant_type": "refresh_token", "refresh_token": self.token_info.get("refresh_token")})
        # response.raise_for_status()
        # self.token_info = response.json()
        # if self.token_info:
        #     if self.token_info.get("expires_in"):
        #         self.token_info["expires_at"] = time.time() + self.token_info["expires_in"]
            
        #     self.save_token_info()
    
    def get_headers(self):
        if self.is_token_expired():
            self.refresh_token()
        return {
            "Authorization": f"Bearer {self.token_info.get('access_token')}",
            "Content-Type": "application/json",
            "User-Agent": "PostmanRuntime/7.44.1"
        }
    
    def save_token_info(self):
        with open("token_info.json", "w", encoding="utf-8") as f:
            json.dump(self.token_info, f)
    
    def load_token_info(self):
        if os.path.exists("token_info.json"):
            try:
                with open("token_info.json", "r", encoding="utf-8") as f:
                    self.token_info = json.load(f)
            except Exception as e:
                print("Failed to load token info", e)
    
    def process_request(self, url: str, method: str = "GET", data: dict = None, headers=None):
        headers = headers or self.get_headers()
        response = self._session.request(method, url, json=data, headers=headers)
        #print("process_request", url, method, data, headers)
        #print(response, response.text)
        if response.status_code in [401, 403]:
            if not self.token_info:
                self.generate_token()
            else:
                if self.is_token_expired():
                    self.refresh_token()
                headers = headers or self.get_headers()
                response = self._session.request(method, url, json=data, headers= headers)
                #print("process_request", url, method, data, headers)
                #print(response, response.text)
        #response.raise_for_status()
        return response
    
    def send_otp(self, mobile_no: str):
        url = f"{self.base_url}/backend/app/auto-payment-link/challan/otp/trigger"
        for i in range(0,5):
            response = self.process_request(url, method="POST", data={"mobile_no": mobile_no, "challan_no": self.challan_no})
            try:
                data = response.json()
            except:
                data = {
                    "status": "error",
                    "message": "OTP Trigger Failed"
                }
            print("-"*50)
            print(f"  FW service | {i+1}. status_code: {response.status_code}")
            print(f"  FW service | {i+1}. Data:")
            pprint.pprint(data, indent=3)
            print(f"  FW service | {i+1}. Status: {data.get('status')}")
            print(f"  FW service | {i+1}. Message: {data.get('message')}")
            if response.status_code == 200 and str(data.get("status")).lower() in ["success"]:
                self.__session_id = data.get("session_id")
                return data                
            time.sleep(2)
        raise exception.OTPTriggerFailed("OTP Trigger Failed")
    
    def verify_otp(self, otp):
        url = f"{self.base_url}/backend/app/auto-payment-link/challan/otp/verify"
        if not self.__session_id:
            raise exception.SessionError("Please send OTP First")
        
        for i in range(5):
            response = self.process_request(url, method="POST", data={"otp": otp, "session_id": self.__session_id})
            try:
                data = response.json()
            except:
                data = {
                    "status": "error",
                    "message": "OTP Verification Failed"
                }
            print("-"*50)
            print(f"  FW service |{i+1}. status_code: {response.status_code}")
            print(f"  FW service |{i+1}. Data:")
            pprint.pprint(data, indent=3)
            print(f"  FW service |{i+1}. Status: {data.get('status')}")
            print(f"  FW service |{i+1}. Message: {data.get('message')}")
            if response.status_code == 200 and str(data.get("status")).lower() in ["success"]:
                return data.get("data")
            
        raise exception.OTPVerificationFailed("OTP Verification Failed")
    
    def marked_failed(self, data):
        venData = (data.get("response") or {}).get("venData")
        pending_url = (data.get("response") or {}).get("url")

        if venData and pending_url:
            return handle_post_redirect(
                url=pending_url, 
                method="POST", 
                data={"encdata": venData},
                challan_no=self.challan_no,
                only_text=True
            )
    
    def generate_payment_link(self, verify_payment: int = 0):
        """_summary_

        Args:
            verify_payment (int, optional): _description_. Defaults to 0.
            0 -> link generation
            1 -> verify payment
            2 -> department error

        Returns:
            _type_: _description_
        """
        url = f"{self.base_url}/backend/app/auto-payment-link/challan/generate"
        if not self.__session_id:
            raise exception.SessionError("Please send OTP First")
        
        payload = {
            "reg_no": self.reg_no,
            "challan_no": self.challan_no,
            "session_id": self.__session_id,
            "verify_payment": verify_payment,
            "is_internal": self._is_internal   
        }
        if self.owner_mobile_no:
            payload["mobile_no"] = self.owner_mobile_no
        if self.owner_name:
            payload["owner_name"] = self.owner_name
        
        max_attempt = 5
        self.is_department_error = False
        
        for i in range(max_attempt):
            try:
                if payload["verify_payment"] != verify_payment:
                    payload["verify_payment"] = verify_payment
                    
                response = self.process_request(url, method="POST", data=payload)
                data = response.json()
            except Exception as e:
                print(f"  FW service |  {i+1}. Failed to parse response: {e}")
                continue
            
            print(f"  FW service |{i+1}. status_code: {response.status_code}")
            print(f"  FW service |{i+1}. Data:")
            pprint.pprint(data, indent=3)
            print(f"  FW service |  {i+1}. Status: {data.get('status_code')}")
            print(f"  FW service |  {i+1}. Message: {(data.get('response') or {}).get('reason')}")
            print("-"*50)
            
            if response.status_code == 200:
                message = ((data.get("response") or {}).get("message") or "").lower()
                reason = ((data.get("response") or {}).get("reason") or "").lower()
                
                print("  FW service | Payment Link Generation | message: ", message)
                print("  FW service | Payment Link Generation | reason: ", reason)
                print("-"*50)
                
                if "payment is pending" in message or "payment is pending" in reason:
                    if str(self.challan_no)[:2] in ["AP", "KL", "TN"]:                        
                        print("  FW service | Payment Already Pending | attempting with verify_payment for  =>", verify_payment)
                        try:
                            self.generate_payment_link(verify_payment=1)
                        except Exception as e:
                            print("  FW service | Pending Payment Link | making Failed | Exception: ", e)
                        continue
                    else:
                        result = self.marked_failed(data)
                        if result:
                           print(f"  FW service |  {i+1}. Payment Link marked failed/success {self.challan_no}")
                           raise Exception("Payment Link marked failed/success")
                   
                    raise exception.PaymentLinkAlreadyGenerated("Payment Link Already Generated! Challan Payment is pending")
            
            if response.status_code == 200:
                if "payment verification" in ((data.get("response") or {}).get("message") or "").lower():
                    # verify payment
                    result = self.marked_failed(data)
                    if result:
                       print(f"  FW service |  {i+1}. Payment Link marked failed/success {self.challan_no}")
                       raise Exception("Payment Link marked failed/success")
                      
                    raise exception.PaymentLinkAlreadyGenerated("Payment Link Already Generated! Challan Payment is pending")
                
                response_data = (data.get("response") or {})
                if "status" in response_data and response_data.get("status") == 200:
                    if "venData" in response_data and response_data.get("venData"):
                        return {
                            "payment_url": response_data.get("vurl"),
                            "payment_method": "POST",
                            "payment_data": response_data.get("venData")
                        }
                    else: 
                        return {
                            "payment_url": response_data.get("url"),
                            "payment_method": "GET",
                            "payment_data": None
                        }
                    
                if "department" in ((data.get("response") or {}).get("reason") or "").lower():
                    self.is_department_error = True
                    
                    print(f"  FW service | {i+1}. Department Error raised | current_attempt: {i+1} | max_attempt: {max_attempt}")
                    
                    if i >= max_attempt:
                        raise exception.DepartmentError("Invalid Department Type!")
                    
                    if str(self.challan_no)[:2] in ["AP", "KL", "TN"]:
                        verify_payment = 0 if verify_payment == 2 else 2 # invert verify_payment
                        print(f"  FW service | {i+1}. Department Error attempting with verify_payment for  =>", verify_payment)
                        continue
                    else:
                        raise exception.DepartmentError("Invalid Department Type!")
                
                if "invalid request" in ((data.get("response") or {}).get("reason") or "").lower():
                    raise exception.PaymentLinkOfflineChallanError("Found Offline Challan!")
            
            #print(f"attempt {i} => generate_payment_link =>", response, data)
            if response.status_code == 200 and (data.get("status_code") or -99 ) == 200:
                # example offline challan url: https://echallan.parivahan.gov.in/api/challan-status/challan/UP152562230701165804
                if "challan-status" in data.get("response").get("payment_url"):
                    raise exception.PaymentLinkOfflineChallanError("Found Offline Challan!")
                return data.get("response")
        
        raise exception.PaymentLinkError("Payment Verification Failed" if verify_payment == 1 else "Payment Link Generation Failed")
    
    def delete_otp(self, mobile_no: str, challan_no: str) -> bool:
        print(f"  FW service |  1. Deleting OTP count for challan {challan_no}...")
        BASE_URL = "https://echallan.parivahan.gov.in"
        payload = json.dumps({
            "mobile_no": mobile_no,
            "challan_no": challan_no
        })
        url = f"{BASE_URL}/index/delete-otp-count?data={parse.quote(payload)}"
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Origin': BASE_URL,
            'Referer': f'{BASE_URL}/index/accused-challan',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=0',
            'Content-Length': '0'
        }
        
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            print(f"  FW service |  1. ✓ OTP Deletion response: {result}")
            
            return result.get('status') == 'success'
            
        except Exception as e:
            print(f"  FW service |  1. ✗ Error Deleting OTP: {e}")
            return False