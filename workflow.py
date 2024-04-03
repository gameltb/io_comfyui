from .comfy_script.runtime import load


def init_comfy_script(
    comfyui: str = None, args=None, vars: dict | None = None, watch: bool = True, save_script_source: bool = True
):
    load(comfyui)

