import base64


class ImageData:
    def comfy_script_load(self) -> tuple["Image", "Mask"]:
        raise NotImplementedError()


class ImageDataComfyUILoadInput(ImageData):
    def __init__(self, image_name) -> None:
        self.image_name = image_name

    def comfy_script_load(self) -> tuple["Image", "Mask"]:
        from ..comfy_script.runtime.nodes import LoadImage

        return LoadImage(self.image_name)


class ImageDataETNLoadImageBase64(ImageData):
    def __init__(self, image_data: bytes) -> None:
        self.image_data = image_data

    def comfy_script_load(self) -> tuple["Image", "Mask"]:
        from ..comfy_script.runtime.nodes import ETNLoadImageBase64
        
        return ETNLoadImageBase64(base64.standard_b64encode(self.image_data).decode())
