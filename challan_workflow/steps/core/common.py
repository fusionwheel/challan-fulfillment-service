from re import L
import re
from playwright.sync_api import Page
from challan_workflow import config
import random

class BasePage:
    def __init__(self, page: Page, **kwargs):
        self.page = page
        self._ctx = kwargs.get("ctx")
    
    def update_status(self, status, state, message, step):
        self._ctx.status = status
        self._ctx.state = state
        self._ctx.message = message
        self._ctx.step = step
        
    def human_click_by_element(self, element):
        element.scroll_into_view_if_needed()
        # Get the bounding box (x, y, width, height)
        box = element.bounding_box()
        if box:
            # Calculate the center of the element
            center_x = box['x'] + box['width'] / 2
            center_y = box['y'] + box['height'] / 2
            
            # Move mouse to the element smoothly
            self.page.mouse.move(center_x, center_y, steps=10)
            # Perform the click
            self.page.mouse.click(center_x, center_y)
            print("click by mouse")
        else:
            # Fallback if bounding box isn't found
            element.click()
            print("click by script")
            
    def human_click(self, selector: str):
        element = self.page.locator(selector)
        element.scroll_into_view_if_needed()
        # Get the bounding box (x, y, width, height)
        box = element.bounding_box()
        if box:
            # Calculate the center of the element
            center_x = box['x'] + box['width'] / 2
            center_y = box['y'] + box['height'] / 2
            
            # Move mouse to the element smoothly
            self.page.mouse.move(center_x, center_y, steps=10)
            # Perform the click
            self.page.mouse.click(center_x, center_y)
            print("click by mouse", selector)
        else:
            # Fallback if bounding box isn't found
            element.click()
            print("click by script", selector)
            
    def wait_for_page_to_load(self):
        self.page.wait_for_load_state("load")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2000)
    
    def simulate_mouse_move(self):
        random_x = random.randint(0, 100)
        random_y = random.randint(0, 100)
        self.page.mouse.move(random_x, random_y)
    
    def scroll_to_bottom(self):
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    
    def scroll_to_top(self):
        self.page.evaluate("window.scrollTo(0, 0)")
    
    def select_option_element_by_text(self, q: str, text: str ):
        select_locator =  self.page.locator(q)
        select_locator.wait_for(state="visible", timeout=5000)
        #print("select_locator", select_locator)
        #for each in select_locator.locator("option").all():
        #    print("each.get_attribute(value) =>", each.get_attribute("value"))
        #    print("each.text_content() =>", each.text_content())
        option = select_locator.locator("option", has_text=text).first
        value = option.get_attribute("value")
        select_locator.select_option(value)
        
    def dispose(self):
        if self.page:
            self.page.close()
            self.page = None
    
    def wait_for_element_to_be_visible(self, q: str):
        self.page.wait_for_selector(q)
    
    def wait_for_timeout(self, timeout: int):
        self.page.wait_for_timeout(timeout)
 
class GoTOeChallanPage(BasePage):
    
    def proceed(self):
        try:
            print("Navigating to challan page...")
            self.page.set_default_timeout(10000)
            self.page.set_default_navigation_timeout(10000)
            
            self.page.goto("https://echallan.parivahan.gov.in", wait_until="domcontentloaded")
            self.page.wait_for_timeout(1000)
            self.update_status("success", "CHALLAN_PAGE_LOADED", "Challan page loaded successfully", "CHALLAN_PAGE")
        except Exception as e:
            self.update_status("failed", "CHALLAN_PAGE_FAILED", "Challan page loading failed", "CHALLAN_PAGE")
            raise e
        
    
    
        
class InitiatePaymentLink(BasePage):
    
    def __init__(self, page: Page, url, method, payload, **kwargs):
        super().__init__(page, **kwargs)
        self.url = getattr(self._ctx, "url", None) or url
        self.method = getattr(self._ctx, "method", None) or method
        self.data = getattr(self._ctx, "payload", None) or payload
    
    def initialize_page(self, url, method, data):
        self.wait_for_page_to_load()
        self.page.wait_for_timeout(1000)
        
        self.page.goto(url, wait_until="domcontentloaded")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_load_state("load")
        self.page.wait_for_timeout(1000)
        print(f"initiate payment link {url} {method}")
        
        try:
            if method == "POST":
                self.page.wait_for_selector('.payment-details', timeout=10000)
            else:
                if "rajkosh" not in url:
                    self.page.wait_for_selector('.container-fluid', timeout=10000)        
        except:
            pass
        
        self.page.evaluate(
            """
            ({ url, method, data }) => {
                const payload = data || {};

                if (method === 'GET') {
                    const params = new URLSearchParams();

                    Object.entries(payload).forEach(([key, value]) => {
                        if (value !== undefined && value !== null) {
                            params.append(
                                key,
                                typeof value === 'object'
                                    ? JSON.stringify(value)
                                    : String(value)
                            );
                        }
                    });
                    const finalUrl = params.toString()
                        ? `${url}?${params.toString()}`
                        : url;

                    window.location.href = finalUrl;
                    return;
                }

                // POST flow
                const container = document.querySelector('.payment-details');
                if (!container) return;
                container.innerHTML = '';
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = url;

                Object.entries(payload).forEach(([key, value]) => {
                    if (value !== undefined && value !== null) {
                        const input = document.createElement('input');
                        input.type = 'hidden';
                        input.name = key;
                        input.value =
                            typeof value === 'object'
                                ? JSON.stringify(value)
                                : String(value);

                        form.appendChild(input);
                    }
                });

                container.appendChild(form);
                form.submit();
            }
            """,
            {
                "url": url,
                "method": method,
                "data": data
            }
        )
        self.page.wait_for_timeout(1000)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_load_state("load")
        self.page.wait_for_timeout(1000)
    
    def proceed(self):
        try:
            self.initialize_page(self.url, method=self.method, data=self.data)
            self.wait_for_timeout(2000)
            # if transaction failed
            if "save-pgi-response" in self.page.url:
                print("Payment failed or terminate")
                self.update_status("failed", "PAYMENT_LINK_FAILED", "Payment failed or terminate", step="PAYMENT_INITIATED_PAGE")
                return
            else:
                self.update_status("success", "PAYMENT_LINK_INITIATED", "Payment link page initialized successfully", step="PAYMENT_INITIATED_PAGE")
            return self.page.url
        except Exception as e:
            self.update_status("failed", "PAYMENT_LINK_FAILED", "Payment link page initialization failed", step="PAYMENT_INITIATED_PAGE")
            raise e

class InitiatePending2FailedPaymentLink(BasePage):
    
    def __init__(self, page: Page, url, method, payload, **kwargs):
        super().__init__(page, **kwargs)
        self.url = url
        self.method = method
        self.data = payload
    
    def initialize_page(self, url, method, data):
        self.wait_for_page_to_load()
        self.page.wait_for_timeout(1000)
        
        self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        self.page.wait_for_load_state("networkidle", timeout=10000)
        self.page.wait_for_load_state("load", timeout=10000)
        self.page.wait_for_timeout(1000)
        print(f"initiate payment link {url} {method}")
        
        try:
            if method == "POST":
                self.page.wait_for_selector('.payment-details', timeout=10000)
            else:
                if "rajkosh" not in url:
                    self.page.wait_for_selector('.container-fluid', timeout=10000)        
        except:
            pass
        
        self.page.evaluate(
            """
            ({ url, method, data }) => {
                const payload = data || {};

                if (method === 'GET') {
                    const params = new URLSearchParams();

                    Object.entries(payload).forEach(([key, value]) => {
                        if (value !== undefined && value !== null) {
                            params.append(
                                key,
                                typeof value === 'object'
                                    ? JSON.stringify(value)
                                    : String(value)
                            );
                        }
                    });
                    const finalUrl = params.toString()
                        ? `${url}?${params.toString()}`
                        : url;

                    window.location.href = finalUrl;
                    return;
                }

                // POST flow
                const container = document.querySelector('.payment-details');
                if (!container) return;
                container.innerHTML = '';
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = url;

                Object.entries(payload).forEach(([key, value]) => {
                    if (value !== undefined && value !== null) {
                        const input = document.createElement('input');
                        input.type = 'hidden';
                        input.name = key;
                        input.value =
                            typeof value === 'object'
                                ? JSON.stringify(value)
                                : String(value);

                        form.appendChild(input);
                    }
                });

                container.appendChild(form);
                form.submit();
            }
            """,
            {
                "url": url,
                "method": method,
                "data": data
            }
        )
        self.page.wait_for_timeout(1000)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_load_state("load")
        self.page.wait_for_timeout(1000)
        
    def proceed(self):
        try:
            self.initialize_page(self.url, method=self.method, data=self.data)
            self.wait_for_timeout(2000)
            # if transaction failed
            #if "save-pgi-response" in self.page.url:
            print("Payment successfully terminated", self.page.url)
            return self.page.url
        except Exception as e:
            raise e


class VahanMORTHGatewayPage(BasePage):
    gateway = "SBI"
    
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
    
    def get_gateway_name(self):
        return config.GATEWAY_NAMES.get(self._ctx.st_cd) or self.gateway
    
    def select_payment_gateway(self):
        print(f"Searching for gateway dropdown...")
        dropdown = self.page.locator(".ui-selectonemenu").filter(
            has=self.page.locator("xpath=ancestor::div[contains(@class, 'row')]//span[contains(text(), 'Select Payment Gateway')]")
        ).first
        self.human_click_by_element(dropdown)
        
        option = self.page.locator(".ui-selectonemenu-item").filter(has_text=self.get_gateway_name()).first
        option.wait_for(state="visible")
        option.click()
    
    def check_tnc(self):
        tnc_container = self.page.locator(".ui-chkbox").filter(has_text="I accept terms and conditions").first
        checkbox_box = tnc_container.locator(".ui-chkbox-box")
        self.human_click_by_element(checkbox_box)
        self.page.wait_for_load_state("networkidle")
    
    def click_submit(self):
        btn_submit = self.page.get_by_role("button", name="Continue")
        btn_submit.wait_for(state="visible")
        self.human_click_by_element(btn_submit)
        btn_submit.wait_for(state="detached", timeout=10000)
    
    def proceed(self):
        try:
            self.select_payment_gateway()
            self.wait_for_timeout(1000)
            self.check_tnc()
            self.wait_for_timeout(1000)
            self.click_submit()
            self.page.wait_for_load_state("load", timeout=10000)
            self.page.wait_for_load_state("networkidle")
            self.wait_for_timeout(1000)
            self.update_status("success", "GATEWAY_TNC_CHECK_SUCCESS", "MORTH gateway page loaded successfully", step="MORTH_PAYMENT_PAGE")
            return self.next_page()
        except Exception as e:
            #self.page.pause()
            self.update_status("failed", "GATEWAY_TNC_CHECK_FAILED", "MORTH gateway page loading failed", step="MORTH_PAYMENT_PAGE")
            raise e

    def next_page(self):
        
        # self.page.wait_for_function("""
        #     () => {
        #     return (
        #         document.querySelector('a[onclick*="OTHERINB"]') ||
        #         document.querySelector('a[href*="icici"]') ||
        #         location.href.includes('EgEChallan') ||
        #         location.href.includes('etranspaymetws')
        #     );
        #     }
        #     """, timeout=10000)
        
        
        return self.page.url
        
class SBIAggregatePage(BasePage):
    gateway = "SBI"
    
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
    
    def get_gateway_name(self):
        return config.GATEWAY_NAMES.get(self._ctx.st_cd) or self.gateway
    
    
    def select_payment_gateway_fallback(self):
        print("Falling back to default gateway")
        dropdown = self.page.locator("#dropOperator")
        dropdown.wait_for(state="visible")
        dropdown.select_option(label=self.get_gateway_name())
    
    def select_payment_gateway(self):
        try:
            print("Selecting payment gateway", self.get_gateway_name())
            self.select_option_element_by_text('#dropOperator', self.get_gateway_name())
        except Exception as e:
            print("Selecting payment gateway failed", e)
            self.select_payment_gateway_fallback()
    
    def check_tnc(self):
        self.page.locator('#checkme').click()
        #self.human_click('#checkme')
    
    def click_submit(self):
        #self.human_click('#sendSubmit')
        self.page.locator('#sendSubmit').click()
    
    def proceed(self):
        try:
            self.select_payment_gateway()
            self.wait_for_timeout(1000)
            self.check_tnc()
            self.wait_for_timeout(1000)
            self.wait_for_element_to_be_visible('#sendSubmit')
            self.click_submit()
            self.page.wait_for_load_state("load", timeout=20000)
            self.page.wait_for_load_state("networkidle")
            self.wait_for_timeout(1000)
            self.update_status("success", "GATEWAY_TNC_CHECK_SUCCESS", "Gateway tnc checked successfully", step="SBI_AGGREGATE_PAGE")
            return self.next_page()
        except Exception as e:
            self.update_status("failed", "GATEWAY_TNC_CHECK_FAILED", "Gateway tnc check failed", step="SBI_AGGREGATE_PAGE")
            raise e

    def next_page(self):
        self.page.wait_for_load_state("load", timeout=20000)
        self.page.wait_for_load_state("networkidle")
        self.wait_for_timeout(1000)
        return self.page.url

class WhichNetBankingProviderSBIAggregatePage(BasePage):
    provider = "OTHERINB"
    
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
        self.provider = kwargs.get("provider", self.provider)

    def select_other_netbanking(self):
        if self.provider == "OTHERINB":
            self.page.wait_for_function("typeof paySubmit === 'function'")
            with self.page.expect_navigation(wait_until="domcontentloaded"):
                self.page.evaluate("paySubmit('OTHERINB')")
            self.wait_for_timeout(1000)
        else:
            raise Exception("Invalid Netbanking Provider")
        
    
    def proceed(self):
        try:
            self.wait_for_timeout(1000)
            self.select_other_netbanking()   
            self.scroll_to_bottom()
            self.scroll_to_top()
            self.simulate_mouse_move()
            self.wait_for_page_to_load()
            self.wait_for_timeout(1000)
            self.update_status("success", "NETBANKING_SELECTION_SUCCESS", "other netbanking selected successfully", step="NETBANKING_PROVIDER_PAGE")
            #return self.next_page()
        except Exception as e:
            self.update_status("failed", "NETBANKING_SELECTION_FAILED", "other netbanking selection failed", step="NETBANKING_PROVIDER_PAGE")
            raise e

class IciciCorpOrRetailSBIAggregatePage(BasePage):
    bank_label = "ICICI Bank Corporate"
    
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
        self.bank_label = kwargs.get("bank_label", self.bank_label)
    
    def select_corporate(self):
        selector = f'input[title*="{self.bank_label}"]'
        
        try:
            # 1. Attempt the UI interaction
            btn_corporate = self.page.locator(selector).first
            btn_corporate.wait_for(state="attached", timeout=5000)
            btn_corporate.scroll_into_view_if_needed()
            
            # Using .check() is safer for radio buttons
            btn_corporate.check(timeout=3000, force=True)
            print("Successfully clicked the radio button.")
            return True
            
        except Exception as e:
            print(f"UI interaction failed: {e}. Trying JS Event Fallback...")
            # 2. JS Fallback: Trigger the site's internal function directly
            #self.page.evaluate("redirectToCorporateBanking()")
            self.page.evaluate(f'document.querySelector("{selector}").click()')
            print("Successfully triggered redirectToCorporateBanking() via JS.")
            return True
        
    def proceed(self):
        try:
            self.wait_for_page_to_load()
            self.page.wait_for_load_state("domcontentloaded")
            self.simulate_mouse_move()
            self.select_corporate()
            self.wait_for_page_to_load()
            self.update_status("success", "ICICI_CORP_OR_RETAIL_SUCCESS", "ICICI bank selected successfully", step="ICICI_CORP_OR_RETAIL_PAGE")
        except Exception as e:
            self.update_status("failed", "ICICI_CORP_OR_RETAIL_FAILED", "ICICI bank selection failed", step="ICICI_CORP_OR_RETAIL_PAGE")
            raise e