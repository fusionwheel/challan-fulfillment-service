from workflow.base.workflow import BaseWorkflow

from workflow.steps.core.common import GoTOeChallanPage
from workflow.steps.core.page_config import EnablePopupAutoClosePageConfig
from workflow.steps.core.page_config import EnableSwalAutoClosePageConfig
from workflow.steps.core.page_config import StealthPageConfig
from workflow.steps.core.common import InitiatePaymentLink
from workflow.steps.core.common import SBIAggregatePage
from workflow.steps.core.sbi_epay import SBIePayPaymentPage
from workflow.steps.netbanking.icici import IciciLoginPage, IciciTransactionPage, IciciTransactionOTPPage
from workflow.steps.core.billdesk import BillDeskSDKPaymentPage
from workflow.steps.receipt.download import DownloadReceiptPage

class GJWorkflow(BaseWorkflow):
    steps = [
        GoTOeChallanPage,
        EnablePopupAutoClosePageConfig,
        EnableSwalAutoClosePageConfig,
        InitiatePaymentLink,
        SBIAggregatePage,
        SBIePayPaymentPage,
        IciciLoginPage,
        IciciTransactionPage,
        IciciTransactionOTPPage,
        DownloadReceiptPage         
    ]