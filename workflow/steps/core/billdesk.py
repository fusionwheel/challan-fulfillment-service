from playwright.sync_api import Page
from workflow.steps.core.common import BasePage
import re


class BillDeskSDKPaymentPage(BasePage):
    bank_name = "ICICI Bank"
    is_corporate = True
    
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
        # Context is locked to the iframe for all operations in this class
        try:
            self.frame = self.page.frame_locator('iframe[name="response-frame"]')
            self.iframe_handle = self.page.locator('iframe[name="response-frame"]')
            
        except Exception as e:
            print("Exception in BillDeskSDKPaymentPage", e)

    def human_click_in_frame(self, element_locator):
        # 1. Get the iframe's position on the main page
        iframe_box = self.iframe_handle.bounding_box()
        # 2. Get the element's position relative to the iframe
        element_box = element_locator.bounding_box()
        if iframe_box and element_box:
            # 3. Calculate absolute coordinates
            abs_x = iframe_box['x'] + element_box['x'] + (element_box['width'] / 2)
            abs_y = iframe_box['y'] + element_box['y'] + (element_box['height'] / 2)
            
            # 4. Move and click
            self.page.mouse.move(abs_x, abs_y, steps=10)
            self.page.mouse.click(abs_x, abs_y)
        else:
            # Fallback
            element_locator.click()
            
    def select_net_banking_tab(self):
        # The tab text is usually "Net Banking"
        #try:
        nb_tab = self.frame.get_by_text("Net Banking", exact=True)
        nb_tab.wait_for(state="visible")
        nb_tab.click()
        #except Exception as e:
        #    print("Exception in select_net_banking_tab", e)

    def select_bank_by_name(self):
        """
        Logic: Try to click a popular bank icon first. 
        If not found, use the 'Select Bank' dropdown or search input.
        """ 
        bank_display_name = self.bank_name + " [Corporate]" if self.is_corporate else " [Retail]"
        bank_option =  self.frame.get_by_text(bank_display_name, exact=False).first
        #try:
        bank_option.wait_for(state="attached", timeout=10000)
        bank_option.scroll_into_view_if_needed()
        self.human_click_in_frame(bank_option)
        print(f"Selected: {bank_display_name}")
        bank_option.wait_for(state="detached", timeout=15000)
        print("BillDesk detached. Waiting for ICICI login page...")
        # except Exception as e:
        #     print("Exception in select_bank_by_name", e)
        #     bank_option.click(force=True, delay=100)
    
    def proceed(self):
        """Main flow for BillDesk SDK interaction"""
        try:
            # 1. Wait for SDK to initialize
            self.wait_for_timeout(2000) 
            self.select_bank_by_name()
            
            self.update_status("success", "BILLDESK_SUCCESS", "netbanking selected successfully", step="BILLDESK_PAGE")
            
            return self.page.url
        except Exception as e:
            self.update_status("failed", "BILLDESK_FAILED", "netbanking selection failed", step="BILLDESK_PAGE")
            raise e