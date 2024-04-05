from typing import Annotated

from ..blender_utils import pil_to_image
from ..comfy_script.runtime.nodes import *
from ..workflow import WorkFlowObject
from ..workflow_types import ComboWidget, FloatCFGType, IntSeedType, IntStepsType


class WorkFlow(WorkFlowObject):
    def execute(
        self,
        checkpoint: Annotated[str, ComboWidget(choices=[e.value for e in CheckpointLoaderSimple.ckpt_name])],
        positive: str = "1girl",
        negative: str = "text, watermark",
        width: int = 512,
        height: int = 512,
        batch_size: int = 1,
        steps: IntStepsType = 20,
        cfg: FloatCFGType = 5,
        seed: IntSeedType = 0,
        sampler_name: Annotated[str, ComboWidget(choices=[e.value for e in KSampler.sampler_name])] = None,
        scheduler: Annotated[str, ComboWidget(choices=[e.value for e in KSampler.scheduler])] = None,
    ):
        model, clip, _ = CheckpointLoaderSimple(checkpoint)
        conditioning = CLIPTextEncode(positive, clip)
        conditioning2 = CLIPTextEncode(negative, clip)
        latent = EmptyLatentImage(width, height, batch_size)
        latent = KSampler(model, seed, steps, cfg, sampler_name, scheduler, conditioning, conditioning2, latent, 1)
        vae = VAELoader("vae-ft-mse-840000-ema-pruned.safetensors")
        image = VAEDecode(latent, vae)
        PreviewImage(image)
        return (PreviewImage(image),)

    def post_execute(self, results):
        out_images = results[0].wait()
        for i, out_image in enumerate(out_images):
            bpy_image = pil_to_image(out_image, f"simple_t2i_{i}")
