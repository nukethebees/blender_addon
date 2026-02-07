import bpy

def register_menu_operator(menu: bpy.types.Menu, 
                           op: bpy.types.Operator
                           ) -> bpy.types.OperatorProperties:
    return menu.layout.operator(op.bl_idname, text=op.bl_label)
