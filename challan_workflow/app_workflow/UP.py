from challan_workflow.base.workflow import BaseWorkflow

from challan_workflow.steps.core.common import GoTOeChallanPage
from challan_workflow.steps.core.page_config import EnablePopupAutoClosePageConfig
from challan_workflow.steps.core.page_config import EnableSwalAutoClosePageConfig
from challan_workflow.steps.core.page_config import StealthPageConfig
from challan_workflow.steps.core.common import InitiatePaymentLink
from challan_workflow.steps.core.common import SBIAggregatePage
from challan_workflow.steps.core.sbi_epay import SBIePayPaymentPage
from challan_workflow.steps.egras.UP import UPRajKoshLandingPage, UPRajKoshPage
from challan_workflow.steps.core.common import WhichNetBankingProviderSBIAggregatePage, IciciCorpOrRetailSBIAggregatePage
from challan_workflow.steps.netbanking.icici import IciciLoginPage, IciciTransactionPage, IciciTransactionOTPPage
from challan_workflow.steps.gateway.billdesk import BillDeskSDKPaymentPage, BillDeskSDKRetailPaymentPage
from challan_workflow.steps.receipt.payment import PostPaymentSuccessRedirectPage
from challan_workflow.steps.receipt.download import DownloadReceiptPage


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
        PostPaymentSuccessRedirectPage,
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
        BillDeskSDKRetailPaymentPage,
        IciciCorpOrRetailSBIAggregatePage,
        IciciLoginPage,
        IciciTransactionPage,
        IciciTransactionOTPPage,
        PostPaymentSuccessRedirectPage,
        DownloadReceiptPage,        
    ]

    def get_workflow_steps(self):
        if self.context.method == "POST":
            return self.sbiagg_steps
        else:
            return self.rajkosh_steps