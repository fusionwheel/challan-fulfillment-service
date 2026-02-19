import re
from challan_workflow.steps import gateway
from challan_workflow.steps.core.common import BasePage
from playwright.sync_api import Page
from challan_workflow.steps.core.common import SBIAggregatePage
from challan_workflow import config


class APSBIAggregatePage(SBIAggregatePage):
    
    def select_payment_gateway(self):
        
        default_gateway = config.GATEWAY_NAMES.get(self._ctx.st_cd) or self.gateway
        try:
            self.select_option_element_by_text('#dropOperator', default_gateway)
            self._ctx.gateway = default_gateway
            return
        except Exception as e:
            pass
        try:
            fallback_gateway = "SBI"
            self.select_option_element_by_text('#dropOperator', fallback_gateway)
            self._ctx.gateway = fallback_gateway
            return
        except Exception as e:
            print(f"Failed to select gateway: {e}")
            raise e
        
        
class APTreasuryGrnPage(BasePage):
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)

    def online_payment_click(self):
        self.page.get_by_role("button", name=re.compile("Online Payment", re.IGNORECASE)).first.click()
    
    def sbi_aggregate_click(self):
        self.page.get_by_role("button", name=re.compile("SBI", re.IGNORECASE)).first.click()
    
    def proceed(self):
        gateway = getattr(self._ctx, "gateway", None)
        if gateway != "CFMS":
            print("Skipping APTreasuryGrnPage for gateway", gateway)
            return
        
        try:
            self.wait_for_page_to_load()
            self.page.wait_for_load_state("domcontentloaded")
            self.wait_for_timeout(1000)
            
            self.online_payment_click()
            
            self.wait_for_page_to_load()
            self.page.wait_for_load_state("domcontentloaded")
            self.wait_for_timeout(1000)
            
            self.sbi_aggregate_click()
            
            self.wait_for_page_to_load()
            self.page.wait_for_load_state("domcontentloaded")
            self.wait_for_timeout(1000)    
        
            self.update_status("success", "GRN_SUCCESS", "Payment link initialized successfully", step="AP_TREASURY_PAGE")
        except Exception as e:
            self.update_status("failed", "GRN_FAILED", "Payment link initialization failed", step="AP_TREASURY_PAGE")
            raise e
    


