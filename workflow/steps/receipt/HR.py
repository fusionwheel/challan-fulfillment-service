import re
from workflow.steps.core.common import BasePage
from playwright.sync_api import Page

class HRPostPaymentSuccessRedirectPage(BasePage):
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
    
    def redirect(self):
        self.page.wait_for_timeout(1000)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_load_state("load")
        click_here = self.page.get_by_role("link", name=re.compile("Click Here", re.IGNORECASE))
        click_here.wait_for(state="visible", timeout=3000)
        click_here.click()
        
    # def download(self):
    #     receipt_url = self.find_receipt()
    #     #self.page.goto(receipt_url)
    #     self.wait_for_timeout(1000)
        
        
    def proceed(self):
        try:
            self.redirect()
            print(f"HR Post Payment Success Redirect success")
        except Exception as e:
            print(f"HR Post Payment Success Redirect failed: {str(e)}")

