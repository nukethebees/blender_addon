import os
from pathlib import Path

import bpy

class PrintHelloOperator(bpy.types.Operator):
    bl_idname = "ntb.print_hello"
    bl_label = "Print Hello"

    def execute(self, context: bpy.types.Context):
        print("Hello, world!")
        return {'FINISHED'}
    
class ReloadScriptsOperator(bpy.types.Operator):
    bl_idname = "ntb.reload_scripts"
    bl_label = "Reload Scripts"

    def execute(self, context: bpy.types.Context):
        bpy.ops.script.reload()
        return {'FINISHED'}

def get_export_dir() -> str:
    blend_file_path = bpy.data.filepath
    blend_dir = os.path.dirname(blend_file_path)
    os.makedirs(blend_dir, exist_ok=True)
    return blend_dir

def make_combined_sm_name() -> str:
    blend_name = Path(bpy.data.filepath).stem
    return f"SM_{blend_name}.fbx"

def get_all_meshes(context: bpy.types.Context) -> list[bpy.types.Object]:
    return [obj for obj in context.scene.objects if obj.type == 'MESH']

class UnrealExportAllMeshesSeparatelyOperator(bpy.types.Operator):
    bl_idname = "ntb.unreal_export_all_meshes_separately"
    bl_label = "Unreal Export All Meshes Separately"

    def execute(self, context: bpy.types.Context):       
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

    
class UnrealExportAllMeshesAsOneOperator(bpy.types.Operator):
    bl_idname = "ntb.unreal_export_all_meshes_as_one"
    bl_label = "Unreal Export All Meshes As One"

    def execute(self, context: bpy.types.Context):       
        folder = get_export_dir()
        file_name = make_combined_sm_name()
        file_path = os.path.join(folder, file_name)

        bpy.ops.object.select_all(action='DESELECT')
        mesh_objects = get_all_meshes(context)
        for obj in mesh_objects:
            obj.select_set(True)

        bpy.ops.export_scene.fbx(
            filepath=file_path,
            apply_unit_scale=True,
            object_types={'MESH'},
            axis_forward='X',
            axis_up='Z',
            mesh_smooth_type='SMOOTH_GROUP'
        )

        self.report({'INFO'}, f"Exported {len(context.selected_objects)} objects to FBX")
        return {'FINISHED'}