import os
from datetime import datetime
from playwright.sync_api import sync_playwright, Page
from playwright_stealth import Stealth
from challan_workflow.base.args import browser_args, browser_ctx_args
from challan_workflow.steps.core.page_config import StealthPageConfig
from challan_workflow.steps.core.common import InitiatePending2FailedPaymentLink, GoTOeChallanPage, InitiatePaymentLink


headless = os.getenv("HEADLESS", "false").lower() == "true"

def handle_post_redirect(url:str, method:str, data:dict, challan_no:str=None, only_text:bool=False):
    stealth = Stealth(navigator_languages_override=("en-IN", "en-US", "en"))   
    with stealth.use_sync(sync_playwright()) as p:
        browser = p.chromium.launch_persistent_context(
            channel="chrome", 
            user_data_dir="./user_data",
            headless=headless,
            args=browser_args,
            #proxy=proxy,
            slow_mo=100,
            **browser_ctx_args
        )
        try:
            StealthPageConfig(browser)
            page:Page = browser.new_page()
            page.set_default_timeout(15000)
            page.set_default_navigation_timeout(15000)
            try:
                page.goto("https://echallan.parivahan.gov.in", wait_until="domcontentloaded", timeout=15000)
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception as e:
                print(f"✗ Error going to eChallan page: {e}")
            page.wait_for_timeout(1000)
            
            InitiatePending2FailedPaymentLink(
                page,
                url=url,
                method=method,
                payload=data
            ).proceed()
            
            content = (
                page.evaluate("document.documentElement.innerText")
                if only_text
                else page.content()
            )
            
            if challan_no:
                # save to path
                st_cd = str(challan_no).upper()[:2]
                path = f"screenshots/pending_failed/{st_cd}/{datetime.now().strftime('%Y-%m-%d')}/{challan_no}.png"
                os.makedirs(os.path.dirname(path), exist_ok=True)
                print(f"Saving screenshot to {path}")
                try:
                    page.screenshot(path=path)
                except Exception as e:
                    print(f"✗ Error taking screenshot: {e}")
            
            return content
        except Exception as e:
            print(f"✗ Error handling post redirect: {e}")
            return None
        finally:
            browser.close()