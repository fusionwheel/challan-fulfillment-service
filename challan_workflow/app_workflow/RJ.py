from challan_workflow.base.workflow import BaseWorkflow

from challan_workflow.steps.core.common import GoTOeChallanPage
from challan_workflow.steps.core.page_config import EnablePopupAutoClosePageConfig, DisablePopupAutoClosePageConfig
from challan_workflow.steps.core.page_config import EnableSwalAutoClosePageConfig
from challan_workflow.steps.core.page_config import StealthPageConfig
from challan_workflow.steps.core.common import InitiatePaymentLink
from challan_workflow.steps.core.common import VahanMORTHGatewayPage
from challan_workflow.steps.core.sbi_epay import SBIePayPaymentPage
from challan_workflow.steps.netbanking.icici import IciciLoginPage, IciciTransactionPage, IciciTransactionOTPPage
from challan_workflow.steps.egras.RJ import RJGrnPage, RJGrnConfirmPage
from challan_workflow.steps.receipt.download import DownloadReceiptPage
from challan_workflow.steps.gateway.razorpay import RazorpayPmtPreviewPage, RazorpayPaymentPage

class RJWorkflow(BaseWorkflow):
    steps = [
        GoTOeChallanPage,
        EnablePopupAutoClosePageConfig,
        EnableSwalAutoClosePageConfig,
        InitiatePaymentLink,
        VahanMORTHGatewayPage,
        RJGrnPage,
        RJGrnConfirmPage,
        DisablePopupAutoClosePageConfig,
        RazorpayPmtPreviewPage,
        RazorpayPaymentPage,
        #SBIePayPaymentPage,
        IciciLoginPage,
        IciciTransactionPage,
        IciciTransactionOTPPage,
        DownloadReceiptPage,        
    ]