import os
from google.api_core.gapic_v1 import method
import requests
import json
from urllib import parse
import dateutil.parser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from challan_workflow.services.redirections import handle_post_redirect
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import logging
logger = logging.getLogger(__name__)

FW_BASE_URL = os.getenv("FW_BASE_URL")
PROXY = os.getenv("PROXY")

class Parivahan:
    base_url = "https://echallan.parivahan.gov.in"
    
    def __init__(self, reg_no: str=None, challan_no: str=None, **kwargs):
        
        self.reg_no = reg_no
        self.challan_no = challan_no
        self._session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[502, 503, 504],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retries)
        self._session.mount('https://', adapter)
        self._session.mount("http://", adapter)
    
    def process_request(self, *args, **kwargs):
        kwargs.setdefault("timeout", 15)
        
        last_exception = None
        for i in range(2):    
            try:
                return self._session.request(*args, **kwargs)
            except requests.exceptions.ConnectionError as ce:
                logger.error(f"Parivahan service | ✗ Connection was reset or aborted: {ce}")
                last_exception = ce
        raise last_exception    
    
    def headers(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/index/accused-challan',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=0',
            'Connection': 'keep-alive',
        }
    
    def get_proxies(self):
        if PROXY:
            return {"http": PROXY, "https": PROXY}
        return None    
    
    def delete_otp(self, mobile_no: str, challan_no: str) -> bool:
        self.challan_no = challan_no or self.challan_no
        
        logger.info(f"  Parivahan service | Deleting OTP count for challan {self.challan_no}...")
        payload = json.dumps({
            "mobile_no": mobile_no,
            "challan_no": self.challan_no
        })
        url = f"{self.base_url}/index/delete-otp-count?data={parse.quote(payload)}"
        try:
            response = self.process_request("POST", url, headers=self.headers(), proxies=self.get_proxies())
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"  Parivahan service | ✓ OTP Deletion response: {result}")
            
            return result.get('status') == 'success'
        
        except Exception as e:
            logger.error(f"  Parivahan service | ✗ Error Deleting OTP: {e}")
            return False
    
    def clean_header_name(self, name: str) -> str:
        mapping = {
            "vehicle_no": "regn_no",
            "application_no": "challan_no",
            "transaction_no/auin": "transaction_no",
            "payment_date": "op_dt",
            "status": "application_status",
            "amount": "fees",
            "grn": "grn_no",
            "payment_gateway": "api_name"
        }
        name = name.strip().replace("\n", "").replace("\r", "").replace("\t", "").replace(".", "").lower().replace(" ", "_")
        return mapping.get(name, name)
    
    def etrans_pgi_payment_status(self, challan_no: str):
        self.challan_no = challan_no or self.challan_no
        logger.info(f"  Parivahan service | ETrans PGI payment status {self.challan_no}...")
        payload = {
            "selection": "6",
            "Challan No./Application No.": self.challan_no
        } 
        url = f"https://vahan.parivahan.gov.in/eTransPgi/paymentDetails"
        
        headers = self.headers().copy()
        headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'text/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Origin': 'https://vahan.parivahan.gov.in',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1.1 Safari/605.1.15',
            'Referer': 'https://vahan.parivahan.gov.in/eTransPgi/paymentDetails',
        })        
        
        try:
            response = self.process_request("POST", url, headers=headers, data=parse.urlencode(payload), proxies=self.get_proxies())
            response.raise_for_status()
           
            if "No Record Found" in response.text:
                logger.info("  Parivahan service | ✓ ETrans PGI payment status response: No Record Found")
                return None
            try:
                table_start = response.text.find("<table>")
                table_end = response.text.find("</table>")
            except:
                table_start = -1
                table_end = -1
            
            if table_start == -1 or table_end == -1:
                logger.error(f"  Parivahan service | ✗ ETrans PGI payment status response: {response.text[:100]}")
                return None
            else:
                table_body = response.text[table_start:table_end+8]
                logger.info(f"  Parivahan service | ✓ ETrans PGI payment status response: {table_body}")
                soup = BeautifulSoup(table_body, 'html.parser')
                table = soup.find('table')
                rows = table.find_all('tr')
                data, headers = [], []
                for row in rows:
                    ths = row.find_all('th')
                    if (not headers) and ths:
                        cols = [self.clean_header_name(ele.text) for ele in ths]
                        headers = cols
                        continue
                    
                    cols = row.find_all('td')
                    cols = {headers[p]: ele.text.strip().replace("\n", "").replace("\r", "").replace("\t", "") for p, ele in enumerate(cols)}
                    data.append(cols)
                if data:
                    return data[-1]
                return None
            
        except Exception as e:
            logger.error(f"  Parivahan service | ✗ Error ETrans PGI payment status: {e}")
            return None
        
    def get_payment_status(self, reg_no: str=None, challan_no: str=None):
        self.challan_no = challan_no or self.challan_no
        self.reg_no = reg_no or self.reg_no
        
        logger.info(f"  Parivahan service | Challan payment status {self.challan_no}...")
        if self.reg_no:
            payload = json.dumps({"regn_no": self.reg_no})
        else:
            payload = json.dumps({"challan_no": self.challan_no})
            
        url = f"{self.base_url}/payment-verification/challan-list?data={parse.quote(payload)}"
        try:
            response = self.process_request("POST", url, headers=self.headers(), proxies=self.get_proxies())
            response.raise_for_status()
            result = response.json()
            print(f"  Parivahan service | ✓ Challan payment status response: {result}")
            if "result" in result and isinstance(result.get("result"), list) and result.get("result"):
                for item in result.get("result") or []:
                    if item.get("challan_no") == self.challan_no:
                        return item
            
            return None
            
        except Exception as e:
            logger.error(f"  Parivahan service | ✗ Error Challan payment status: {e}")    
            return None
    
    def is_payment_pending(self, pmt_st_data) -> bool:
        if pmt_st_data.get("application_status") == "R": # pending
            return True
        return False
    
    def is_payment_success(self, pmt_st_data) -> bool:
        if pmt_st_data.get("application_status") == "S": # success
            return True
        return False
    
    def is_payment_initiated_recently(self, pmt_st_data) -> bool:
        if pmt_st_data.get("application_status") in ["R", "S"]:
            if pmt_st_data.get("op_dt"):
                try:
                    op_dt = dateutil.parser.parse(pmt_st_data.get("op_dt"), ignoretz=True, dayfirst=True)
                    if op_dt + timedelta(minutes=15) >= datetime.now():
                        return True
                except Exception as e:
                    logger.error(f"  Parivahan service | ✗ Error parsing op_dt: {e}")
        return False
    
    def call_payment_verification(self, url: str, method: str, data: dict):
        logger.info(f"  Parivahan service | Call Payment Verification for challan {self.challan_no}...")
        result = handle_post_redirect(url=url, method=method, data=data, challan_no=self.challan_no, only_text=True)
        print(f"  Parivahan service | ✓ Payment Verification response: {result}")
        return bool(result)
    
    def verify_payment(self, pmt_st_data) -> bool:
        logger.info(f"  Parivahan service | Verify Payment for challan {self.challan_no}...")
        payload = json.dumps({
            "regn_no": pmt_st_data.get("regn_no"),
            "challan_no": pmt_st_data.get("challan_no"),
            "transaction_no": pmt_st_data.get("transaction_no"),
            "amount": pmt_st_data.get("fees"),
            "state_cd": pmt_st_data.get("state_cd"),
            "dpt_cd": pmt_st_data.get("dpCd"),
            "api_name": pmt_st_data.get("verify_api_name"),
        })
        url = f"{self.base_url}/payment-verification/proceed-payment-verification?data={parse.quote(payload)}"
        
        try:
            logger.info(f"  Parivahan service | Payment Verification URL: {url}")
            response = self.process_request("POST", url, headers=self.headers(), allow_redirects=True, proxies=self.get_proxies())
            response.raise_for_status()
            result = response.json()
            print(f"  Parivahan service | ✓ Payment Verification response: {result}")
            if response.status_code == 200:
                if str(result.get("status")) == "203":
                    print("  Parivahan service | ✓ Payment already verified.")
                    return True
                if str(result.get("status")) == "200":
                    # OLD GATEWAY
                    pgi_url = (result.get("result") or {}).get("pgi_url")
                    logger.info(f"  Parivahan service | Old Gateway URL: {pgi_url}")
                    if pgi_url:
                        return self.call_payment_verification(url=pgi_url, method="GET", data={})
                    
                    # NEW SBI GATEWAY
                    vurl = result.get("vurl")
                    encdata=result.get("venData")
                    logger.info(f"  Parivahan service | New Gateway URL: {vurl}")
                    if vurl and encdata:
                        return self.call_payment_verification(url=vurl, method="POST", data={"encdata": encdata})
                
            return None
            
        except Exception as e:
            logger.error(f"  Parivahan service | ✗ Error Payment Verification: {e}")    
            return None
        