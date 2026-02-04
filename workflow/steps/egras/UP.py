import re
from workflow.steps.core.common import BasePage
from playwright.sync_api import Page

class UPRajKoshLandingPage(BasePage):
    btn_next = "#btnProceed"
    
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)

    def proceed_next(self):
        btn = self.page.locator(self.btn_next)
        btn.wait_for(state="visible", timeout=10000)
        btn.click(timeout=10000)
        #btn.wait_for(state="detached", timeout=15000)
        #self.wait_for_page_to_load()
        print(f"{self.__class__.__name__} completed....")
    
    def proceed(self):
        try:
            self.proceed_next()
            self.update_status("success", "RAJKOSH_LANDING_SUCCESS", "GRN generated successfully", step="RAJKOSH_UP_LANDING_PAGE")
        except Exception as e:
            self.update_status("failed", "RAJKOSH_LANDING_FAILED", "GRN generation failed", step="RAJKOSH_UP_LANDING_PAGE")
            raise e
        
        
class UPRajKoshPage(BasePage):
    
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
        
    def close_model_popup(self):
        try:
            # self.page.locator('#modelPopup').click()
            self.page.evaluate("hide('popDiv')")
            self.wait_for_timeout(1000)
        except Exception as e:
            print("Model popup not found", e)
        
    def click_proceed(self):
        try:
            btn = self.page.get_by_text(re.compile("Proceed With Net", re.IGNORECASE))
            if btn.is_visible():
                self.human_click_by_element(btn)
                return
        except:
            print("Proceed with button not found 1")
            pass
        
        try:
            btn = self.page.locator("input[type='submit']").first
            if btn.is_visible():
                btn.click(timeout=5000)
                return
        except:
            print("Proceed button not found 2")
            pass
        
        for frame in self.page.frames:
            try:
                btn = frame.locator("button:has-text('Proceed')")
                if btn.is_visible():
                    self.human_click_by_element(btn)
                    return
            except:
                print("Proceed button not found 3")
                pass
        
        raise Exception("Proceed button not found")
    
    def proceed(self):
        
        try:    
            #self.close_all_popup_windows()
            #print("closed all popup windows....")
            self.wait_for_element_to_be_visible("#popDiv")
            print("popDiv visible....")
            self.wait_for_timeout(1000)
            print("closing model popup....")
            self.close_model_popup()
            print("closed model popup....")
            self.wait_for_timeout(1000)
            self.click_proceed()
            self.update_status("success", "GRN_SUCCESS", "GRN generated successfully", step="RAJKOSH_UP_PAGE")
        except Exception as e:
            self.update_status("failed", "GRN_FAILED", "GRN generation failed", step="RAJKOSH_UP_PAGE")
            raise e
                

