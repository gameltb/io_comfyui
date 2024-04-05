from typing import Set

import bpy
from bpy.props import EnumProperty, FloatProperty, PointerProperty, StringProperty
from bpy.types import AddonPreferences, Context, Event, Operator, Panel, PropertyGroup

from .blender_types import gen_blender_annotations
from .workflow import WORKFLOW_MAP, init_comfy_script, run_workflow

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

    comfyui_server_address: StringProperty(
        default="http://127.0.0.1:8188/", name="Comfyui Server Address", description="ComfyUI service address."
    )

    def draw(self, context):
        self.layout.row(align=True).prop(self, "page", expand=True)
        box = self.layout.box()
        row = box.row()
        row.prop(self, "comfyui_server_address")


def get_preferences():
    return bpy.context.preferences.addons[__package__].preferences


WORKFLOW_ARGS_CLS = None


def update_workflow_property_group(self, context):
    global WORKFLOW_ARGS_CLS
    if context is None:
        return
    workflow_name = context.scene.io_comfyui.workflow_name
    if hasattr(bpy.types.Scene, "io_comfyui_workflow_args"):
        pass
    if not hasattr(bpy.types.Scene, "io_comfyui_workflow_args"):
        annotations = gen_blender_annotations(WORKFLOW_MAP[workflow_name].execute)
        data = {
            "bl_label": "IO ComfyUI workflow args",
            "bl_idname": "io_comfyui.workflow_args",
            "__annotations__": annotations,
        }

        WORKFLOW_ARGS_CLS = type("IOComfyUISceneWorkflowArgsProperties", (bpy.types.PropertyGroup,), data)

        bpy.utils.register_class(WORKFLOW_ARGS_CLS)

        bpy.types.Scene.io_comfyui_workflow_args = bpy.props.PointerProperty(type=WORKFLOW_ARGS_CLS)


def remove_workflow_property_group(self, context):
    if WORKFLOW_ARGS_CLS is not None:
        bpy.utils.unregister_class(WORKFLOW_ARGS_CLS)
    if hasattr(bpy.types.Scene, "io_comfyui_workflow_args"):
        del bpy.types.Scene.io_comfyui_workflow_args


class IOComfyUISceneProperties(PropertyGroup):
    workflow_name: EnumProperty(
        name="Workflow Name",
        description="Workflow Name",
        items=lambda scene, context: [(key, key, "") for key in WORKFLOW_MAP],
        update=update_workflow_property_group,
    )

    workflow_progress: FloatProperty()


class IOComfyUIMainPanel(Panel):
    bl_idname = "OBJECT_PT_IOComfyUIMain"
    bl_label = "IO ComfyUI"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "IO ComfyUI"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        subrow = layout.row()
        subsubrow = subrow.row(align=True)
        subsubrow.operator("io_comfyui.init", text="Init ComfyScript")

        subrow = layout.row()
        subsubrow = subrow.row(align=True)
        subsubrow.prop(scene.io_comfyui, "workflow_name", text="workflow")

        if hasattr(bpy.types.Scene, "io_comfyui_workflow_args"):
            box = layout.box()
            for item_key in WORKFLOW_ARGS_CLS.__annotations__:
                row = box.row()
                row.prop(scene.io_comfyui_workflow_args, item_key)

        subrow = layout.row()
        subsubrow = subrow.row(align=True)
        subsubrow.operator("io_comfyui.run_workflow", text="Run Workflow")

        if scene.io_comfyui.workflow_progress != 0:
            row = layout.row()
            row.progress(
                factor=scene.io_comfyui.workflow_progress,
                type="BAR",
                text="Workflow in progress..." if scene.io_comfyui.workflow_progress < 1 else "Workflow Finished !",
            )


class IOComfyUIInit(Operator):
    bl_idname = "io_comfyui.init"
    bl_label = "IO ComfyUI Init"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        init_comfy_script(get_preferences().comfyui_server_address)
        update_workflow_property_group(None, context)
        return {"FINISHED"}


class IOComfyUIRunWorkFlow(Operator):
    bl_idname = "io_comfyui.run_workflow"
    bl_label = "IO ComfyUI Run Workflow"

    workflow_name: StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        run_workflow_name = None
        if hasattr(self, "workflow_name"):
            workflow_name = str(self.workflow_name).strip()
            if len(workflow_name) > 0:
                run_workflow_name = workflow_name

        if run_workflow_name is None:
            workflow_name = str(context.scene.io_comfyui.workflow_name).strip()
            if len(workflow_name) > 0:
                run_workflow_name = workflow_name

        if run_workflow_name is not None:
            workflow_object = WORKFLOW_MAP[run_workflow_name]()
            workflow_kwargs = {}
            if hasattr(bpy.types.Scene, "io_comfyui_workflow_args"):
                for item_key in WORKFLOW_ARGS_CLS.__annotations__:
                    workflow_kwargs[item_key] = getattr(context.scene.io_comfyui_workflow_args, item_key)
                    item = WORKFLOW_ARGS_CLS.__annotations__[item_key]
                    if item.keywords.get("subtype", None) == "FILE_PATH":
                        workflow_kwargs[item_key] = bpy.path.abspath(workflow_kwargs[item_key])
            self.working_workflow = (*run_workflow(workflow_object, **workflow_kwargs), workflow_object)

        wm = context.window_manager
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context: Context, event: Event) -> Set[str] | Set[int]:
        if self.working_workflow[0].task.set_result_flag:
            self.working_workflow[0].task.wait()
            # task.done not update if no task.wait :(
            if self.working_workflow[0].task.done():
                context.scene.io_comfyui.workflow_progress = 0

                self.working_workflow[-1].post_execute(self.working_workflow[1])

                return {"FINISHED"}
        if event.type in {"ESC"}:
            # TODO: Cancel
            # return {"CANCELLED"}
            pass

        context.scene.io_comfyui.workflow_progress = 0.5

        return {"PASS_THROUGH"}


classes = (IOComfyUIMainPanel, IOComfyUIInit, IOComfyUIMainPreference, IOComfyUIRunWorkFlow, IOComfyUISceneProperties)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.io_comfyui = PointerProperty(type=IOComfyUISceneProperties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.io_comfyui
    remove_workflow_property_group(None, None)


if __name__ == "__main__":
    register()
