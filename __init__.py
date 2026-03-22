import importlib
from types import ModuleType

import bpy

bl_info = {
    "name": "NukeTheBees",
    "blender": (5, 0, 0),
    "category": "Object",
}

from . import operators as ops
from . import panels
from . import registration
from . import key_mapping
from . import selection_utils
from . import orientation_utils

modules: tuple[ModuleType] = (
    ops, 
    panels, 
    registration,
    key_mapping,
    selection_utils,
    orientation_utils
)

if "bpy" in locals():
    for m in modules:
        importlib.reload(m)

classes_to_register = (
    ops.PrintHelloOperator,
    ops.UnrealExportMeshesOperator,
    ops.UnrealExportMeshesOperator.Settings,
    ops.DuplicateAroundCursorOperator,
    ops.DuplicateAroundCursorOperator.Settings,
    ops.AlignAroundCursorOperator,
    ops.AlignAroundCursorOperator.Settings,
    ops.ReloadScriptsOperator,
    panels.NPanel,
    panels.MenuBar
)

top_bar_menus = (
    panels.draw_menu_button,
)

def register():
    print(f"Loading module: {bl_info['name']}")
    
    print(f"Registering classes")
    for c in classes_to_register:
        print(f"    {c}")
        bpy.utils.register_class(c)

    for m in top_bar_menus:
        bpy.types.TOPBAR_MT_editor_menus.append(m)

    key_mapping.register_keys()

    bpy.types.Scene.unreal_export_meshes_settings = \
        bpy.props.PointerProperty(type=ops.UnrealExportMeshesOperator.Settings)
    bpy.types.Scene.duplicate_around_cursor_settings = \
        bpy.props.PointerProperty(type=ops.DuplicateAroundCursorOperator.Settings)
    bpy.types.Scene.align_around_cursor_settings = \
        bpy.props.PointerProperty(type=ops.AlignAroundCursorOperator.Settings)
    
def unregister():
    print(f"Unloading module: {bl_info['name']}")

    print(f"Unregistering classes")
    for c in classes_to_register:
        print(f"    {c}")
        bpy.utils.unregister_class(c)

    for m in top_bar_menus:
        bpy.types.TOPBAR_MT_editor_menus.remove(m)

    key_mapping.unregister_keys()

    del bpy.types.Scene.unreal_export_meshes_settings
    del bpy.types.Scene.duplicate_around_cursor_settings
    del bpy.types.Scene.align_around_cursor_settings

if __name__ == "__main__":
    register()