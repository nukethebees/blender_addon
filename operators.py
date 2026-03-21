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

def make_fbx_name(x:str) -> str:
    return f"SM_{x}.fbx"

def make_combined_sm_name() -> str:
    blend_name = Path(bpy.data.filepath).stem
    return make_fbx_name(blend_name)

def get_all_meshes(context: bpy.types.Context) -> list[bpy.types.Object]:
    return [obj for obj in context.scene.objects if obj.type == 'MESH']

def unselect_all() -> None:
    bpy.ops.object.select_all(action='DESELECT')

def select_all_meshes_only(context: bpy.types.Context
                           ) -> list[bpy.types.Object]:
    unselect_all()
    mesh_objects = get_all_meshes(context)
    for obj in mesh_objects:
        obj.select_set(True)
    return mesh_objects

def select_only(obj: bpy.types.Object) -> None:
    unselect_all()
    obj.select_set(True)

class UnrealExportMeshesOperator(bpy.types.Operator):
    bl_idname = "ntb.unreal_export_meshes"
    bl_label = "Unreal Export Meshes"
    bl_options = {'REGISTER', 'UNDO'}

    class Settings(bpy.types.PropertyGroup):
        mesh_mode: bpy.props.EnumProperty(
            name="Mesh Mode",
            description="Mesh combining mode",
            items=[
                ('Combine', "Combine", "Combine meshes as one"),
                ('Separate', "Separate", "Export meshes separately"),
            ],
            default='Combine'
        ) # type: ignore

    def init_class_members(self) -> None:
        self.empty_scales = {}
        self.to_remove = []

    def shrink_empty_scales(self, context) -> None:
        self.empty_scales = {}
        for obj in context.scene.objects:
            if obj.type == 'EMPTY':
                self.empty_scales[obj.name] = obj.scale.copy()
                obj.scale = (0.01, 0.01, 0.01)  # shrink to tiny size for Unreal

    def restore_empty_scales(self) -> None:
        for name, scale in self.empty_scales.items():
            bpy.data.objects[name].scale = scale

    def export_cleanup(self) -> None:
        self.restore_empty_scales()

        for obj in self.to_remove:
            bpy.data.objects.remove(obj, do_unlink=True)

    def create_union(self, context) -> None:
        bpy.ops.object.duplicate()

        dupes = []
        for obj in context.selected_objects:
            obj.name = f"UnionTemp_{obj.name}"
            dupes.append(obj)      

        # Boolean union them
        base = dupes[0]
        bpy.context.view_layer.objects.active = base

        for obj in dupes[1:]:
            mod = base.modifiers.new(name=f"Union_{obj.name}", type='BOOLEAN')
            mod.operation = 'UNION'
            mod.object = obj
            bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(obj, do_unlink=True)

        # Export the combined union mesh
        select_only(base)

        self.to_remove.append(base)

    def execute(self, context: bpy.types.Context):
        self.init_class_members()

        props: UnrealExportMeshesOperator.Settings = context.scene.unreal_export_meshes_settings
        folder = get_export_dir()

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        def get_file_path(file_name:str) -> str:
            return os.path.join(folder, file_name)
        def run_fbx_export(file_path: str):
            self.shrink_empty_scales(context)

            try:
                bpy.ops.export_scene.fbx(
                    filepath=file_path,
                    apply_unit_scale=True,
                    object_types={'MESH', 'EMPTY'},
                    axis_forward='X',
                    axis_up='Z',
                    mesh_smooth_type='SMOOTH_GROUP',
                    use_selection=True
                )
            except:
                pass
            
            self.export_cleanup()
       
        def export_mesh_to_fbx(name:str) -> None:
            file_name = make_fbx_name(name)
            file_path = get_file_path(file_name)
            run_fbx_export(file_path)

        if (props.mesh_mode == "Combine"): 
            select_all_meshes_only(context)
            export_mesh_to_fbx(Path(bpy.data.filepath).stem)
            self.report({'INFO'}, f"Exported to FBX")
        else:
            n_exported = 0
            for obj in get_all_meshes(context):
                select_only(obj)
                export_mesh_to_fbx(obj.name)
                n_exported += 1

            self.report({'INFO'}, f"Exported {n_exported} objects to FBX")
        unselect_all()
        return {'FINISHED'}