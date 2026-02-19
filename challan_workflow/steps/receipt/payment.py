import re
from challan_workflow.steps.core.common import BasePage
from playwright.sync_api import Page

class PostPaymentSuccessRedirectPage(BasePage):
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
    
    def redirect(self):
        self.page.wait_for_timeout(1000)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_load_state("load")
        self.page.wait_for_load_state("domcontentloaded")
        try:
            print("try Post Payment Success Redirect 1")
            click_here = self.page.get_by_text(re.compile(r"Click here", re.I))
            click_here.wait_for(state="visible", timeout=5000)
            click_here.click()
            return
        except Exception as e:            
            print(f"Post Payment Success Redirect failed: {str(e)}")
        
        try:
            self.page.evaluate("redirectToHandler()")
            self.page.wait_for_load_state("load")
            print("JS Fallback successful.")
            self.page.wait_for_timeout(1000)
            return
        except Exception as e:
            print(f"Post Payment Success Redirect failed: {str(e)}")
    # def download(self):
    #     receipt_url = self.find_receipt()
    #     #self.page.goto(receipt_url)
    #     self.wait_for_timeout(1000)
        
        
    def proceed(self):
        try:
            self.wait_for_page_to_load()
            self.page.wait_for_load_state("domcontentloaded")
            self.redirect()
            self.wait_for_page_to_load()
            print(f"HR Post Payment Success Redirect success")
        except Exception as e:
            print(f"HR Post Payment Success Redirect failed: {str(e)}")
            

