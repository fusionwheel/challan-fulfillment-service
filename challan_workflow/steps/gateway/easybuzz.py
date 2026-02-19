from playwright.sync_api import Page
from challan_workflow.steps.core.common import BasePage
import re


class EasyBuzzSDKPaymentPage(BasePage):
    bank_name = "ICICI"
    is_corporate = True
    
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)

    def select_net_banking_tab(self):
        nb_tab = self.page.get_by_text("NetBanking", exact=True)
        nb_tab.wait_for(state="visible")
        nb_tab.click()
        

    def select_bank_by_name(self):
        """
        Logic: Try to click a popular bank icon first. 
        If not found, use the 'Select Bank' dropdown or search input.
        """ 
        bank_display_name = (
            f"{self.bank_name} Corporate"
            if self.is_corporate
            else f"{self.bank_name} Bank"
        )
        
        search_input = self.page.get_by_role("textbox", name="Search by Bank Name", exact=False)
        search_input.wait_for(state="visible", timeout=10000)
        search_input.fill(self.bank_name) # Type the name to filter the list
        
        bank_option =  self.page.get_by_text(bank_display_name, exact=True).first
        bank_option.wait_for(state="attached", timeout=10000)
        bank_option.scroll_into_view_if_needed()
        try:
            self.human_click_by_element(bank_option)
        except Exception as e:
            print("Exception in select_bank_by_name", e)
            bank_option.click()
            
        print(f"Selected: {bank_display_name}")
    
    def click_pay_button(self):
        pay_button = self.page.get_by_test_id("pay-button")
        pay_button.wait_for(state="visible", timeout=3000)
        pay_button.click()
            
        pay_button.wait_for(state="detached", timeout=15000)
        print("EasyBuzz detached. Waiting for ICICI login page...")
    
    
    def proceed(self):
        """Main flow for EasyBuzz SDK interaction"""
        try:
            # 1. Wait for SDK to initialize
            self.wait_for_page_to_load()
            self.select_net_banking_tab()
            self.wait_for_timeout(1000) 
            
            self.select_bank_by_name()
            self.wait_for_timeout(1000) 
            self.click_pay_button()
            
            self.update_status("success", "EASYBUZZ_SUCCESS", "netbanking selected successfully", step="EASYBUZZ_PAGE")
            
            return self.page.url
        except Exception as e:
            self.update_status("failed", "EASYBUZZ_FAILED", "netbanking selection failed", step="EASYBUZZ_PAGE")
            #raise e
