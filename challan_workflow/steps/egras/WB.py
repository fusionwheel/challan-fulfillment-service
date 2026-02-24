import re
from challan_workflow.steps.core.common import BasePage
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
        
        payment_mode_select = self.page.locator("mat-form-field:has-text('Payment Mode') mat-select")
        payment_mode_select.wait_for(state="visible", timeout=5000)
        payment_mode_select.click()
        
        #wait for overlay panel to appear
        panel = self.page.locator(".cdk-overlay-pane .mat-select-panel")
        panel.wait_for(state="visible", timeout=5000)
        
        # Wait for overlay options
        #sbi_epay_option = self.page.locator("mat-option").filter(has_text=re.compile("^SBI", re.IGNORECASE))
        sbi_epay_option = panel.locator("mat-option", has_text="SBI Epay")
        sbi_epay_option.wait_for(state="visible", timeout=5000)
        sbi_epay_option.click()

        self.wait_for_page_to_load()
        self.page.wait_for_timeout(1000)
        
        
        pay_through_select = self.page.locator("mat-form-field:has-text('Pay through') mat-select")
        pay_through_select.wait_for(state="visible", timeout=5000)
        pay_through_select.click()
        
        # Wait for NEW overlay panel
        panel = self.page.locator(".cdk-overlay-pane .mat-select-panel")
        panel.wait_for(state="visible", timeout=5000)
        
        #grips_option = self.page.locator("mat-option").filter(has_text=re.compile("^Payment Gateway", re.IGNORECASE))
        pay_th_option = panel.locator("mat-option", has_text="Payment Gateway/Bank")
        pay_th_option.wait_for(state="visible", timeout=5000)
        pay_th_option.click()
        self.page.wait_for_timeout(1000)
        # 3. Click Next
        next_btn = self.page.get_by_role("button", name=re.compile("^Next$", re.IGNORECASE))
        next_btn.click()

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
            self.page.wait_for_load_state("load", timeout=10000)
            self.update_status("success", "GRN_SUCCESS", "Payment link initialized successfully", step="GRIPS_WB_PAGE")
        except Exception as e:
            print(e)
            self.update_status("failed", "GRN_FAILED", "Payment link initialization failed", step="GRIPS_WB_PAGE")
            raise e
        
        #self.wait_for_page_to_load()

class WBGRIPSPostPaymentSuccessRedirectPage(BasePage):
    
    def redirect(self):
        self.page.wait_for_timeout(10000)
    
    def proceed(self):
        try:
            self.redirect()
            self.wait_for_page_to_load()
            print(f"WB Post Payment Success Redirect success")
        except Exception as e:
            print(f"WB Post Payment Success Redirect failed: {str(e)}")