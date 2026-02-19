import re
from challan_workflow.steps.core.common import BasePage
from playwright.sync_api import Page


class KLETreasuryGrnPage(BasePage):
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
        
    def click_proceed(self):
        btn = self.page.get_by_role("button", name=re.compile("Proceed to pay", re.IGNORECASE)).first
        btn.wait_for(state="visible", timeout=2000)
        btn.scroll_into_view_if_needed()
        btn.click(timeout=5000)
        self.wait_for_page_to_load()
    
    def select_gateway_preferred(self):
        self.wait_for_page_to_load()
        #btn = self.page.get_by_role("listitem", name=re.compile("Payment Gateway (Preferred)", re.IGNORECASE))
        btn = self.page.get_by_text("Payment Gateway (Preferred)").first
        btn.wait_for(state="visible", timeout=2000)
        btn.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.wait_for_page_to_load()
        

    def proceed(self):
        try:
            self.wait_for_timeout(1000)
            self.select_gateway_preferred()
            print("selected gateway preferred....")
            self.click_proceed()
            print("clicked proceed button....")
            self.close_all_popup_windows()
            print("closed all popup windows....")
            self.wait_for_timeout(1000)
            
            self.close_model_popup()
            print("closed model popup....")
            self.wait_for_timeout(1000)
            self.wait_for_page_to_load()
            self.page.wait_for_load_state("domcontentloaded")
            self.wait_for_timeout(1000)
            
            self.update_status("success", "GRN_SUCCESS", "Payment link initialized successfully", step="KL_TREASURY_PAGE")
        except Exception as e:
            self.update_status("failed", "GRN_FAILED", "Payment link initialization failed", step="KL_TREASURY_PAGE")
            raise e
    


