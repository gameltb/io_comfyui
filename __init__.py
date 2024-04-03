import bpy
from bpy.types import AddonPreferences, Operator, Panel

from .workflow import init_comfy_script

bl_info = {
    "name": "IO ComfyUI",
    "author": "gamegccltb",
    "version": (0, 1, 0),
    "blender": (4, 1, 0),
    "location": "",
    "description": "Let Blender work with ComfyUI by ComfyScript.",
    "warning": "This addon is still in development.",
    "wiki_url": "",
    # "support": "TESTING",
    "category": "Material",
}


class IOComfyUIMainPreference(AddonPreferences):
    bl_idname = __package__

    comfyui_server_address: bpy.props.StringProperty(
        default="http://127.0.0.1:8188/", name="Comfyui Server Address", description="ComfyUI service address."
    )

    def draw(self, context):
        self.layout.row(align=True).prop(self, "page", expand=True)
        box = self.layout.box()
        row = box.row()
        row.prop(self, "comfyui_server_address")


def get_preferences():
    return bpy.context.preferences.addons[__package__].preferences


class IOComfyUIMainPanel(Panel):
    bl_idname = "OBJECT_PT_IOComfyUIMain"
    bl_label = "IO ComfyUI"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "IO ComfyUI"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        flow = row.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=False)
        subrow = flow.row()
        subsubrow = subrow.row(align=True)
        subsubrow.operator("io_comfyui.init", text="Init ComfyScript")


class IOComfyUIInit(Operator):
    bl_idname = "io_comfyui.init"
    bl_label = "IO ComfyUI Init"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        init_comfy_script(get_preferences().comfyui_server_address)
        return {"FINISHED"}


classes = (IOComfyUIMainPanel, IOComfyUIInit, IOComfyUIMainPreference)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
