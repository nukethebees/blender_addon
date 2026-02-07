import os

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

def get_export_dir() -> str:
    blend_file_path = bpy.data.filepath
    blend_dir = os.path.dirname(blend_file_path)
    os.makedirs(blend_dir, exist_ok=True)
    return blend_dir

class UnrealExportAllMeshesSeparatelyOperator(bpy.types.Operator):
    bl_idname = "ntb.unreal_export_all_meshes_separately"
    bl_label = "Unreal Export All Meshes Separately"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):       
        folder = get_export_dir()

        for obj in context.scene.objects:
            if obj.type != 'MESH':
                continue

            # Prefix name with SM_
            filename = "SM_" + obj.name + ".fbx"
            full_path = os.path.join(folder, filename)

            # Export FBX
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.ops.export_scene.fbx(
                filepath=full_path,
                apply_unit_scale=True,
                object_types={'MESH'},
                axis_forward='X',      
                axis_up='Z',           
                mesh_smooth_type='SMOOTH_GROUP'
            )

        self.report({'INFO'}, f"Exported {len(context.selected_objects)} objects to FBX")
        return {'FINISHED'}