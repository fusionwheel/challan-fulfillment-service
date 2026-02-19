from playwright.sync_api import Page
from .context import WorkflowContext
from typing import List, Type
import gc
class BaseWorkflow:
    steps: List[Type] = []

    def __init__(self, page: Page, context: WorkflowContext):
        self.page = page
        self.context = context

    def get_workflow_steps(self):
        return self.steps
    
    def run(self):
        for klass in self.get_workflow_steps():
            try:
                step = klass(self.page, ctx=self.context, **self.context.to_dict())
                step.proceed()
            finally:
                del step; gc.collect()
        #return self.context
    
    def dispose(self):
        if self.page:
            self.page.close()
            self.page = None
        if self.context:
            del self.context
            self.context = None