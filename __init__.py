import importlib
from types import ModuleType

import bpy

bl_info = {
    "name": "NukeTheBees",
    "blender": (5, 0, 0),
    "category": "Object",
}

from . import operators
from . import panels
from . import registration
from . import key_mapping

modules: tuple[ModuleType] = (
    operators, 
    panels, 
    registration,
    key_mapping,
)

if "bpy" in locals():
    for m in modules:
        importlib.reload(m)

classes_to_register = (
    operators.PrintHelloOperator,
    operators.UnrealExportAllMeshesSeparatelyOperator,
    operators.UnrealExportAllMeshesAsOneOperator,
    operators.ReloadScriptsOperator,
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
    
def unregister():
    print(f"Unloading module: {bl_info['name']}")

    print(f"Unregistering classes")
    for c in classes_to_register:
        print(f"    {c}")
        bpy.utils.unregister_class(c)

    for m in top_bar_menus:
        bpy.types.TOPBAR_MT_editor_menus.remove(m)

    key_mapping.unregister_keys()

if __name__ == "__main__":
    register()