from dataclasses import dataclass

import bpy

from . import operators as ops

@dataclass
class KeyDef:
    map: bpy.types.KeyMap
    item: bpy.types.KeyMapItem

old_keys: list[bpy.types.KeyMapItem] = []
addon_keymap: list[KeyDef] = []

def add_operator_shortcut(km: bpy.types.KeyMap, 
                          op: bpy.types.Operator,
                          key: str,
                          value='PRESS',
                          **kwargs) -> bpy.types.KeyMapItem:
    return km.keymap_items.new(op.bl_idname, key, value, **kwargs)

def register_keys():
    global old_keys, addon_keymap

    print("Registering keys")

    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='Window', space_type='EMPTY')

    old_keys = [kmi for kmi in km.keymap_items if kmi.type == 'F5']
    
    kmi = add_operator_shortcut(km, ops.ReloadScriptsOperator, 'F5')

    addon_keymap.append(KeyDef(km, kmi))

def unregister_keys():
    global old_keys, addon_keymap

    print("Unregistering keys")    

    for key_def in addon_keymap:
        key_def.map.keymap_items.remove(key_def.item)
    addon_keymap.clear()

    for kmi in old_keys:
        kmi.active = True