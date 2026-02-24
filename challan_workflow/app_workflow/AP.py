import gc
from challan_workflow.base.workflow import BaseWorkflow

from challan_workflow.steps.core.common import GoTOeChallanPage
from challan_workflow.steps.core.page_config import EnablePopupAutoClosePageConfig
from challan_workflow.steps.core.page_config import EnableSwalAutoClosePageConfig
from challan_workflow.steps.core.page_config import StealthPageConfig
from challan_workflow.steps.core.common import InitiatePaymentLink
from challan_workflow.steps.core.sbi_epay import SBIePayPaymentPage
from challan_workflow.steps.netbanking.icici import IciciLoginPage, IciciTransactionPage, IciciTransactionOTPPage
from challan_workflow.steps.gateway.billdesk import BillDeskSDKPaymentPage
from challan_workflow.steps.receipt.download import DownloadReceiptPage
from challan_workflow.steps.egras.AP import APSBIAggregatePage, APTreasuryGrnPage
from challan_workflow.steps.core.common import WhichNetBankingProviderSBIAggregatePage

class APWorkflow(BaseWorkflow):
    
    inital_steps = [
         GoTOeChallanPage,
        EnablePopupAutoClosePageConfig,
        EnableSwalAutoClosePageConfig,
        InitiatePaymentLink,
        APSBIAggregatePage,
    ]
    
    steps_cfms = [
        APTreasuryGrnPage, # skip if not CFMS
        WhichNetBankingProviderSBIAggregatePage,
        BillDeskSDKPaymentPage,
    ]
    
    steps_sbi_epay = [
         SBIePayPaymentPage,
    ]
    
    complete_steps = [
        IciciLoginPage,
        IciciTransactionPage,
        IciciTransactionOTPPage,
        DownloadReceiptPage         
    ]
    
    def get_workflow_steps(self):
        return self.inital_steps
    
    def run(self):
        # initial steps
        for klass in self.get_workflow_steps():
            try:
                step = klass(self.page, ctx=self.context, **self.context.to_dict())
                step.proceed()
            finally:
                del step; gc.collect()
    
        # further steps based on. gateway chosen in inital steps
        further_steps = self.steps_sbi_epay if getattr(self.context, "gateway", "") == "SBI" else self.steps_cfms
        further_steps = further_steps + self.complete_steps
    
        for klass in further_steps:
            try:
                step = klass(self.page, ctx=self.context, **self.context.to_dict())
                step.proceed()
            finally:
                del step; gc.collect()