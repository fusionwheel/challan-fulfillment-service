from challan_workflow.base.workflow import BaseWorkflow

from challan_workflow.steps.core.common import GoTOeChallanPage
from challan_workflow.steps.core.page_config import EnablePopupAutoClosePageConfig
from challan_workflow.steps.core.page_config import EnableSwalAutoClosePageConfig
from challan_workflow.steps.core.page_config import StealthPageConfig
from challan_workflow.steps.core.common import InitiatePaymentLink
from challan_workflow.steps.core.common import SBIAggregatePage
from challan_workflow.steps.egras.HR import EgrassGrnPage 
from challan_workflow.steps.core.common import WhichNetBankingProviderSBIAggregatePage
from challan_workflow.steps.netbanking.icici import IciciLoginPage, IciciTransactionPage, IciciTransactionOTPPage
from challan_workflow.steps.gateway.billdesk import BillDeskSDKPaymentPage
from challan_workflow.steps.receipt.download import DownloadReceiptPage
from challan_workflow.steps.receipt.payment import PostPaymentSuccessRedirectPage

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
        PostPaymentSuccessRedirectPage,
        DownloadReceiptPage,
    ]