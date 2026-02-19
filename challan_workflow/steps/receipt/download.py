import re
from challan_workflow.steps.core.common import BasePage
from playwright.sync_api import Page

class DownloadReceiptPage(BasePage):
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
    
    def find_receipt(self):
        self.page.wait_for_timeout(1000)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_load_state("load")
        self.page.wait_for_load_state("domcontentloaded")
        receipt = self.page.get_by_role("link", name=re.compile("PRINT YOUR RECEIPT", re.IGNORECASE))
        receipt.wait_for(state="visible", timeout=3000) 
        receipt_url = receipt.get_attribute("href")
        return receipt_url
    
    # def download(self):
    #     receipt_url = self.find_receipt()
    #     #self.page.goto(receipt_url)
    #     self.wait_for_timeout(1000)
        
        
    def proceed(self):
        try:
            receipt_url = self.find_receipt()
            self._ctx.receipt_url = receipt_url
            self.update_status("success", "RECEIPT_DOWNLOAD_SUCCESS", "Receipt downloaded successfully!", step="RECEIPT_DOWNLOAD_PAGE")
            return receipt_url
        except Exception as e:
            self.update_status("failed", "RECEIPT_DOWNLOAD_FAILED", "Receipt download failed!", step="RECEIPT_DOWNLOAD_PAGE")
            raise e
