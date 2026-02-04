
import re
from workflow.steps.core.common import BasePage
from playwright.sync_api import Page
from sms.adb_manager import ADBOTPManager
from workflow.base import exception

class IciciLoginPage(BasePage):
    user_id_selector = "#login-step1-userid"
    #password_selector = "#AuthenticationFG.ACCESS_CODE"
    password_selector = 'input[id="AuthenticationFG.ACCESS_CODE"]'
    submit_selector = "#VALIDATE_CREDENTIALS1"
    
    
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
        self.username = kwargs.get("netbanking_username")
        self.password = kwargs.get("netbanking_password")

    def login(self):
        # Login ID
        self.page.wait_for_selector(self.user_id_selector, timeout=20000)
        usr_id_input = self.page.locator(self.user_id_selector)
        print("usr_id_input", usr_id_input)
        usr_id_input.press_sequentially(self.username, delay=100)
        self.page.wait_for_timeout(1000)
        print("user_id filled")
        # Enable password field
        # self.page.evaluate(f"""
        #     const pwd = document.getElementById('AuthenticationFG.ACCESS_CODE');
        #     if (pwd) pwd.removeAttribute('readonly');
        # """)

        # Password
        self.page.keyboard.press("Tab")
        self.page.wait_for_timeout(500)
        pwd_input = self.page.locator(self.password_selector)
        #pwd_input.wait_for(state="attached", timeout=10000)
        
        pwd_input.scroll_into_view_if_needed()
        self.page.wait_for_timeout(500)
        
        pwd_input.click(force=True)
        self.page.wait_for_timeout(500)
        
        self.page.evaluate("""
        const el = document.getElementById('AuthenticationFG.ACCESS_CODE');
        if (el) el.removeAttribute('readonly');
        """)
        # 4. (Optional) Secondary safety: manually force removal via JS if focus isn't enough
        # self.page.evaluate(f"document.getElementById('AuthenticationFG.ACCESS_CODE').removeAttribute('readonly')")
        print("pwd_input removed readonly")
        pwd_input.press_sequentially(self.password, delay=120)
        #pwd_input.fill(self.password)
        self.page.wait_for_timeout(1000)
        print("pwd_input filled")

        # proceed btn click
        self.human_click(self.submit_selector)
        self.page.wait_for_timeout(2000)
        #self.page.screenshot(path="icici_login_proceed.png")
        print("proceed btn clicked")

    def is_login_successful(self):
        return not self.page.locator(self.user_id_selector).is_visible()
    
    def proceed(self):
        try:
            self.simulate_mouse_move()
            self.login()
            self.wait_for_page_to_load()
            self.update_status("success", "LOGIN_SUCCESS", "Login successful!", step="ICICI_LOGIN_PAGE")
            
        except Exception as e:
            self.update_status("failed", "LOGIN_FAILED", "Login failed!", step="ICICI_LOGIN_PAGE")
            raise e

class IciciTransactionPage(BasePage):
    # Selectors based on the provided HTML
    remarks_selector = "input[name='TranRequestManagerFG.ENT_REMARKS']"
    proceed_button_selector = "input[value='Proceed']"
    
    # Optional: If there is a "Review" or intermediate proceed button 
    # often used in this portal:
    alt_proceed_selector = "input[name='Action.CONTINUE_TXN_WITH_ADDN_DET']"

    def __init__(self, page: Page, payment_remarks: str = "", **kwargs):
        super().__init__(page, **kwargs)
        self.payment_remarks = payment_remarks

    def add_remarks_and_proceed(self):
        """
        Fills the remarks field and clicks the proceed/submit button.
        """
        # Ensure the page is ready
        self.wait_for_page_to_load()
        
        self.payment_remarks = self.payment_remarks or "" #input("Enter Remarks :")
        
        # 1. Fill Remarks
        self.page.wait_for_selector(self.remarks_selector, state="visible", timeout=15000)
        self.page.fill(self.remarks_selector, self.payment_remarks)

        # 2. Simulate human behavior before clicking
        self.simulate_mouse_move()
        
        # 3. Click Proceed
        try:
            self.human_click(self.proceed_button_selector)
        except Exception as e:
            print(f"Error clicking proceed button: {e}")
            for btn in self.page.locator(self.proceed_button_selector, has_text="Proceed"):
                if btn.is_visible():
                    self.human_click(btn)
                    break
            

    def verify_transaction_sent(self):
        return self.page.locator(self.remarks_selector).is_hidden()

    def proceed(self):
        try:
            self.add_remarks_and_proceed()
            self.page.wait_for_load_state("domcontentloaded")
            self.wait_for_page_to_load()
            self.page.wait_for_timeout(2000)
            self.update_status("success", "REMARKS_SUCCESS", "Remarks added successfully!", step="ICICI_REMARKS_PAGE")
        except Exception as e:
            self.update_status("failed", "REMARKS_FAILED", "Remarks failed!", step="ICICI_REMARKS_PAGE")
            raise e
        

class IciciTransactionOTPPage(BasePage):
    otp_selector = "input[name='TranRequestManagerFG.ONE_TIME_PASSWORD__']"
    submit_btn_selector = "input[value='Submit']"
    
    alt_submit_btn_selector = "input[name='Action.SUBMIT_TRANSACTION']"

    def __init__(self, page: Page, otp: str = "", **kwargs):
        super().__init__(page, **kwargs)
        self.otp = otp 

    def extract_tx_amount(self, message):
        try:
            amount = re.search(r'\d+\.\d{2}', message).group()
            self._ctx.pgi_amount = amount
            return amount
        except Exception as e:
            pass
        
    
    def enter_otp_and_submit(self):
        # 1. Fill OTP
        adb_manager = ADBOTPManager(sender_name="ICICI")
        otp_details = adb_manager.get_otp_details(body_contains="from ICICI Bank Acc")
        if not otp_details:
            raise exception.OTPNotFound("OTP not found !")
        otp = otp_details.get("otp") #self.otp or input("Enter OTP:")
        if not otp:
            raise Exception("OTP Required...")
        else:
            self.update_status("failed", "OTP_ENTERED", "OTP entered successfully !", step="ICICI_OTP_PAGE")
            print("entered OTP is:", otp)
         
        print(f"Waiting for OTP field: {self.otp_selector}")
        self.page.wait_for_selector(self.otp_selector, state="visible", timeout=15000)
        self.page.locator(self.otp_selector).press_sequentially(otp.strip(), delay=100)
        self.extract_tx_amount(otp_details.get("body"))
        
        # 2. Simulate human behavior before clicking
        self.simulate_mouse_move()
        
        # 3. Click Proceed
        #self.page.wait_for_selector(self.submit_btn_selector, state="visible", timeout=5000)
        self.page.wait_for_timeout(2000)
        btn_clicked = False
        for btn in self.page.locator(self.submit_btn_selector).all():
            if btn.is_visible():
                btn.scroll_into_view_if_needed()
                btn.click()
                btn_clicked = True
                break
        
        if not btn_clicked:
            raise Exception("OTP submit button not found")
        #self.human_click(self.submit_btn_selector)
        # except Exception as e:
        #     print(f"Error clicking submit button: {e}")
        #     for btn in self.page.locator(self.submit_btn_selector):
        #         if btn.is_visible():
        #             self.human_click(btn)
        #             break
    
    def extract_transaction_amount(self):
        selectors = [
            "#HREF_TranRequestManagerFG\\.AMOUNT", 
            "#HREF_TranRequestManagerFG\\.TOTAL_TXN_AMT",
            "#HREF_TranRequestManagerFG\\.TOTAL_AMT",
        ]
        for selector in selectors:
            try:
                loc = self.page.locator(selector)
                if loc.count() > 0:
                    amount = loc.first.inner_text().strip()
                    amount = float(amount)
                    print("amount is:", amount)
                    if amount:
                        self._ctx.pgi_amount = amount
                        #return amount
            except:
                pass
    
    def click_wait_for_redirect_to_receipt(self):
        self.page.wait_for_timeout(10000)
        
    
    def is_transaction_successful(self):
        # Usually looks for a "Transaction Successful" text or reference number
        return self.page.get_by_text("Successful", exact=False).is_visible()
    
    def proceed(self):
        # Ensure the page is ready
        try:
            self.update_status("success", "INIT_SUCCESS", "Transaction initialized", step="ICICI_OTP_PAGE")
            self.wait_for_page_to_load()
        except Exception as e:
            self.update_status("failed", "INIT_FAILED", "Transaction failed", step="ICICI_OTP_PAGE")
            raise e
        try:
            if not getattr(self._ctx, "pgi_amount", None):
                self.extract_transaction_amount()
            self.update_status("success", "AMOUNT_EXTRACTED_SUCCESS", "amount extracted successfully", step="ICICI_OTP_PAGE")
        except Exception as e:
            self.update_status("failed", "AMOUNT_EXTRACTED_FAILED", "amount extracted failed", step="ICICI_OTP_PAGE")
            raise e
        
        otp_sucess = 0
        try:
            self.enter_otp_and_submit()
            otp_sucess = 1
            self._ctx.otp_success = otp_sucess
            self.update_status("success", "OTP_SUBMITTED_SUCCESS", "otp submitted successfully", step="ICICI_OTP_PAGE")
            self.page.wait_for_load_state("domcontentloaded")
            self.wait_for_page_to_load()
            self.page.wait_for_timeout(2000)
        except Exception as e:
            if otp_sucess == 1:
                self.update_status("failed", "OTP_SUBMITTED_SUCCESS", "otp submitted successfully", step="ICICI_OTP_PAGE")
            else:
                self.update_status("failed", "OTP_SUBMITTED_FAILED", "otp submitted failed", step="ICICI_OTP_PAGE")
            raise e
        
        try:
            self.click_wait_for_redirect_to_receipt()
            self.update_status("success", "RECEIPT_REDIRECT_SUCCESS", "receipt redirect successful", step="ICICI_OTP_PAGE")
        except Exception as e:
            self.update_status("failed", "RECEIPT_REDIRECT_FAILED", "receipt redirect failed", step="ICICI_OTP_PAGE")
            raise e