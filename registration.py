import bpy

def register_menu_operator(menu: bpy.types.Menu, op: bpy.types.Operator):
    menu.layout.operator(op.bl_idname, text=op.bl_label, icon="TEXT")
