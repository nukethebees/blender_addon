import bpy

def register_menu_operator(layout: bpy.types.UILayout, 
                           op: bpy.types.Operator
                           ) -> bpy.types.OperatorProperties:
    return layout.operator(op.bl_idname, text=op.bl_label)
