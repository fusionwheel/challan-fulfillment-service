from workflow.steps.core.common import BasePage
from playwright.sync_api import Page

class EgrassGrnPage(BasePage):
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
    
    def is_popup_open(self):
        self.page.wait_for_selector('#popup', timeout=30000)
        return self.page.locator('#popup').is_visible()
    
    def close_popup(self):
        self.page.locator('#popup').click()
        self.wait_for_timeout(1000)
    
    def click_continue(self):
        self.page.locator('#continue').click()
        self.wait_for_timeout(1000)
    
    def proceed(self):
        if self.is_popup_open():
            self.close_popup()
        self.wait_for_timeout(1000)
        self.wait_for_element_to_be_visible('#continue')
        self.click_continue()

