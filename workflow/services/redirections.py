from playwright.sync_api import sync_playwright, Page
from playwright_stealth import Stealth
from workflow.base.args import browser_args, browser_ctx_args
from workflow.steps.core.page_config import StealthPageConfig


def handle_post_redirect(url:str, data:dict):
    stealth = Stealth(navigator_languages_override=("en-IN", "en-US", "en"))   
    with stealth.use_sync(sync_playwright()) as p:
        browser = p.chromium.launch_persistent_context(
            channel="chrome", 
            user_data_dir="./user_data",
            headless=False,
            args=browser_args,
            #proxy=proxy,
            slow_mo=100,
            **browser_ctx_args
        )
        StealthPageConfig(browser)
        page:Page = browser.new_page()
        page.goto(url)
        
        html_content = f"""
        <html>
        <body onload="document.forms[0].submit()">
            <form method="POST" action="{url}">
                <input type="hidden" name="encData" value="{data['encData']}">
            </form>
        </body>
        </html>
        """
        
        page.set_content(html_content)
        page.wait_for_load_state("networkidle") 
        print(f"Redirected to: {page.url}")
        content = page.content
        browser.close()
        return content