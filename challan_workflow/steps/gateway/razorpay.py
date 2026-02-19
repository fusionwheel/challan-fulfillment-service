"""
# Continue button

# Netbanking
# All indian banks
locator("iframe").content_frame.get_by_role("listitem").filter(has_text="Netbanking All Indian banks")


# select bank
locator("iframe").content_frame.get_by_role("button", name="Select a different bank")
`
# search bank
locator("iframe").content_frame.get_by_role("combobox", name="Search for bank")
#icici bank - corporate Banking
locator("iframe").content_frame.get_by_text("ICICI Bank - Corporate Banking")

# pay now
locator("iframe").content_frame.get_by_role("button", name="Pay Now")

# Continue And Pay
locator("iframe").content_frame.get_by_text("Continue and pay")
"""

from playwright.sync_api import Page
from challan_workflow.steps.core.common import BasePage
import re


class RazorpayPmtPreviewPage(BasePage):
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
    
    def click_continue(self):    
        btn = self.page.get_by_role("button", name=re.compile(r"^Continue", re.IGNORECASE))
        if btn.is_visible(timeout=5000):
            btn.click(force=True)
            print(f"  {self.__class__.__name__} | Clicked continue")
            # Wait for the next page or the Razorpay iframe to appear
            self.page.wait_for_load_state("load")
        else:
            print(f"  {self.__class__.__name__} | Continue button not found, skipping...")
            
    
    def proceed(self):
        try:
            print(f" {self.__class__.__name__} | waiting for page to load....")
            self.page.wait_for_load_state("load", timeout=10000)
            self.page.wait_for_load_state("domcontentloaded", timeout=10000)
            
            self.click_continue()
            print(f" {self.__class__.__name__} | clicked continue button....")
            self.update_status("success", "RAZORPAY_PMT_PREVIEW_SUCCESS", "Payment link initialized successfully", step="RAZORPAY_PAGE")
        except Exception as e:
            print(f" {self.__class__.__name__} | failed to click continue button | {e}")
            #self.page.pause()
            #self.update_status("failed", "RAZORPAY_PMT_PREVIEW_FAILED", "Payment link initialization failed", step="RAZORPAY_PAGE")
            #raise e


class RazorpayPaymentPage(BasePage):
    bank_name = "ICICI Bank"
    is_corporate = True
    
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
        # Razorpay's iframe selector is usually 'iframe.razorpay-checkout-frame'
        self.iframe_selector = 'iframe.razorpay-checkout-frame'
        try:
            # Context is locked to the Razorpay iframe
            self.frame = self.page.frame_locator(self.iframe_selector)
            self.iframe_handle = self.page.locator(self.iframe_selector)
        except Exception as e:
            print(f"  {self.__class__.__name__} Exception initializing RazorpayPaymentPage: {e}")

    def human_click_in_frame(self, element_locator):
        """Calculates absolute coordinates to bypass simple bot detection."""
        element_locator.wait_for(state="visible", timeout=8000)
        
        iframe_handle = self.page.locator(self.iframe_selector)
        iframe_box = iframe_handle.bounding_box()
        element_box = element_locator.bounding_box()

        if iframe_box and element_box:
            abs_x = iframe_box['x'] + element_box['x'] + (element_box['width'] / 2)
            abs_y = iframe_box['y'] + element_box['y'] + (element_box['height'] / 2)
            self.page.mouse.move(abs_x, abs_y, steps=10)
            self.page.mouse.click(abs_x, abs_y)
        else:
            element_locator.click(force=True)

    def get_razorpay_version(self):
        """
        Identifies the Razorpay version immediately upon iframe load.
        """
        
        return "v1"
        
        # Wait for the iframe body to exist
        body = self.frame.locator("body")
        body.wait_for(state="attached", timeout=10000)

        # Condition 1: Check for Catalyst (New V2 Entry Point)
        if self.frame.locator("#Catalyst").is_visible(timeout=1000):
            return "v2"

        # Condition 2: Check for Tailwind-specific classes from your snippet
        # V2 uses 'antialiased' and specific overflow rules on the body
        class_attribute = body.get_attribute("class") or ""
        if "antialiased" in class_attribute:
            return "v2"

        # Condition 3: Check for data-testids on the main screen
        # V2 usually exposes test-ids for the payment list
        if self.frame.get_by_test_id("payment-method-netbanking").is_visible(timeout=1000):
            return "v2"

        # Fallback: If none of the above are found, it's likely the legacy V1
        return "v2"

    def detect_version(self):
        """Determines if the checkout is the new v2 or legacy v1."""
        print("  Detecting Razorpay version...")
        # V2 often has the specific 'fee-bearer-cta' or Tailwind-like classes
        # V1 uses more standard role-based structures
        self.version = self.get_razorpay_version()
        
        print(f"  Detected Version: {self.version}")
        
        
    def select_netbanking_option(self):
        """Selects the 'Netbanking' list item from the main payment method list."""
        
        if self.version == "v1":
            self.frame.get_by_text(re.compile(r"^Netbanking", re.IGNORECASE)).first.click()
            return
            
        else:
            for text in ["Netbanking All Indian banks", "Netbanking"]:
                #nb_option = self.frame.get_by_role("listitem").filter(has_text=text)
                try:
                    nb_option = self.frame.get_by_text(re.compile(r"^Netbanking", re.IGNORECASE)).first#.filter(has_text=text)
                    if nb_option.is_visible(timeout=5000):
                        self.human_click_in_frame(nb_option)
                        return
                except Exception as e:
                    print(f"✗ Error selecting netbanking option: {e}")
                    continue
                
                
        raise Exception("Netbanking option not found")
    
    def search_and_select_bank(self):
        """Handles the bank selection dropdown and search input."""
        if self.version == "v1":
            search_box = self.frame.get_by_placeholder(re.compile(r"Search", re.I))
            if not search_box.is_visible(timeout=5000):
                self.frame.get_by_text("Select a different bank").click()
            search_box.fill(self.bank_name)
        
        else:
            # 1. Click 'Select a different bank' if the desired bank isn't in popular list
            select_diff_btn = self.frame.get_by_role("button", name="Select a different bank")
            select_diff_btn.wait_for(state="visible", timeout=5000)
            select_diff_btn.scroll_into_view_if_needed()
            if select_diff_btn.is_visible(timeout=3000):
                self.human_click_in_frame(select_diff_btn)

            # 2. Type into the search box
            search_box = self.frame.get_by_role("combobox", name="Search for bank")
            search_box.wait_for(state="visible", timeout=5000)
            search_box.scroll_into_view_if_needed()
            search_box.fill(self.bank_name)

            # 3. Select the specific corporate or retail branch
            target_text = f"{self.bank_name} - Corporate Banking" if self.is_corporate else self.bank_name
            print(f"  {self.__class__.__name__} | Target Bank: {target_text}")
            bank_entry = self.frame.get_by_text(target_text, exact=False)
            self.human_click_in_frame(bank_entry)

    def payment_initiation(self):
        """Handles the final 'Pay Now' and 'Continue and pay' sequence."""
        
        if self.version == "v1":
            btn = self.frame.get_by_test_id("fee-bearer-cta")
            if btn.is_visible(timeout=5000):
                btn.click()
        
        else:
            pay_now_btn = self.frame.get_by_role("button", name="Pay Now")
            pay_now_btn.wait_for(state="visible", timeout=5000)
            self.human_click_in_frame(pay_now_btn)
            print(f"  {self.__class__.__name__} | Clicked Pay Now")
            
            self.handle_fees_and_pay()

    
    def handle_fees_and_pay(self):
        print("  Handling Fees Breakup overlay...")
        # 1. Target the Razorpay iframe
        checkout_frame = self.page.frame_locator(self.iframe_selector)
        # 2. Target the 'Continue and pay' DIV specifically
        continue_btn = checkout_frame.locator("div.btn", has_text=re.compile(r"\bcontinue\s+and\s+pay\b", re.I)).first
        try:
            continue_btn.wait_for(state="visible", timeout=10000)
            self.human_click_in_frame(continue_btn)
            print(f"  {self.__class__.__name__} | Continue and pay clicked | redirected triggered")
            
        except Exception as e:
            print(f"  Overlay button not found or already dismissed. Error: {e}")

    def proceed(self):
        """Main flow for Razorpay SDK interaction"""
        try:
            self.wait_for_page_to_load()
            
            # 1. Detect which UI we are dealing with
            self.detect_version()
            
            # Step 1: Navigate to Netbanking
            self.select_netbanking_option()
            print(f"  {self.__class__.__name__} | Netbanking selected")
            # Step 2: Search and pick bank
            self.search_and_select_bank()
            print(f"  {self.__class__.__name__} |Bank searched and selected")
            # Step 3: Trigger payment redirection
            self.payment_initiation()
            print(f"  {self.__class__.__name__} | Payment button triggered")
            
            self.page.wait_for_load_state("networkidle", timeout=15000)
            
            #self.wait_for_page_to_load()
            #self.page.wait_for_function("() => !window.location.href.includes('razorpay')", timeout=10000)
            
            print(f"  {self.__class__.__name__} | Payment redirection URL: {self.page.url}")
            
            self.update_status("success", "RAZORPAY_SUCCESS", "Bank selected successfully", step="RAZORPAY_PAGE")
            self.page.pause()
            return self.page.url
        except Exception as e:
            self.page.pause()
            self.update_status("failed", "RAZORPAY_NAV_FAILED", "Bank selection failed | " + str(e), step="RAZORPAY_PAGE")
            raise e