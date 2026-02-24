
class DepartmentError(Exception):
    message = "Invalid Department Type!"

class OTPVerificationFailed(Exception):
    message = "OTP Verification Failed"

class OTPTriggerFailed(Exception):
    message = "OTP Trigger Failed"
    
class OTPNotFound(Exception):
    message = "OTP Not Found"

class PaymentLinkError(Exception):
    message = "Payment Link Error"

class PaymentLinkGenerationFailed(Exception):
    message = "Payment Link Generation Failed"

class PaymentInitiatedRecently(Exception):
    message = "Payment Initiated Recently. try after 15 minutes"

class PaymentVerificationFailed(Exception):
    message = "Payment verification failed"

class PaymentLinkAlreadyGenerated(Exception):
    message = "Payment Link Already Generated"

class PaymentLinkOfflineChallanError(Exception):
    message = "Payment Link Offline Challan Error"

class SessionError(Exception):
    message = "Session Error"