import re
from challan_workflow.steps.core.common import BasePage
from playwright.sync_api import Page


class TNSBILandingPage(BasePage):
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
    
    def click_proceed(self):
        btn = self.page.get_by_text(re.compile(r"^Proceed to payment", re.IGNORECASE))
        btn.wait_for(state="visible", timeout=2000)
        btn.scroll_into_view_if_needed()
        
        with self.page.expect_navigation(wait_until="domcontentloaded") as nav_info:
            btn.click(timeout=5000)
    
    def proceed(self):
        try:
            self.wait_for_timeout(1000)
            self.click_proceed()
            print(f"{self.__class__.__name__} clicked proceed button....")
            self.wait_for_timeout(3000)
            
            self.update_status("success", "PROCEED_TO_PAY_SUCCESS", "Proceed to payment page successfully", step="TN_SBI_LANDING_PAGE")
        except Exception as e:
            self.update_status("failed", "PROCEED_TO_PAY_FAILED", "Proceed to payment page failed", step="TN_SBI_LANDING_PAGE")
            raise e
    


