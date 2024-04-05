import importlib
import os
import traceback

from .comfy_script.runtime import Workflow, load

WORKFLOW_MAP = {}

BASE_DIR = os.path.dirname(__file__)


class WorkFlowObject:
    """Generic parent."""

    def __init__(self) -> None:
        self.workflow = None
        self.results = None

    def pre_execute(self, kwargs):
        """Processing parameters"""
        pass

    def execute(self, **kwargs):
        """WorkFlow."""
        pass

    def post_execute(self, results):
        """Process the results."""
        pass


def init_comfy_script(comfyui: str = None):
    load(comfyui)

    workflow_dir = os.path.join(BASE_DIR, "custom_workflows")
    for file_name in os.listdir(workflow_dir):
        try:
            base_name, ext = os.path.splitext(file_name)
            if ext == ".py":
                module = importlib.import_module(f".custom_workflows.{base_name}", package=__package__)
                WORKFLOW_MAP[base_name] = module.WorkFlow
        except Exception:
            traceback.print_exc()


def run_workflow(workflow: WorkFlowObject, *arg, **kwargs):
    wf = Workflow()
    with wf:
        result = workflow.execute(*arg, **kwargs)
    workflow.workflow = wf
    workflow.results = result
    return wf, result
