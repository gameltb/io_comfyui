import inspect
from typing import Annotated

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty, StringProperty

from .workflow_types import (
    BoolWidget,
    ComboWidget,
    ComfyWidgetType,
    FloatWidget,
    IntWidget,
    StringWidget,
    find_comfy_widget_type_annotation,
)


class BlenderObjectWidget(ComfyWidgetType):
    TYPE = "BLENDER_OBJECT"

    @property
    def blender_annotation(self):
        return PointerProperty(type=bpy.types.Object)


BlenderObjectType = Annotated[bpy.types.Object, BlenderObjectWidget()]


TYPE_MAP = {
    int: IntWidget(),
    float: FloatWidget(),
    bool: BoolWidget(),
    str: StringWidget(),
}


def gen_blender_annotations(func):
    sig = inspect.signature(func)
    annotations = {}
    for k, v in sig.parameters.items():
        comfy_widget = None
        try:
            if v.annotation in TYPE_MAP:
                comfy_widget = TYPE_MAP[v.annotation]
        except TypeError:
            pass

        if comfy_widget is None:
            comfy_widget = find_comfy_widget_type_annotation(v.annotation)

        if comfy_widget is None:
            continue

        value_default = None
        if v.default is not inspect._empty:
            value_default = v.default

        tp = comfy_widget.TYPE

        annotation = None
        if hasattr(comfy_widget, "blender_annotation"):
            annotation = comfy_widget.blender_annotation
        elif isinstance(comfy_widget, IntWidget):
            default = value_default if value_default is not None else 0
            annotation = IntProperty(
                name=k,
                step=comfy_widget.step if comfy_widget.step is not None else 1,
                min=comfy_widget.min if comfy_widget.min is not None else 0,
                max=comfy_widget.max if comfy_widget.max is not None and comfy_widget.max < 2**31 - 1 else 2**31 - 1,
                default=default,
            )
        elif isinstance(comfy_widget, FloatWidget):
            default = value_default if value_default is not None else 0
            annotation = FloatProperty(
                name=k,
                step=comfy_widget.step if comfy_widget.step is not None else 0.1,
                min=comfy_widget.min if comfy_widget.min is not None else 0,
                max=comfy_widget.max if comfy_widget.max is not None else 3.402823e38,
                default=default,
            )
        elif isinstance(comfy_widget, BoolWidget):
            default = value_default if value_default is not None else False
            annotation = BoolProperty(
                name=k,
                default=default,
            )
        elif isinstance(comfy_widget, StringWidget):
            default = value_default if value_default is not None else ""
            annotation = StringProperty(
                name=k,
                default=default,
            )
        elif isinstance(comfy_widget, ComboWidget):
            annotation = EnumProperty(
                name=k,
                items=[(key, key, "") for key in comfy_widget.type],
            )
        elif tp == "IMAGE":
            annotation = StringProperty(
                name=k,
                subtype="FILE_PATH",
            )

        if annotation is None:
            continue

        annotations[k] = annotation
    return annotations
