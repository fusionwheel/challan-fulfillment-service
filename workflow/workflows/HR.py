from workflow.base.workflow import BaseWorkflow

from workflow.steps.core.common import GoTOeChallanPage
from workflow.steps.core.page_config import EnablePopupAutoClosePageConfig
from workflow.steps.core.page_config import EnableSwalAutoClosePageConfig
from workflow.steps.core.page_config import StealthPageConfig
from workflow.steps.core.common import InitiatePaymentLink
from workflow.steps.core.common import SBIAggregatePage
from workflow.steps.egras.HR import EgrassGrnPage 
from workflow.steps.core.common import WhichNetBankingProviderSBIAggregatePage
from workflow.steps.netbanking.icici import IciciLoginPage, IciciTransactionPage, IciciTransactionOTPPage
from workflow.steps.core.billdesk import BillDeskSDKPaymentPage
from workflow.steps.receipt.download import DownloadReceiptPage
from workflow.steps.receipt.HR import HRPostPaymentSuccessRedirectPage

class HRWorkflow(BaseWorkflow):
    steps = [
        GoTOeChallanPage,
        EnablePopupAutoClosePageConfig,
        EnableSwalAutoClosePageConfig,
        InitiatePaymentLink,
        SBIAggregatePage,
        EgrassGrnPage,
        WhichNetBankingProviderSBIAggregatePage,
        BillDeskSDKPaymentPage,
        IciciLoginPage,
        IciciTransactionPage,
        IciciTransactionOTPPage,
        HRPostPaymentSuccessRedirectPage,
        DownloadReceiptPage,
    ]