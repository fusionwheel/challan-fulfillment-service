from hmac import new
from playwright.sync_api import Page
from challan_workflow.steps.core.common import BasePage

class DisablePopupAutoClosePageConfig(BasePage):
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
    
    def proceed(self):
        if hasattr(self._ctx, 'should_monitor'):
            self._ctx.should_monitor = False
            print("  Popup monitoring disabled via flag.")
        

class EnablePopupAutoClosePageConfig(BasePage):
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
    
    def enable_popup_auto_close(self):
        context = self.page.context
        main_page = self.page
        # Auto-close future popup windows
        self._ctx.should_monitor = True
        
        def handle_new_page(new_page):
            # Give the page a moment to load its URL
            print("handle_new_page triggered")
            
            if not getattr(self._ctx, 'should_monitor', False):
                return
            
            
            new_page.wait_for_load_state("load")
            new_page.wait_for_load_state("domcontentloaded")
            new_page.wait_for_timeout(1000)
            
            url = new_page.url
            print("handle_new_page triggered new page url =>", new_page.url)
            # Add your bank keywords here
            bank_keywords = ["billdesk", "icicibank", "icici", "razorpay", "hdfcbank", "sbi"]
            is_bank_page = any(key in url.lower() for key in bank_keywords)
            print("handle_new_page triggered is_bank_page =>", is_bank_page)
            if new_page != main_page and not is_bank_page:
                print(f"Closing unwanted popup: {url}")
                new_page.close()
            else:
                print(f"Allowing important page: {url}")
        
        #context.on("page", lambda p: p.close() if p != main_page else None)
        context.on("page", handle_new_page)
        # Auto-accept JS dialogs
        self.page.on("dialog", lambda d: d.accept())

    def proceed(self):
        self.enable_popup_auto_close()

class EnableSwalAutoClosePageConfig(BasePage):
    
    def __init__(self, page: Page, **kwargs):
        super().__init__(page, **kwargs)
        self.page = page
    
    def enable_swal_auto_close(self):
        self.page.add_init_script("""
        () => {
            if (window.Swal && !Swal.__autoCloseInstalled) {
                Swal.__autoCloseInstalled = true;
                const originalFire = Swal.fire;
                Swal.fire = function(...args) {
                    const p = originalFire.apply(this, args);
                    setTimeout(() => Swal.close(), 300);
                    return p;
                };
            }
        }
        """)
    
    def proceed(self):
        self.enable_swal_auto_close()

class StealthPageConfig:
    
    def __init__(self, browser_context, **kwargs):
        self.context = browser_context
    
    def apply_stealth(self):
        """
        Injects scripts to mask the automation fingerprint by hiding the 
        webdriver property, mocking chrome objects, and fixing permission queries.
        """
        self.context.add_init_script("""
            () => {
                // 1. Hide the webdriver flag
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // 2. Mock the chrome runtime object
                window.chrome = { runtime: {} };

                // 3. Fix the permissions.query consistency
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications'
                        ? Promise.resolve({ state: Notification.permission })
                        : originalQuery(parameters)
                );
            }
        """)
    
    def proceed(self):
        self.apply_stealth()