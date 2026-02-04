from playwright.sync_api import Page
from workflow.base import exception
from workflow.services.fw import FWLink
from sms.adb_manager import ADBOTPManager
from workflow import config

class WorkflowContext:
    
    def __init__(
            self, 
            st_cd: str = None,
            otp_mobile_no: str = None,
            url: str = None, 
            method: str = None, 
            payload: dict = None,
            reg_no: str = None,
            appointment_id: str = None,
            order_item_id: str = None,
            challan_no: str = None,
            owner_name: [str, None] = None,
            owner_mobile_no: [str, None] = None,
            payment_remarks: [str, None] = None,
            netbanking_username: [str, None] = None,
            netbanking_password: [str, None] = None,
            **kwargs
        ):
        self.st_cd = st_cd
        self.url = url
        self.method = method
        self.payload = payload
        self.reg_no = reg_no
        self.appointment_id = appointment_id
        self.order_item_id = order_item_id
        self.challan_no = challan_no
        self.owner_name = owner_name
        self.owner_mobile_no = owner_mobile_no
        self.otp_mobile_no = otp_mobile_no
        self.payment_remarks = payment_remarks
        self.netbanking_username = netbanking_username
        self.netbanking_password = netbanking_password
    
    def to_dict(self):
        return self.__dict__

class PaymentLinkContext(WorkflowContext):
    def __init__(self, *args, **kwrgs) -> None:
        super().__init__(*args, **kwrgs)
        #self.context = WorkflowContext(appointment_id=appointment_id, order_item_id=order_item_id, challan_no=challan_no, payment_remarks=payment_remarks)
        self.set_context()
    
    def get_fw_client(self):
        if not hasattr(self, "fw_service"):
            if self.appointment_id:
                self.fw_service = FWLink.from_appointment_id(app_id=self.appointment_id, challan_no=self.challan_no)
            else:
                self.fw_service = FWLink.from_order_item_id(order_item_id=self.order_item_id, challan_no=self.challan_no)
        return self.fw_service
    
    def get_payment_data(self, verify_payment):
        fw_service = self.get_fw_client()
        print(f"  deleting Existing OTP's from {self.otp_mobile_no}...")
        fw_service.delete_otp(mobile_no=self.otp_mobile_no, challan_no=self.challan_no)
        print(f"  Sending OTP on {self.otp_mobile_no}...")
        fw_service.send_otp(mobile_no=self.otp_mobile_no)
        print("*" * 50)
        print(f"  Waiting for OTP SMS on {self.otp_mobile_no}...")
        adb_manager = ADBOTPManager(sender_name="VAAHAN")
        otp_details = adb_manager.get_otp_details(body_contains="getting challan detail at eChallan")
        if not otp_details:
            raise exception.OTPNotFound("OTP not found !")
        
        print("  Found OTP details =>", otp_details)
        print("*" * 50)
        print("  OTP Verification in progress...")
        fw_service.verify_otp(otp=otp_details.get("otp"))
        print("  OTP Verification completed !")
        print("*" * 50)
        print("  Payment Link Generation in progress...")
        print(f"  Payment type: {verify_payment}")
        payment_data = fw_service.generate_payment_link(verify_payment=verify_payment)
        del otp_details; del adb_manager
        return payment_data
    
    def set_context(self):
        fw_service = self.get_fw_client()
        print("*" * 50)
        
        ST_CODE = fw_service.challan_no[:2]
        
        print(f"OTP Mobile No: {self.otp_mobile_no}")
        print(f"Reg No: {fw_service.reg_no}")
        print(f"Challan No: {fw_service.challan_no}")
        print(f"Owner Mobile No: {fw_service.owner_mobile_no}")
        print(f"Owner Name: {fw_service.owner_name}")
        print(f"Payment Remarks: {self.payment_remarks}")
        print(f"ST Code: {ST_CODE}")
        print("*" * 50)
        
        verify_payment = config.PMT_VERIFY_IX.get(ST_CODE, config.DEFAULT_PMT_VERIFY_IX) 
        
        max_retry_count = 3
        payment_data = {}
        for i in range(max_retry_count):
            try:            
                payment_data = self.get_payment_data(verify_payment=verify_payment)
                if payment_data:
                    break
            except exception.OTPNotFound:
                if i == max_retry_count - 1:
                    raise exception.OTPNotFound("OTP not found !")
                continue
            except exception.PaymentLinkAlreadyGenerated as e:
                try:
                    if "challan payment is pending" in e.message.lower():
                        self.get_payment_data(verify_payment=1)
                        # verify payment to get existing link
                        continue
                except:
                    pass
                if i == max_retry_count - 1:
                    raise exception.PaymentLinkAlreadyGenerated("Payment Link Already Generated!")
                continue
            
            except exception.DepartmentError:
                verify_payment = 0 if verify_payment == 2 else 2 # invert verify_payment
                continue
            except exception.PaymentLinkOfflineChallanError:
                raise exception.PaymentLinkOfflineChallanError("Payment Link Generation failed => Offline Challan !")
            
            except Exception as e:
                if i == max_retry_count - 1:
                    raise exception.PaymentLinkGenerationFailed("Payment Link Generation failed ! Reason =>", e)
                continue
            
        if "payment_url" in payment_data:
            if "challan" not in payment_data.get("payment_url"):
                print("  Payment Link Generation completed !")
            else:
                raise exception.PaymentLinkOfflineChallanError("Payment Link Generation failed => Offline Challan !")
        else:
            raise exception.PaymentLinkGenerationFailed("Payment Link Generation failed ! Reason =>", payment_data.get("reason") or payment_data.get("message"))
        
        print("*" * 50)
        
        self.reg_no = fw_service.reg_no        
        self.challan_no = fw_service.challan_no
        self.owner_mobile_no = fw_service.owner_mobile_no
        self.owner_name = fw_service.owner_name
        self.st_cd = fw_service.challan_no[:2]
        
        self.url = payment_data.get("payment_url")
        self.method = payment_data.get("payment_method")
        self.payload = payment_data.get("payment_data")
        
        del fw_service
        print("payment_link =>", self.url)
        print("payment_method =>", self.method)
        print("payment_data =>", self.payload)
    
    def to_dict(self):
        if hasattr(self, "fw_service"):
            del self.fw_service
        return super().to_dict()


class QueueContext(PaymentLinkContext):
    def __init__(self, *args, **kwrgs) -> None:
        super().__init__(*args, **kwrgs)
        
    def get_fw_client(self):
        if not hasattr(self, "fw_service"):
            self.fw_service = FWLink(
                reg_no=self.reg_no, 
                challan_no=self.challan_no, 
                mobile_no=self.owner_mobile_no,
                owner_name=self.owner_name
            )
        return self.fw_service
