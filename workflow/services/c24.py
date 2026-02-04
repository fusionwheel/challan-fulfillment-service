import os
import json 
import requests


class C24SearchChallanOrderServiceProvider:
    C24_API_KEY = None
    C24_BASE_URL = None
    
    def __init__(self) -> None:
        self._session = requests.Session()
        self.C24_API_KEY = os.environ.get('C24_API_KEY')
        self.C24_BASE_URL = os.environ.get('C24_BASE_URL') or "https://c2b-partner-gateway-stage.qac24svc.dev"
        
    @property
    def headers(self):
        return {
            "x-api-key": self._get_api_key(),
            #"User-Agent": "fusion-wheel/auto-challan-fullfillment/1.0.0"
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1.1 Safari/605.1.15"
        }
    
    def _get_api_key(self):
        if not self.C24_API_KEY:
            raise Exception("`C24_API_KEY` Not configured in environment variables")
        return self.C24_API_KEY
    
    def get_challan_details_by_order_item_id(self, order_item_id):
        url = f"{self.C24_BASE_URL}/c2b-vas/order-item/{order_item_id}"
        response = self._session.get(url, headers=self.headers)
        print("get_challan_details_by_order_item_id")
        print(response.text)
        if response.status_code == 200:
            result = response.json()
            return {
                "reg_no": (result.get("data") or {}).get("regNumber"),
                "challan_no": ((result.get("data") or {}).get("productJsonMap") or {}).get("challanNo"),
                "owner_name": (result.get("data") or {}).get("ownerName"),
                "mobile_no": (result.get("data") or {}).get("mobileNo"),
            }
        
        raise Exception("Challan details not found")
    
    def get_challan_details_by_app_id(self, app_id, challan_no):
        url = f"{self.C24_BASE_URL}/challan-service/api/v1/challan-item/reg-number?appointmentOrderId={app_id}&noticeNumber={challan_no}"
        response = self._session.get(url, headers=self.headers)
        print("get_challan_details_by_app_id", app_id, challan_no)
        print(response.text)
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == 200:
                reg_no = (result.get("detail") or {}).get("regNumber")
                if reg_no:
                    return {
                        "reg_no": reg_no,
                        "challan_no": challan_no,
                        "owner_name": (result.get("detail") or {}).get("ownerName"),
                        "mobile_no": (result.get("detail") or {}).get("mobileNo")
                    }                    
        raise Exception("Challan details not found")