from workflow.base.workflow import BaseWorkflow

from workflow.steps.core.common import GoTOeChallanPage
from workflow.steps.core.page_config import EnablePopupAutoClosePageConfig
from workflow.steps.core.page_config import EnableSwalAutoClosePageConfig
from workflow.steps.core.page_config import StealthPageConfig
from workflow.steps.core.common import InitiatePaymentLink
from workflow.steps.core.common import VahanMORTHGatewayPage
from workflow.steps.core.sbi_epay import SBIePayPaymentPage
from workflow.steps.netbanking.icici import IciciLoginPage, IciciTransactionPage, IciciTransactionOTPPage
from workflow.steps.egras.RJ import EgrassGrnPage
from workflow.steps.receipt.download import DownloadReceiptPage
from workflow.steps.core.billdesk import BillDeskSDKPaymentPage

class RJWorkflow(BaseWorkflow):
    steps = [
        GoTOeChallanPage,
        EnablePopupAutoClosePageConfig,
        EnableSwalAutoClosePageConfig,
        InitiatePaymentLink,
        VahanMORTHGatewayPage,
        EgrassGrnPage,
        BillDeskSDKPaymentPage,
        #SBIePayPaymentPage,
        IciciLoginPage,
        IciciTransactionPage,
        IciciTransactionOTPPage,
        DownloadReceiptPage,        
    ]