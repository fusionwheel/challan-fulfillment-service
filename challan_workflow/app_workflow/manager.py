import gc
from challan_workflow.app_workflow.HR import HRWorkflow
from challan_workflow.app_workflow.AS import ASWorkflow
from challan_workflow.app_workflow.RJ import RJWorkflow
from challan_workflow.app_workflow.DL import DLWorkflow
from challan_workflow.app_workflow.WB import WBWorkflow
from challan_workflow.app_workflow.GJ import GJWorkflow
from challan_workflow.app_workflow.MH import MHWorkflow
from challan_workflow.app_workflow.UP import UPWorkflow
from challan_workflow.app_workflow.TN import TNWorkflow
from challan_workflow.app_workflow.KL import KLWorkflow
from challan_workflow.app_workflow.AP import APWorkflow

# TN / KA / KL / MP / JH / BR / OR / AP / CG / CH / GA / GO / HP / NL / PB / TS / UK 

class WorkflowManager:
    # 1. Define the mapping of states to their respective classes
    WORKFLOW_MAP = {
        #"AP": APWorkflow,
        "AS": ASWorkflow,
        "DL": DLWorkflow,
        "GJ": GJWorkflow,
        "HR": HRWorkflow,
        "MH": MHWorkflow,
        "RJ": RJWorkflow,
        "UP": UPWorkflow,
        "WB": WBWorkflow,
        "TN": TNWorkflow,
        "KL": KLWorkflow,
    }

    @classmethod
    def run_state_workflow(cls, page, context):
        st_cd = context.st_cd
        
        # 2. Look up the class based on the state
        workflow_class = cls.WORKFLOW_MAP.get(st_cd)

        if workflow_class:
            # 3. Instantiate and run
            try:
                wflow = workflow_class(page, context=context)
                wflow.run()
            finally:
                del wflow; del workflow_class; gc.collect()
        else:
            print(f"No workflow defined for state: {st_cd}")
            raise Exception(f"No workflow defined for state: {st_cd}")