from typing import Set

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, PointerProperty, StringProperty
from bpy.types import AddonPreferences, Context, Event, Operator, Panel, PropertyGroup

from .blender_types import gen_blender_annotations
from .workflow import WORKFLOW_MAP, WorkFlowObject, init_comfy_script, run_workflow, wait_for_workflow

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
        self.layout.row(align=True)
        box = self.layout.box()
        row = box.row()
        row.prop(self, "comfyui_server_address")


def get_preferences():
    return bpy.context.preferences.addons[__package__].preferences


WORKFLOW_ARGS_CLS = None


def get_property_group_kwargs(ins, cls):
    property_group_kwargs = {}
    for item_key in cls.__annotations__:
        property_group_kwargs[item_key] = getattr(ins, item_key)
        item = cls.__annotations__[item_key]
        if item.keywords.get("subtype", None) == "FILE_PATH":
            property_group_kwargs[item_key] = bpy.path.abspath(property_group_kwargs[item_key])
    return property_group_kwargs


def update_workflow_property_group(self, context):
    global WORKFLOW_ARGS_CLS
    if context is None:
        return
    workflow_name = context.scene.io_comfyui.workflow_name
    if hasattr(bpy.types.Scene, "io_comfyui_workflow_args"):
        remove_workflow_property_group(self, context)

    annotations = gen_blender_annotations(WORKFLOW_MAP[workflow_name])
    data = {
        "bl_label": "IO ComfyUI workflow init args",
        "bl_idname": "io_comfyui.workflow_init_args",
        "__annotations__": annotations,
    }

    workflow_init_args_cls = type("IOComfyUISceneWorkflowInitArgsProperties", (bpy.types.PropertyGroup,), data)

    annotations = gen_blender_annotations(WORKFLOW_MAP[workflow_name].execute)
    data = {
        "bl_label": "IO ComfyUI workflow execute args",
        "bl_idname": "io_comfyui.workflow_execute_args",
        "__annotations__": annotations,
    }

    workflow_execute_args_cls = type("IOComfyUISceneWorkflowExecuteArgsProperties", (bpy.types.PropertyGroup,), data)

    class IOComfyUISceneWorkflowArgsProperties(bpy.types.PropertyGroup):
        bl_label = "IO ComfyUI workflow args"
        bl_idname = "io_comfyui.workflow_args"

        workflow_init_args: PointerProperty(type=workflow_init_args_cls)
        workflow_execute_args: PointerProperty(type=workflow_execute_args_cls)

    WORKFLOW_ARGS_CLS = (IOComfyUISceneWorkflowArgsProperties, workflow_init_args_cls, workflow_execute_args_cls)
    for cls in reversed(WORKFLOW_ARGS_CLS):
        bpy.utils.register_class(cls)

    bpy.types.Scene.io_comfyui_workflow_args = bpy.props.PointerProperty(type=IOComfyUISceneWorkflowArgsProperties)


def remove_workflow_property_group(self, context):
    if WORKFLOW_ARGS_CLS is not None:
        for cls in WORKFLOW_ARGS_CLS:
            bpy.utils.unregister_class(cls)
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
            for item_key in WORKFLOW_ARGS_CLS[1].__annotations__:
                row = box.row()
                row.prop(scene.io_comfyui_workflow_args.workflow_init_args, item_key)
            for item_key in WORKFLOW_ARGS_CLS[2].__annotations__:
                row = box.row()
                row.prop(scene.io_comfyui_workflow_args.workflow_execute_args, item_key)

        subrow = layout.row()
        subsubrow = subrow.row(align=True)
        subsubrow.operator("io_comfyui.run_workflow", text="Run Workflow").use_custom_workflow_obj = False

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


CUSTOM_WORKFLOW_OBJECT = None


class IOComfyUIRunWorkFlow(Operator):
    bl_idname = "io_comfyui.run_workflow"
    bl_label = "IO ComfyUI Run Workflow"

    use_custom_workflow_obj: BoolProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        workflow_object: WorkFlowObject = None
        workflow_kwargs = {}
        if hasattr(self, "use_custom_workflow_obj") and self.use_custom_workflow_obj:
            if CUSTOM_WORKFLOW_OBJECT is not None:
                workflow_object = CUSTOM_WORKFLOW_OBJECT

        if workflow_object is None:
            workflow_name = str(context.scene.io_comfyui.workflow_name).strip()
            if len(workflow_name) > 0:
                run_workflow_name = workflow_name
                workflow_init_kwargs = {}
                if hasattr(bpy.types.Scene, "io_comfyui_workflow_args"):
                    workflow_init_kwargs = get_property_group_kwargs(
                        context.scene.io_comfyui_workflow_args.workflow_init_args, WORKFLOW_ARGS_CLS[1]
                    )

                workflow_object = WORKFLOW_MAP[run_workflow_name](**workflow_init_kwargs)

                if hasattr(bpy.types.Scene, "io_comfyui_workflow_args"):
                    workflow_kwargs = get_property_group_kwargs(
                        context.scene.io_comfyui_workflow_args.workflow_execute_args, WORKFLOW_ARGS_CLS[2]
                    )

        if workflow_object is not None:
            workflow_kwargs = workflow_object.pre_execute(workflow_kwargs)
            run_workflow(workflow_object, **workflow_kwargs)
            self.working_workflow = workflow_object
        else:
            return {"CANCELLED"}

        wm = context.window_manager
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context: Context, event: Event) -> Set[str] | Set[int]:
        wait_for_workflow(self.working_workflow)
        if self.working_workflow.workflow.task.done():
            context.scene.io_comfyui.workflow_progress = 0

            self.working_workflow.post_execute(self.working_workflow.results)

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
