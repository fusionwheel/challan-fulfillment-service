from challan_workflow.base.workflow import BaseWorkflow

from challan_workflow.steps.core.common import GoTOeChallanPage
from challan_workflow.steps.core.page_config import EnablePopupAutoClosePageConfig
from challan_workflow.steps.core.page_config import EnableSwalAutoClosePageConfig
from challan_workflow.steps.core.page_config import StealthPageConfig
from challan_workflow.steps.core.common import InitiatePaymentLink
from challan_workflow.steps.core.common import SBIAggregatePage
from challan_workflow.steps.core.sbi_epay import SBIePayPaymentPage
from challan_workflow.steps.egras.TN import TNSBILandingPage
from challan_workflow.steps.netbanking.icici import IciciLoginPage, IciciTransactionPage, IciciTransactionOTPPage
from challan_workflow.steps.gateway.billdesk import BillDeskSDKPaymentPage
from challan_workflow.steps.receipt.download import DownloadReceiptPage

class TNWorkflow(BaseWorkflow):
    steps_1 = [
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
    
    steps_2 = [
        GoTOeChallanPage,
        EnablePopupAutoClosePageConfig,
        EnableSwalAutoClosePageConfig,
        InitiatePaymentLink,
        TNSBILandingPage,
        SBIePayPaymentPage,
        IciciLoginPage,
        IciciTransactionPage,
        IciciTransactionOTPPage,
        DownloadReceiptPage         
    ]
    
    def get_workflow_steps(self):
        print("self.context.url => ", self.context.url)
        if "sbilanding" in self.context.url.lower():
            return self.steps_2
        else:
            return self.steps_1