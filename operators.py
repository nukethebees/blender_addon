import math
import os
from pathlib import Path
from typing import cast

import bpy
import mathutils

from .selection_utils import *

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
                select_hierarchy(obj)
                export_mesh_to_fbx(obj.name)
                n_exported += 1

            self.report({'INFO'}, f"Exported {n_exported} objects to FBX")
        unselect_all()
        return {'FINISHED'}
    
class DuplicateAroundCursorOperator(bpy.types.Operator):
    bl_idname = "ntb.duplicate_around_cursor"
    bl_label = "Duplicate around cursor"
    bl_options = {'REGISTER', 'UNDO'}

    class Settings(bpy.types.PropertyGroup):
        count: bpy.props.IntProperty(
            name="count",
            default=8,
            min=1,
            description="Number of duplicates"
        ) # type: ignore
        radius: bpy.props.FloatProperty(
            name="radius",
            default=2.0,
            min=0.0,
            description="Radius of the circle"
        ) # type: ignore
        apply_transforms: bpy.props.BoolProperty(
            name="apply_transforms",
            default=False,
            description="Apply transforms"
        ) # type: ignore
        orientation: bpy.props.EnumProperty(
            name="orientation",
            description="Copy orientation",
            items=[
                ('Source', "Source", "Same as source object"),
                ('CentreXY', "CentreXY", "Towards centre object"),
            ],
            default='CentreXY'
        ) # type: ignore

    def execute(self, context: bpy.types.Context):
        n_selected_objects = len(context.selected_objects)
        if n_selected_objects != 1:
            self.report({'WARNING'}, f"{n_selected_objects} selected objects. Only 1 allowed")
            return {'CANCELLED'}

        obj = context.selected_objects[0]
        if obj is None:
            self.report({'WARNING'}, "Object is none")
            return {'CANCELLED'}         
        
        props = cast(UnrealExportMeshesOperator.Settings, context.scene.duplicate_around_cursor_settings)
        count = cast(int, props.count)
        radius = cast(float, props.radius)

        created_objects: list[bpy.types.Object] = []
        cursor = context.scene.cursor.location
        angle_step = 2 * math.pi / count

        for i in range(count):
            angle = i * angle_step
            pos = mathutils.Vector((
                cursor.x + radius * math.cos(angle),
                cursor.y + radius * math.sin(angle),
                cursor.z
            ))

            new_obj = obj.copy()
            if obj.data is not None:
                new_obj.data = obj.data.copy()
            new_obj.location = pos
            new_obj.name = f"{obj.name}_{i}"

            if props.orientation == "CentreXY":
                direction = (cursor - pos).normalized()
                rot = direction.to_track_quat('Z', 'Y')  # Z forward, Y up
                new_obj.rotation_euler = rot.to_euler()

            context.collection.objects.link(new_obj)
            created_objects.append(new_obj)

        if props.apply_transforms:
            bpy.ops.object.select_all(action='DESELECT')
            for o in created_objects:
                o.select_set(True)
            context.view_layer.objects.active = created_objects[0]
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


        return {'FINISHED'}