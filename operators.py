import bpy

class PrintHelloOperator(bpy.types.Operator):
    bl_idname = "ntb.print_hello"
    bl_label = "Print Hello"

    def execute(self, context):
        print("Hello, world!")
        return {'FINISHED'}