from workflow.base.workflow import BaseWorkflow

from workflow.steps.core.common import GoTOeChallanPage
from workflow.steps.core.page_config import EnablePopupAutoClosePageConfig
from workflow.steps.core.page_config import EnableSwalAutoClosePageConfig
from workflow.steps.core.page_config import StealthPageConfig
from workflow.steps.core.common import InitiatePaymentLink
from workflow.steps.core.common import SBIAggregatePage
from workflow.steps.core.sbi_epay import SBIePayPaymentPage
from workflow.steps.egras.UP import UPRajKoshLandingPage, UPRajKoshPage
from workflow.steps.core.common import WhichNetBankingProviderSBIAggregatePage
from workflow.steps.netbanking.icici import IciciLoginPage, IciciTransactionPage, IciciTransactionOTPPage
from workflow.steps.core.billdesk import BillDeskSDKPaymentPage
from workflow.steps.receipt.download import DownloadReceiptPage

class UPWorkflow(BaseWorkflow):
    rajkosh_steps = [
        GoTOeChallanPage,
        EnablePopupAutoClosePageConfig,
        EnableSwalAutoClosePageConfig,
        InitiatePaymentLink,
        # RAJ KOSH steps
        UPRajKoshLandingPage,
        UPRajKoshPage,
        WhichNetBankingProviderSBIAggregatePage,
        BillDeskSDKPaymentPage,
        IciciLoginPage,
        IciciTransactionPage,
        IciciTransactionOTPPage,
        DownloadReceiptPage,        
    ]
    
    sbiagg_steps = [
        GoTOeChallanPage,
        EnablePopupAutoClosePageConfig,
        EnableSwalAutoClosePageConfig,
        InitiatePaymentLink,
        # SBI AGGREGATE steps
        SBIAggregatePage,
        WhichNetBankingProviderSBIAggregatePage,
        BillDeskSDKPaymentPage,
        IciciLoginPage,
        IciciTransactionPage,
        IciciTransactionOTPPage,
        DownloadReceiptPage,        
    ]

    def get_workflow_steps(self):
        if self.context.method == "POST":
            return self.sbiagg_steps
        else:
            return self.rajkosh_steps