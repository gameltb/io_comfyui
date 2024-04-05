from typing import Annotated

from ..blender_utils import pil_to_image
from ..comfy_script.runtime.nodes import *
from ..io_utils.image import ImageDataETNLoadImageBase64
from ..workflow import WorkFlowObject
from ..workflow_types import ComboWidget, FloatCFGType, FloatPercentageType, ImageType, IntSeedType, IntStepsType


class WorkFlow(WorkFlowObject):
    def execute(
        self,
        checkpoint: Annotated[str, ComboWidget(choices=[e.value for e in CheckpointLoaderSimple.ckpt_name])],
        positive: str = "1girl",
        negative: str = "text, watermark",
        control_net_hint: ImageType = None,
        control_net: Annotated[str, ComboWidget(choices=[e.value for e in ControlNetLoader.control_net_name])] = None,
        control_net_strength: FloatPercentageType = 1,
        width: int = 512,
        height: int = 512,
        batch_size: int = 1,
        steps: IntStepsType = 20,
        cfg: FloatCFGType = 5,
        seed: IntSeedType = 0,
        sampler_name: Annotated[str, ComboWidget(choices=[e.value for e in KSampler.sampler_name])] = None,
        scheduler: Annotated[str, ComboWidget(choices=[e.value for e in KSampler.scheduler])] = None,
    ):
        image_data = open(control_net_hint, "rb").read()
        control_net_hint_node = ImageDataETNLoadImageBase64(image_data)

        model, clip, vae = CheckpointLoaderSimple(checkpoint)
        conditioning = CLIPTextEncode(positive, clip)
        control_net_model = ControlNetLoader(control_net)
        image, _ = control_net_hint_node.comfy_script_load()
        conditioning = ControlNetApply(conditioning, control_net_model, image, control_net_strength)
        conditioning2 = CLIPTextEncode(negative, clip)
        latent = EmptyLatentImage(width, height, batch_size)
        latent = KSampler(model, seed, steps, cfg, sampler_name, scheduler, conditioning, conditioning2, latent, 1)
        image3 = VAEDecode(latent, vae)
        return (PreviewImage(image3),)

    def post_execute(self, results):
        out_images = results[0].wait()
        for i, out_image in enumerate(out_images):
            bpy_image = pil_to_image(out_image, f"control_net_output_{i}")
