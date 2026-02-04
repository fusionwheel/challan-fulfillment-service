from workflow.workflows.HR import HRWorkflow
from workflow.workflows.AS import ASWorkflow
from workflow.workflows.RJ import RJWorkflow
from workflow.workflows.DL import DLWorkflow
from workflow.workflows.WB import WBWorkflow
from workflow.workflows.GJ import GJWorkflow
from workflow.workflows.MH import MHWorkflow
from workflow.workflows.UP import UPWorkflow

# TN / KA / KL / MP / JH / BR / OR / AP / CG / CH / GA / GO / HP / NL / PB / TS / UK 

class WorkflowManager:
    # 1. Define the mapping of states to their respective classes
    WORKFLOW_MAP = {
        "AS": ASWorkflow,
        "DL": DLWorkflow,
        "GJ": GJWorkflow,
        "HR": HRWorkflow,
        "MH": MHWorkflow,
        "RJ": RJWorkflow,
        "UP": UPWorkflow,
        "WB": WBWorkflow,
    }

    @classmethod
    def run_state_workflow(cls, page, context):
        st_cd = context.st_cd
        
        # 2. Look up the class based on the state
        workflow_class = cls.WORKFLOW_MAP.get(st_cd)

        if workflow_class:
            # 3. Instantiate and run
            workflow_class(page, context=context).run()
        else:
            print(f"No workflow defined for state: {st_cd}")