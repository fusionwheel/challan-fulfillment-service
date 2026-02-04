from workflow.steps.core.common import BasePage
from playwright.sync_api import Page

class EgrassGrnPage(BasePage):
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
            if btn.is_visible():
                btn.click(timeout=5000)
                return
        except:
            print("Continue button not found 0")
            pass
        try:
            btn = self.page.locator("button:has-text('Continue')").first
            if btn.is_visible():
                btn.click(timeout=5000)
                return
        except:
            print("Continue button not found 1")
            pass
        
        try:
            btn = self.page.locator("input[type='submit'][value='Continue']")
            if btn.is_visible():
                btn.click(timeout=5000)
                return
        except:
            print("Continue button not found 2")
            pass
        
        for frame in self.page.frames:
            try:
                btn = frame.locator("button:has-text('Continue')")
                if btn.is_visible():
                    btn.click(timeout=3000)
                    return
            except:
                print("Continue button not found 3")
                pass
        
        raise Exception("Continue button not found")
    
    def select_netbanking(self):
        self.wait_for_page_to_load()
        self.page.click("li#paymentgateway")
        self.wait_for_page_to_load()
        self.wait_for_timeout(2000)
        
        # 2. Select ICICI Bank using the visible text
        self.page.select_option("select#ddlbank", label="HDFC")
        
        # 3. Click the Proceed button
        self.page.click("input#btnSubmit")
        self.wait_for_timeout(1000)
        self.wait_for_page_to_load()
        
    
    def proceed(self):
        try:
            self.close_all_popup_windows()
            print("closed all popup windows....")
            self.wait_for_timeout(3000)
            self.close_model_popup()
            print("closed model popup....")
            self.wait_for_timeout(3000)
        
            self.wait_for_element_to_be_visible('#txtGo')
            print("contine button visible....")
            self.click_continue()
            print("clicked continue button....")
            self.select_netbanking()
            print("selected netbanking....")
            self.update_status("success", "GRN_SUCCESS", "Payment link initialized successfully", step="EGRAS_RJ_PAGE")
        except Exception as e:
            self.update_status("failed", "GRN_FAILED", "Payment link initialization failed", step="EGRAS_RJ_PAGE")
            raise e
    


