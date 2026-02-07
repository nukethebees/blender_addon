from dataclasses import dataclass
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

modules: tuple[ModuleType] = (
    operators, 
    panels, 
    registration,
)

if "bpy" in locals():
    for m in modules:
        importlib.reload(m)

classes_to_register = (
    operators.PrintHelloOperator,
    operators.UnrealExportAllMeshesSeparatelyOperator,
    operators.ReloadScriptsOperator,
    panels.NPanel,
    panels.MenuBar
)

top_bar_menus = (
    panels.draw_menu_button,
)

@dataclass
class KeyDef:
    map: bpy.types.KeyMap
    item: bpy.types.KeyMapItem

old_keys: list[bpy.types.KeyMapItem] = []
addon_keymap: list[KeyDef] = []

def register_keys():
    global old_keys, addon_keymap

    print("Registering keys")

    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='Window', space_type='EMPTY')

    old_keys = [kmi for kmi in km.keymap_items if kmi.type == 'F5']
    
    kmi = km.keymap_items.new('ntb.reload_scripts', 'F5', 'PRESS')
    addon_keymap.append(KeyDef(km, kmi))

def unregister_keys():
    global old_keys, addon_keymap

    print("Unregistering keys")    

    for key_def in addon_keymap:
        key_def.map.keymap_items.remove(key_def.item)
    addon_keymap.clear()

    for kmi in old_keys:
        kmi.active = True

def register():
    print(f"Loading module: {bl_info['name']}")
    
    print(f"Registering classes")
    for c in classes_to_register:
        print(f"    {c}")
        bpy.utils.register_class(c)

    for m in top_bar_menus:
        bpy.types.TOPBAR_MT_editor_menus.append(m)

    register_keys()
    
def unregister():
    print(f"Unloading module: {bl_info['name']}")

    print(f"Unregistering classes")
    for c in classes_to_register:
        print(f"    {c}")
        bpy.utils.unregister_class(c)

    for m in top_bar_menus:
        bpy.types.TOPBAR_MT_editor_menus.remove(m)

    unregister_keys()

if __name__ == "__main__":
    register()