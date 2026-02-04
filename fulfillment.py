import os
from datetime import datetime
from playwright.sync_api import sync_playwright, Page
from playwright_stealth import Stealth

from workflow.base.context import PaymentLinkContext, QueueContext
from workflow.services.fw import FWLink
from workflow.workflows.manager import WorkflowManager
from workflow.steps.core.page_config import StealthPageConfig
from workflow.base.args import browser_args, browser_ctx_args
from workflow.services.Parivahan import Parivahan
from workflow.base import exception

from dotenv import load_dotenv
load_dotenv()

SMS_SENDER_MOB_NO = "8448492299"

icici_user_id = os.getenv("ICICI_NETBANKING_USER_ID")
icici_password = os.getenv("ICICI_NETBANKING_PASSWORD")
mob_no_for_otp = os.getenv("MOB_NO_FOR_OTP")
FW_BASE_URL = os.getenv("FW_BASE_URL")

print("NETBANKING USER ID", icici_user_id)
print("NETBANKING PASSWORD", icici_password.replace("", "*"))
print("MOB NO FOR OTP", mob_no_for_otp)
print("FW BASE URL", FW_BASE_URL)
print("-" * 50)
proxy=None


def process_from_queue(order_item_id, reg_no, challan_no, payment_remarks, owner_name, owner_mobile_no,  **kwargs):
    parivahan = Parivahan(reg_no=reg_no)
    pmt_st_data = parivahan.get_payment_status(challan_no=challan_no)
    
    if not pmt_st_data:
        pmt_st_data = parivahan.etrans_pgi_payment_status(challan_no=challan_no)
    
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
    try:
        st_cd: str = str(challan_no).upper()[:2]
        challan_ctx = QueueContext(
            st_cd=st_cd,
            otp_mobile_no=mob_no_for_otp,
            order_item_id=order_item_id,
            reg_no=reg_no,
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
        print(f"Exception {order_item_id}")
        return {
                "status": "FAILED",
                "state": "LINK_FAILED",
                "message": f"Exception: {e}",
                "exception": str(e),
                "step": "LINK_GENERATION"
            }
    
    stealth = Stealth(navigator_languages_override=("en-IN", "en-US", "en"))   
    with stealth.use_sync(sync_playwright()) as p:
        browser_ctx = p.chromium.launch_persistent_context(
            channel="chrome", 
            user_data_dir="./user_data",
            headless=False,
            args=browser_args,
            #proxy=proxy,
            slow_mo=100,
            **browser_ctx_args
        )
        StealthPageConfig(browser_ctx)
        page:Page = browser_ctx.new_page()
        webdriver_status = page.evaluate("navigator.webdriver")
        print(f"Is Webdriver detected? {webdriver_status}")
        path = f"screenshots/{challan_ctx.st_cd}/{datetime.now().strftime('%Y-%m-%d')}/{challan_ctx.appointment_id or challan_ctx.order_item_id}_{challan_ctx.challan_no}.png"
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
        
        try:
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
                print(f"Payment failed {order_item_id} state: {getattr(challan_ctx, "state", "PAYMENT_FAILED")} message: {getattr(challan_ctx, "message", "Payment initiation failed")} step: {getattr(challan_ctx, "step", "PAYMENT_INITIATED_PAGE")} pgi_amount: {getattr(challan_ctx, "pgi_amount", 0)}")
                response = {
                    "status": "FAILED",
                    "state": "PAYMENT_FAILED",
                    "message": getattr(challan_ctx, "message", "Payment initiation failed"),
                    "exception": str(e),
                    "step": getattr(challan_ctx, "step", "PAYMENT_INITIATED_PAGE"),
                    "pgi_amount": getattr(challan_ctx, "pgi_amount", 0)
                }
        
        page.close()   
        browser_ctx.close()
        
        return response
    

def process(order_item_id, type, reg_no, challan_no, payment_remarks, **kwargs):
    
    if str(type).upper() == "C2B":
        APP_ID = order_item_id
    else:
        APP_ID = None
    
    CHALLAN_NO = challan_no
    PMT_REMARKS = payment_remarks
    
    parivahan = Parivahan(reg_no=reg_no)
    pmt_st_data = parivahan.get_payment_status(challan_no=CHALLAN_NO)
    
    if not pmt_st_data:
        pmt_st_data = parivahan.etrans_pgi_payment_status(challan_no=CHALLAN_NO)
    
    if pmt_st_data:
        print("Payment status", pmt_st_data)
        
        if parivahan.is_payment_success(pmt_st_data):
            return {
                "status": "success",
                "state": "ALREADY_PAID",
                "message": "Payment already paid",
                "settlement_amount": pmt_st_data.get("settlement_amount"),
            }
        
        if parivahan.is_payment_initiated_recently(pmt_st_data):
            return {
                "status": "failed",
                "state": "PAYMENT_INITIATED_RECENTLY",
                "message": "Payment already initiated recently. will be processed after 15 minutes"
            }
        
        if parivahan.is_payment_pending(pmt_st_data):
            return {
                "status": "failed",
                "state": "PAYMENT_PENDING",
                "message": "Payment already in pending state"
            }
    try:
        challan_ctx = PaymentLinkContext(
            challan_no=CHALLAN_NO, appointment_id=APP_ID, order_item_id=order_item_id,
            payment_remarks=PMT_REMARKS, otp_mobile_no=mob_no_for_otp,
            netbanking_username=icici_user_id, netbanking_password=icici_password
        )
    except exception.DepartmentError:
        return {
                "status": "failed",
                "state": "DEPARTMENT_ERROR",
                "message": "Department Error"
            }
    
    except exception.PaymentLinkOfflineChallanError:
        return {
                "status": "failed",
                "state": "OFFLINE_CHALLAN_ERROR",
                "message": "Payment Link Offline Challan Error"
            }
    
    except exception.PaymentLinkAlreadyGenerated:
        return {
                "status": "failed",
                "state": "LINK_ALREADY_GENERATED",
                "message": "Payment Link Already Generated"
            }
    
    except Exception as e:
        return {
                "status": "failed",
                "state": "LINK_GENERATION_FAILED",
                "message": f"{e}"
            }
    
    stealth = Stealth(navigator_languages_override=("en-IN", "en-US", "en"))   
    with stealth.use_sync(sync_playwright()) as p:
        browser_ctx = p.chromium.launch_persistent_context(
            channel="chrome", 
            user_data_dir="./user_data",
            headless=False,
            args=browser_args,
            #proxy=proxy,
            slow_mo=100,
            **browser_ctx_args
        )
        StealthPageConfig(browser_ctx)
        page:Page = browser_ctx.new_page()
        webdriver_status = page.evaluate("navigator.webdriver")
        print(f"Is Webdriver detected? {webdriver_status}")
        path = f"screenshots/{challan_ctx.st_cd}/{datetime.now().strftime('%Y-%m-%d')}/{challan_ctx.appointment_id or challan_ctx.order_item_id}_{challan_ctx.challan_no}.png"
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
        
        try:
            WorkflowManager.run_state_workflow(page=page, context=challan_ctx)    
            page.screenshot(path=path)
            
            print("Payment completed successfully")
            receipt_url = getattr(challan_ctx, "receipt_url", None)
            pay_state = "PAYMENT_SUCCESS_WITH_RECEIPT" if receipt_url else "PAYMENT_SUCCESS_WITHOUT_RECEIPT"
            response = {
                "status": "success",
                "state": pay_state,
                "message": "Payment completed successfully",
                "receipt_url": receipt_url,
                "step": "PAYMENT_SUCCESS_PAGE",
                "pgi_amount": getattr(challan_ctx, "pgi_amount", 0)
            }
        except Exception as e:
            print("Exception in run_state_workflow", e)
            try:page.screenshot(path=path)
            except:pass
            otp_success = getattr(challan_ctx, "otp_success", 0)
            if otp_success:
                response = {
                    "status": "success",
                    "state": "PAYMENT_SUCCESS",
                    "message": "Banking transaction completed successfully! Receipt failed to download",
                    "step": getattr(challan_ctx, "step", "PAYMENT_SUCCESS_PAGE"),
                    "pgi_amount": getattr(challan_ctx, "pgi_amount", 0)
                }
                
            else:
                response = {
                    "status": "failed",
                    "state": getattr(challan_ctx, "state", "PAYMENT_FAILED"),
                    "message": getattr(challan_ctx, "message", "Payment initiation failed"),
                    "step": getattr(challan_ctx, "step", "PAYMENT_INITIATED_PAGE"),
                    "pgi_amount": getattr(challan_ctx, "pgi_amount", 0)
                }
        
        page.close()   
        browser_ctx.close()
        
        return response