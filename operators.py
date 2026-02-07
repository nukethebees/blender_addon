import bpy

class PrintHelloOperator(bpy.types.Operator):
    bl_idname = "ntb.print_hello"
    bl_label = "Print Hello"

    def execute(self, context):
        print("Hello, world!")
        return {'FINISHED'}
    
class ExportUnrealOperator(bpy.types.Operator):
    bl_idname = "ntb.export_unreal"
    bl_label = "Export Unreal"

    def execute(self, context):
        return {'FINISHED'}