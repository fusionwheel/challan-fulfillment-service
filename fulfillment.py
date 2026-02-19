import os
import time
import shutil
import traceback
from datetime import datetime

from challan_workflow.base.context import QueueContext
from challan_workflow.app_workflow.manager import WorkflowManager
from challan_workflow.steps.core.page_config import StealthPageConfig
from challan_workflow.base.args import browser_args, browser_ctx_args
from challan_workflow.base.args import firefox_browser_args, firefox_browser_ctx_args
from challan_workflow.services.Parivahan import Parivahan
from challan_workflow.base import exception

def process_from_queue(order_item_id:str, reg_no:str, challan_no:str, payment_remarks:str, owner_name:str, owner_mobile_no:str, appointment_id:str=None, **kwargs):
    print("PID:", os.getpid(), "PPID:", os.getppid())
    
    # import shutil
    # from challan_workflow.base.context import QueueContext
    # from challan_workflow.app_workflow.manager import WorkflowManager
    # from challan_workflow.steps.core.page_config import StealthPageConfig
    # from challan_workflow.base.args import browser_args, browser_ctx_args
    # from challan_workflow.base.args import firefox_browser_args, firefox_browser_ctx_args
    # from challan_workflow.services.Parivahan import Parivahan
    # from challan_workflow.base import exception

    from playwright.sync_api import sync_playwright, Page, BrowserContext
    from playwright_stealth import Stealth
    
    # from env 
    icici_user_id:str = os.environ.get("ICICI_NETBANKING_USER_ID")
    icici_password:str = os.environ.get("ICICI_NETBANKING_PASSWORD")
    mob_no_for_otp:str = os.environ.get("MOB_NO_FOR_OTP")
    headless = os.getenv("HEADLESS", "false").lower() == "true"
    
    if not icici_user_id or not icici_password or not mob_no_for_otp:
        raise ValueError("ICICI_NETBANKING_USER_ID, ICICI_NETBANKING_PASSWORD, MOB_NO_FOR_OTP are required")
    
    
    parivahan:Parivahan = Parivahan(reg_no=reg_no)
    
    pmt_st_data:[dict, None] = None
    
    for i in range(2):
        try:
            pmt_st_data = parivahan.get_payment_status(challan_no=challan_no)
            if not pmt_st_data:
                pmt_st_data = parivahan.etrans_pgi_payment_status(challan_no=challan_no)
            break
        except Exception as e:
            print("Exception in get_payment_status", e)
            continue
            
    if pmt_st_data:
        print("Payment status", pmt_st_data)
        
        if parivahan.is_payment_success(pmt_st_data):
            return {
                "status": "SUCCESS",
                "state": "ALREADY_PAID",
                "step": "LINK_GENERATION",
                "message": "Payment already paid"
            }
        
        if parivahan.is_payment_initiated_recently(pmt_st_data):
            return {
                "status": "FAILED",
                #"state": "PAYMENT_INITIATED_RECENTLY",
                "state": "LINK_FAILED",
                "step": "LINK_GENERATION",
                "message": "Payment already initiated recently. will be processed after 15 minutes"
            }
        
        if parivahan.is_payment_pending(pmt_st_data):
            if not parivahan.verify_payment(pmt_st_data):
                # After verification, check again
                return {
                    "status": "FAILED",
                    #"state": "PAYMENT_PENDING",
                    "state": "LINK_FAILED",
                    "step": "LINK_GENERATION",
                    "message": "Payment already in pending state"
                }
                
    del parivahan
    
    try:
        st_cd: str = str(challan_no).upper()[:2]
        challan_ctx:QueueContext = QueueContext(
            st_cd=st_cd,
            otp_mobile_no=mob_no_for_otp,
            order_item_id=order_item_id,
            reg_no=reg_no,
            appointment_id=appointment_id,
            challan_no=challan_no, 
            owner_name=owner_name,
            owner_mobile_no=owner_mobile_no,
            payment_remarks=payment_remarks,
            netbanking_username=icici_user_id, 
            netbanking_password=icici_password
        )
    except exception.DepartmentError:
        print(f"Department Error {order_item_id}")
        return {
                "status": "FAILED",
                "state": "LINK_FAILED",
                "step": "LINK_GENERATION",
                "message": "Department Error"
            }
    
    except exception.PaymentLinkOfflineChallanError:
        print(f"Offline Challan Error {order_item_id}")
        return {
                "status": "FAILED",
                "state": "LINK_FAILED",
                "step": "LINK_GENERATION",
                "message": "Payment Link Offline Challan Error"
            }
    
    except exception.PaymentLinkAlreadyGenerated:
        print(f"Already Generated {order_item_id}")
        return {
                "status": "FAILED",
                "state": "LINK_FAILED",
                "step": "LINK_GENERATION",
                "message": "Payment Link Already Generated",
            }
    
    except Exception as e:
        print(f"Exception in Link Generation {order_item_id} | {e}")
        traceback.print_exc()
        return {
                "status": "FAILED",
                "state": "LINK_FAILED",
                "message": f"Exception: {e}",
                "exception": str(e),
                "step": "LINK_GENERATION"
            }
    thread_data_dir:str = os.path.join("./user_data", f"ctx_{order_item_id}")
    page:Page = None
    browser_ctx:BrowserContext = None
    try:
        stealth:Stealth = Stealth(navigator_languages_override=("en-IN", "en-US", "en"))   
        os.makedirs(thread_data_dir, exist_ok=True) # Ensure it exists
        with stealth.use_sync(sync_playwright()) as p:
            browser_ctx = p.firefox.launch_persistent_context(
                channel="firefox", 
                user_data_dir=thread_data_dir,
                headless=False,
                #args=browser_args,
                args=firefox_browser_args,
                #proxy=proxy,
                slow_mo=100,
                **firefox_browser_ctx_args
                #**browser_ctx_args
            )
            # browser = p.chromium.launch(
            #     channel="chrome",
            #     headless=headless,
            #     args=browser_args,
            # )
            # browser_ctx = browser.new_context(
            #     **browser_ctx_args
            # )
            StealthPageConfig(browser_ctx)
            page:Page = browser_ctx.new_page()
            webdriver_status = page.evaluate("navigator.webdriver")
            print(f"Is Webdriver detected? {webdriver_status}")
            path = f"screenshots/{challan_ctx.st_cd}/{datetime.now().strftime('%Y-%m-%d')}/{challan_ctx.order_item_id or challan_ctx.appointment_id}_{challan_ctx.challan_no}.png"
            #if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            max_repeat = 1 if challan_ctx.st_cd == "UP" else 2
            
            try:
                # UP challan can be processed only once
                WorkflowManager.run_state_workflow(page=page, context=challan_ctx)
                page.screenshot(path=path)
                print("Payment completed successfully")
                receipt_url = getattr(challan_ctx, "receipt_url", None)
                pay_state = "PAYMENT_SUCCESS_WITH_RECEIPT" if receipt_url else "PAYMENT_SUCCESS_WITHOUT_RECEIPT"
                response = {
                    "status": "SUCCESS",
                    "state": pay_state,
                    "message": "Payment completed successfully",
                    "receipt_url": receipt_url,
                    "step": getattr(challan_ctx, "step", "PAYMENT_SUCCESS_PAGE"),
                    "pgi_amount": getattr(challan_ctx, "pgi_amount", 0)
                }
            except Exception as e:
                traceback.print_exc()
                print("Exception in run_state_workflow", e)
                try:page.screenshot(path=path)
                except:pass
                otp_success = getattr(challan_ctx, "otp_success", 0)
                if otp_success:
                    response = {
                        "status": "SUCCESS",
                        "state": "PAYMENT_SUCCESS_WITHOUT_RECEIPT",
                        "message": "Banking transaction completed successfully! Receipt failed to download",
                        "exception": str(e),
                        "step": getattr(challan_ctx, "step", "PAYMENT_SUCCESS_PAGE"),
                        "pgi_amount": getattr(challan_ctx, "pgi_amount", 0)
                    }
                    
                else:
                    print(
                        f"Payment failed {order_item_id} "
                        f"state: {getattr(challan_ctx, 'state', 'PAYMENT_FAILED')} "
                        f"message: {getattr(challan_ctx, 'message', 'Payment initiation failed')} "
                        f"step: {getattr(challan_ctx, 'step', 'PAYMENT_INITIATED_PAGE')} "
                        f"pgi_amount: {getattr(challan_ctx, 'pgi_amount', 0)}"
                    )

                    response = {
                        "status": "FAILED",
                        "state": "PAYMENT_FAILED",
                        "message": getattr(challan_ctx, "message", "Payment initiation failed"),
                        "exception": str(e),
                        "step": getattr(challan_ctx, "step", "PAYMENT_INITIATED_PAGE"),
                        "pgi_amount": getattr(challan_ctx, "pgi_amount", 0)
                    }
            finally:
                try:
                    if page:
                        page.close()
                    if browser_ctx:
                        browser_ctx.close()
                    del stealth; del page; del browser_ctx; del challan_ctx
                except:pass
            
            return response
    
    except Exception as e:
        traceback.print_exc()
        return {
            "status": "FAILED",
            "state": "INIT_FAILED",
            "message": "Payment initiation failed",
            "exception": str(e),
            "step": "LINK_GENERATION",
            "pgi_amount": 0
        }
    finally:
        # remove thread data dir
        time.sleep(2)
        try:
            if os.path.exists(thread_data_dir):
                shutil.rmtree(thread_data_dir, ignore_errors=True)
        except:
            pass