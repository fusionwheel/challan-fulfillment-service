import re
from workflow.steps.core.common import BasePage
from playwright.sync_api import Page

class WBGRIPSPaymentPage(BasePage):
    
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
        self.grn_number = None

    def check_n_verify(self):
        """Step 1: Confirm details and move to Payment Mode selection"""
        checkbox = self.page.locator("mat-checkbox#mat-checkbox-1")
        checkbox.wait_for(state="visible", timeout=10000)
        
        # Check if it's already checked, if not, click it
        if "mat-checkbox-checked" not in checkbox.get_attribute("class"):
            self.human_click_by_element(checkbox)
            
        self.wait_for_timeout(1000)

        # Click the 'Next' button to move to Step 2
        next_btn = self.page.get_by_role("button", name=re.compile("Next", re.IGNORECASE))
        self.human_click_by_element(next_btn)
        print("Moved to Payment Mode selection.")

    def select_bank_and_gateway(self):
        """Step 2: Select Payment Gateway (SBI ePay) and Bank"""
        # Selecting Payment Mode (usually a dropdown or radio button in Step 2)
        # Based on your HTML, 'SBI Epay' is the target gateway
        
        # Select the Gateway (SBI ePay)
        gateway_dropdown = self.page.locator("mat-select[placeholder*='Bank']")
        self.human_click_by_element(gateway_dropdown)
        self.page.get_by_role("option", name=re.compile("SBI ePay", re.IGNORECASE)).click()
        
        # Select the Payment Mode (Online Payment)
        payment_mode_dropdown = self.page.locator("mat-select[placeholder*='Payment Mode']")
        payment_mode_dropdown.wait_for(state="visible")
        self.human_click_by_element(payment_mode_dropdown)
        self.page.get_by_role("option", name="Online Payment").click()
        

        # Click Next - This triggers the GRN Popup
        next_btn = self.page.get_by_role("button", name=re.compile("Next", re.IGNORECASE))
        self.human_click_by_element(next_btn)

    def handle_grn_popup(self):
        """Handles the 'OK' popup that displays the GRN"""
        # The popup in GRIPS 2.0 is often a mat-dialog or a standard window.alert
        # Capturing the GRN if it's in a dialog
        popup_ok_btn = self.page.get_by_role("button", name="OK")
        popup_ok_btn.wait_for(state="visible", timeout=15000)
        
        # Optional: Extract GRN text for logging
        dialog_text = self.page.locator("mat-dialog-container").inner_text()
        print(f"Popup detected: {dialog_text}")
        
        self.human_click_by_element(popup_ok_btn)
        self.wait_for_timeout(1000)

    def click_pay_now(self):
        """Step 3: Final Transaction Details and Redirect"""
        # The 'Pay Now' button only appears after the GRN popup is dismissed
        pay_now_btn = self.page.get_by_role("button", name=re.compile("Pay Now", re.IGNORECASE))
        pay_now_btn.wait_for(state="visible", timeout=10000)
        
        self.human_click_by_element(pay_now_btn)
        print("Redirecting to Bank Gateway...")

    def proceed(self):
        """Full workflow execution"""
        try:  
            # Step 1: Review
            self.check_n_verify()
            self.wait_for_timeout(1000)
            self.wait_for_page_to_load()
            # Step 2: Selection
            self.select_bank_and_gateway()
            self.wait_for_timeout(1000)
            self.wait_for_page_to_load()
            # Handle the OK Popup
            self.handle_grn_popup()
            self.wait_for_timeout(1000)
            self.wait_for_page_to_load()
            
            # Step 3: Final Pay Now
            self.click_pay_now()
            self.wait_for_timeout(1000)
            self.update_status("success", "GRN_SUCCESS", "Payment link initialized successfully", step="GRIPS_WB_PAGE")
        except Exception as e:
            self.update_status("failed", "GRN_FAILED", "Payment link initialization failed", step="GRIPS_WB_PAGE")
            raise e
        
        #self.wait_for_page_to_load()