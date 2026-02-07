import bpy

class PrintHelloOperator(bpy.types.Operator):
    bl_idname = "ntb.print_hello"
    bl_label = "Print Hello"

    def execute(self, context):
        print("Hello, world!")
        return {'FINISHED'}
    
class ReloadScriptsOperator(bpy.types.Operator):
    bl_idname = "ntb.reload_scripts"
    bl_label = "Reload Scripts"

    def execute(self, context):
        bpy.ops.script.reload()
        return {'FINISHED'}

class ExportUnrealOperator(bpy.types.Operator):
    bl_idname = "ntb.export_unreal"
    bl_label = "Export Unreal"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, "Filepath not set")
            return {'CANCELLED'}

        return {'FINISHED'}