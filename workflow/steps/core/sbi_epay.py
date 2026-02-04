from os import name
from socket import timeout
from playwright.sync_api import Page
from workflow.steps.core.common import BasePage
import re


class SBIePayPaymentPage(BasePage):
    bank_name = "ICICI Bank"
    is_corporate = True
    
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
        # Context is locked to the iframe for all operations in this class
            
    def select_net_banking_tab(self):
        # The tab text is usually "Net Banking"
        try:
            #nb_tab = self.page.locator("#activeNB > a").filter(has_text="Net Banking").first
            #nb_tab = self.page.get_by_text("Net Banking", exact=False)
            #nb_tab = nb_tab or self.page.get_by_role("listitem", id="activeNB", exact=True)
            nb_tab = self.page.locator("#activeNB > a").first
            nb_tab.wait_for(state="visible", timeout=10000)
            nb_tab.scroll_into_view_if_needed()
            self.human_click_by_element(nb_tab)
            
            # wait for accordion content to open
            self.page.locator("#collapseib").wait_for(state="visible", timeout=10000)
        except Exception as e:
            print("Exception in select_net_banking_tab", e)

    def select_pay_by_net_banking(self):
        # The tab text is usually "Net Banking"
        try:
            #radio = self.page.get_by_role("radio", name="nbblRadioOption", exact=True)
            radio = self.page.locator("#nbbl_NetBanking").first
            radio.wait_for(state="visible")
            self.human_click_by_element(radio)
        except Exception as e:
            print("Exception in select_pay_by_net_banking", e)
            
    def select_bank_by_name(self):
        """
        Logic: Try to click a popular bank icon first. 
        If not found, use the 'Select Bank' dropdown or search input.
        """ 
        # select id and name both otherbanks
        bank_label = (
                f"{self.bank_name} - Corporate"
                if self.is_corporate
                else f"{self.bank_name} - Retail"
            )
        try:
            self.page.locator("#nbblNBContent").wait_for(state="visible", timeout=15000)
            select = self.page.locator("#otherbanks")
            select.wait_for(state="visible", timeout=10000)
            select.scroll_into_view_if_needed()
            select.select_option(label=bank_label)
            print(f"Selected: {bank_label}")
        except Exception as e:
            print("Exception in select_bank_by_name", e)
            #bank_option.click(force=True, delay=100)
    
    def submit_pay_now(self):
        try:
            #pay_now = self.page.get_by_text("Pay Now", exact=True)
            #pay_now = self.page.get_by_role("button", name="netbank", exact=True)
            pay_now = self.page.locator("#subButton")
            pay_now.wait_for(state="visible")
            pay_now.scroll_into_view_if_needed()
            self.human_click_by_element(pay_now)
            pay_now.wait_for(state="detached", timeout=15000)
            print("spi epay pay now detached. Waiting for ICICI login page...")
        except Exception as e:
            print("Exception in submit_pay_now", e)

    
    def proceed(self):
        """Main flow for SBI ePay interaction"""
        
        # 1. Wait for SDK to initialize
        self.wait_for_timeout(10000) 
        self.select_net_banking_tab()
        self.wait_for_timeout(1000)
        self.select_pay_by_net_banking()
        self.wait_for_timeout(1000)
        self.select_bank_by_name()
        self.wait_for_timeout(1000)
        self.submit_pay_now()
        #self.wait_for_timeout(1000)
        #self.page.screenshot(path="sbi_epay_proceed1.png")
        self.update_status("success", "INIT_SUCCESS", "Payment link initialized successfully", step="SBI_EPAY_PAGE")
        
        return self.page.url