import importlib
import bpy

bl_info = {
    "name": "NukeTheBees",
    "blender": (5, 0, 0),
    "category": "Object",
}

from . import operators
from . import panels

if "bpy" in locals():
    importlib.reload(operators)
    importlib.reload(panels)

classes_to_register = (
    operators.PrintHelloOperator,
    panels.NPanel,
    panels.MenuBar
)

top_bar_menus = (
    panels.draw_menu_button,
)

def register():
    print(f"Loading module: {bl_info['name']}")
    for c in classes_to_register:
        print(f"Registering class: {c}")
        bpy.utils.register_class(c)

    for m in top_bar_menus:
        bpy.types.TOPBAR_MT_editor_menus.append(m)
    
def unregister():
    print(f"Unloading module: {bl_info['name']}")
    for c in classes_to_register:
        print(f"Unregistering class: {c}")
        bpy.utils.unregister_class(c)

    for m in top_bar_menus:
        bpy.types.TOPBAR_MT_editor_menus.remove(m)

if __name__ == "__main__":
    register()