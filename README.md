# io_comfyui

Let Blender work with ComfyUI by ComfyScript.  
This addon is still in development.

![](asset/scr.png)

# Installation

## ComfyUI

You'll need an [ComfyUI](https://github.com/comfyanonymous/ComfyUI) installation, which can be local or remote.  
This addon currently requires ComfyUI to have the following nodes installed:

- [comfyui-tooling-nodes](https://github.com/Acly/comfyui-tooling-nodes)

## Blender

Install like other blender addon.  
Download [main.zip](https://github.com/gameltb/io_comfyui/archive/refs/heads/main.zip).  
It requires the installation of dependencies in the [requirements.txt](requirements.txt). I'm not sure what to do in the environment you're using.

# Usage

## Basic usage

You need to start comfyui first.  
Than set comfyui server address in addon preferences.  
Find `IO ComfyUI` panel at 3D view, Usually click the N key to toggle Show/Hide.  
Click the `Init ComfyScript` and select workflow.

## Make your own workflow

This addon base on [ComfyScript](https://github.com/Chaoses-Ib/ComfyScript), You can refer to it documentation to make your own workflow.  
example

- [controlnet](custom_workflows/controlnet.py)
- [simple_t2i](custom_workflows/simple_t2i.py)

New workflow can be save to custom_workflows/ like example.

## Use in blender script

```python
import bpy

import io_comfyui
from io_comfyui.blender_utils import image_to_pil, pil_to_image
from io_comfyui.comfy_script.runtime.nodes import *
from io_comfyui.workflow import WorkFlowObject


class WorkFlow(WorkFlowObject):
    def __init__(self) -> None:
        super().__init__()

    def execute(self):
        model, clip, _ = CheckpointLoaderSimple("majicmixRealistic_v6.safetensors")
        conditioning = CLIPTextEncode("1girl", clip)
        conditioning2 = CLIPTextEncode("text, watermark", clip)
        latent = EmptyLatentImage(512, 768, 1)
        latent = KSampler(model, 0, 20, 5.0, "euler_ancestral", "karras", conditioning, conditioning2, latent, 1.0)
        vae = VAELoader("vae-ft-mse-840000-ema-pruned.safetensors")
        image = VAEDecode(latent, vae)
        return (PreviewImage(image),)

    def post_execute(self, results):
        out_images = results[0].wait()
        for i, out_image in enumerate(out_images):
            bpy_image = pil_to_image(out_image, f"script_{i}")


w = WorkFlow()
io_comfyui.CUSTOM_WORKFLOW_OBJECT = w
bpy.ops.io_comfyui.run_workflow(use_custom_workflow_obj=True)
```
