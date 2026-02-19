import re
from challan_workflow.steps.core.common import BasePage
from playwright.sync_api import Page

class RJGrnPage(BasePage):
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
    
    def close_all_popup_windows(self):
        for p in self.page.context.pages:
            if p != self.page and not p.is_closed():
                p.close()
    
    def close_model_popup(self):
        try:
            self.page.evaluate("""
                () => {
                    
                    // SweetAlert2
                    if (window.Swal && Swal.isVisible()) {
                        Swal.close();
                    }
                    
                    // Legacy SweetAlert
                    const legacy = document.querySelector('.swal-overlay');
                    if (legacy) {
                        legacy.remove();
                    }
                    
                    if (window.Swal && !Swal.__autoCloseInstalled) {
                        Swal.__autoCloseInstalled = true;

                        const originalFire = Swal.fire;
                        Swal.fire = function(...args) {
                            const p = originalFire.apply(this, args);
                            setTimeout(() => Swal.close(), 300);
                            return p;
                        };
                    }
                    
                    // Generic HTML modal buttons (OK / Close only)
                    const keywords = ['ok', 'close'];

                    const buttons = Array.from(
                        document.querySelectorAll('button, input[type="button"], input[type="submit"]')
                    ).filter(b =>
                        b.offsetParent !== null &&
                        keywords.includes(b.innerText.trim().toLowerCase())
                    );

                    if (buttons.length) {
                        buttons[0].click();
                    } 
                }
                """)
            # self.page.locator('#modelPopup').click()
            self.wait_for_timeout(1000)
        except Exception as e:
            print("Model popup not found", e)
        
    def click_continue(self):
        try:
            btn = self.page.locator("#txtGo").first
            btn.wait_for(state="visible", timeout=3000)
            btn.click(timeout=5000, force=True)
            return
        except:
            print("Continue button not found 1")
            pass
        
        try:
            btn = self.page.get_by_role("button", name="Submit")
            btn.wait_for(state="visible", timeout=3000)
            btn.click(timeout=5000, force=True)
            return
        except:
            print("Continue button not found 2")
            pass
        
        raise Exception("Continue button not found")
    
    def select_netbanking(self):
        self.wait_for_page_to_load()
        self.page.click("li#paymentgateway")
        self.wait_for_page_to_load()
        self.wait_for_timeout(2000)
        
        # 2. Select HDFC using the visible text
        self.page.select_option("select#ddlbank", label="HDFC")
    
    def click_proceed(self):
        
        #self.page.wait_for_selector("input:has-text('Continue')", state="visible", timeout=2000)
        btn = self.page.get_by_role("button", name=re.compile(r"^Proceed", re.IGNORECASE))
        btn.wait_for(state="visible", timeout=1000)
        btn.click(timeout=5000, force=True)
        btn.wait_for(state="detached", timeout=5000)
        self.wait_for_timeout(1000)
        self.wait_for_page_to_load()
    
    
    def proceed(self):
        try:
            #self.page.pause()
            #self.close_all_popup_windows()
            #print(f" {self.__class__.__name__} | closed all popup windows....")
            #self.wait_for_timeout(3000)
            #self.close_model_popup()
            #print(f" {self.__class__.__name__} | closed model popup....")
            #self.wait_for_timeout(3000)
        
            self.wait_for_element_to_be_visible('#txtGo')
            print(f" {self.__class__.__name__} | contine button visible....")
            self.click_continue()
            print(f" {self.__class__.__name__} | clicked continue button....")
            self.select_netbanking()
            print(f" {self.__class__.__name__} | selected netbanking....")
            self.click_proceed()
            print(f" {self.__class__.__name__} | clicked proceed button....")
            self.update_status("success", "GRN_SUCCESS", "Payment link initialized successfully", step="EGRAS_RJ_PAGE")
        except Exception as e:
            print(f" {self.__class__.__name__} | failed to proceed | {e}")
            self.page.pause()
            self.update_status("failed", "GRN_FAILED", "Payment link initialization failed", step="EGRAS_RJ_PAGE")
            raise e
    

class RJGrnConfirmPage(BasePage):
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
    
    def click_continue(self):
        btn = self.page.get_by_role("button", name=re.compile(r"^Continue", re.IGNORECASE))
        btn.wait_for(state="visible", timeout=1000)
        btn.click(timeout=5000, force=True)
        btn.wait_for(state="detached", timeout=5000)
        self.wait_for_timeout(1000)
        self.wait_for_page_to_load()
    
    def proceed(self):
        try:
            self.wait_for_page_to_load()
            self.click_continue()
            print(f" {self.__class__.__name__} | clicked continue button....")
            
            #self.page.wait_for_timeout(12000)
            #print(f" {self.__class__.__name__} | waited for 12 seconds....")
            
            self.update_status("success", "GRN_SUCCESS", "Payment link initialized successfully", step="EGRAS_RJ_PAGE")
        except Exception as e:
            print(f" {self.__class__.__name__} | failed to click continue button | {e}")
            self.page.pause()
            self.update_status("failed", "GRN_FAILED", "Payment link initialization failed", step="EGRAS_RJ_PAGE")
            raise e
