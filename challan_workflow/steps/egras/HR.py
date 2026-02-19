from challan_workflow.steps.core.common import BasePage
from playwright.sync_api import Page

class EgrassGrnPage(BasePage):
    def __init__(self, page: Page, **kwargs):
        super().__init__(page,  **kwargs)
    
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
            #btn = self.page.locator("input[type='submit'][value='Continue']").click(timeout=5000)
            btn = self.page.locator("input[type='submit'][value='Continue']")
            btn.wait_for(state="visible", timeout=7000)
            btn.click(timeout=5000, force=True)
            return
        except Exception as e:
            print(e)
            print("Continue button not found 1")
            pass
        
        raise Exception("Continue button not found")
    
    def proceed(self):
        try:
            self.close_all_popup_windows()
            print("closed all popup windows....")
            self.wait_for_timeout(3000)
            self.close_model_popup()
            print("closed model popup....")
            self.wait_for_timeout(2000)
            self.page.wait_for_selector('input[type="submit"][value="Continue"]', timeout=5000)
            print("contine button visible....")
            self.click_continue()
            print("clicked continue button....")
            self.update_status("success", "GRN_SUCCESS", "GRN generated successfully", step="EGRAS_HR_PAGE")
        except Exception as e:
            self.update_status("failed", "GRN_FAILED", "GRN generation failed", step="EGRAS_HR_PAGE")
            raise e
    
