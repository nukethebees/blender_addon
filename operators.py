import math
import os
from pathlib import Path
import re
from typing import cast

import bpy
import mathutils

Vector = mathutils.Vector

from .selection_utils import *
from . import orientation_utils as ou

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
            name="Mesh mode",
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
            name="Count",
            default=8,
            min=1,
            description="Number of duplicates"
        ) # type: ignore
        positioning_mode: bpy.props.EnumProperty(
            name="Positioning mode",
            description="Determine how the copies are positioned",
            items=[
                ('Radius', "Radius", "Radius value"),
                ('SelectedObject', "Selected Object", "Selected object is first object"),
            ],
            default='SelectedObject'
        ) # type: ignore
        radius: bpy.props.FloatProperty(
            name="Radius",
            default=2.0,
            min=0.0,
            description="Radius of the circle"
        ) # type: ignore
        apply_transforms: bpy.props.BoolProperty(
            name="Apply transforms",
            default=False,
            description="Apply transforms"
        ) # type: ignore
        angle_offset: bpy.props.FloatProperty(
            name="Angle offset",
            default=0.0,
            description="Angle offset"
        ) # type: ignore
        orientation: bpy.props.EnumProperty(
            name="Orientation",
            description="Copy orientation",
            items=[
                ('Source', "Source", "Same as source object"),
                ('CentreXY', "CentreXY", "Towards centre object"),
                ('-CentreXY', "-CentreXY", "Away from centre object"),
            ],
            default='CentreXY'
        ) # type: ignore
        orientation_fwd: bpy.props.StringProperty(
            name="Orientation Forward",
            description="The forward axis for alignment.",
            default="X"
        ) # type: ignore
        orientation_up: bpy.props.StringProperty(
            name="Orientation up",
            description="The up axis for alignment.",
            default="Z"
        ) # type: ignore
        orientation_offset: bpy.props.FloatVectorProperty(
            name="Orientation offset",
            description="Orientation offset (degrees)",
            default=Vector()
        ) # type: ignore

    def orientate_towards(self, obj:bpy.types.Object, direction:Vector) -> None:
        return ou.orientate_towards(obj, direction, (self.orientation_fwd, self.orientation_up), self.orientation_offset)

    def apply_transforms(self, context: bpy.types.Context):
        bpy.ops.object.select_all(action='DESELECT')
        for o in self.ring_objects:
            o.select_set(True)
        context.view_layer.objects.active = self.ring_objects[0]
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    def execute(self, context: bpy.types.Context) -> set[str]:
        n_selected_objects = len(context.selected_objects)
        if n_selected_objects != 1:
            self.report({'WARNING'}, f"{n_selected_objects} selected objects. Only 1 allowed")
            return {'CANCELLED'}

        self.ref_obj = context.selected_objects[0]
        if self.ref_obj is None:
            self.report({'WARNING'}, "Object is none")
            return {'CANCELLED'}         
        
        self.props = cast(UnrealExportMeshesOperator.Settings, context.scene.duplicate_around_cursor_settings)
        self.count = cast(int, self.props.count)
        self.radius = cast(float, self.props.radius)
        self.angle_offset = cast(float, self.props.angle_offset)
        self.positioning_mode = cast(float, self.props.positioning_mode)
        self.orientation = cast(str, self.props.orientation)
        self.should_apply_transforms = cast(bool, self.props.apply_transforms)
        self.orientation_fwd = cast(str, self.props.orientation_fwd)
        self.orientation_up = cast(str, self.props.orientation_up)
        self.orientation_offset = cast(Vector, self.props.orientation_offset)

        self.ring_objects: list[bpy.types.Object] = []
        cursor = context.scene.cursor.location
        self.angle_step = 2 * math.pi / self.count
        
        base_name = self.ref_obj.name
        base_number = 0
        if match := re.search(r'([a-zA-Z_][a-zA-Z0-9_]+)_(\d+)$', self.ref_obj.name):
            base_name = match.group(1)
            base_number = int(match.group(2))            

        start_index = 0
        match self.positioning_mode:
            case "Radius":
                pass
            case "SelectedObject":
                start_index = 1
                self.ring_objects.append(self.ref_obj)
            case _:
                self.report({'WARNING'}, f"Unhandled positioning mode: {self.positioning_mode}")
                return {'CANCELLED'}      
        
        for i in range(start_index, self.count):
            new_obj = self.ref_obj.copy()
            if self.ref_obj.data is not None:
                new_obj.data = self.ref_obj.data.copy()
            new_obj.name = f"{base_name}_{base_number + i}"

            context.collection.objects.link(new_obj)
            self.ring_objects.append(new_obj)

        for i in range(self.count):
            obj = self.ring_objects[i]
            angle = (i * self.angle_step) + self.angle_offset

            match self.positioning_mode:
                case "Radius":
                    pos = Vector((
                        cursor.x + self.radius * math.cos(angle),
                        cursor.y + self.radius * math.sin(angle),
                        cursor.z
                    ))
                    obj.location = pos
                case "SelectedObject":
                    translated = self.ref_obj.location - cursor
                    rotation_matrix = mathutils.Matrix.Rotation(angle, 3, 'Z')
                    rotated = rotation_matrix @ translated
                    pos = rotated + cursor
                    obj.location = pos
                case _:
                    self.report({'WARNING'}, f"Unhandled positioning mode: {self.positioning_mode}")
                    return {'CANCELLED'}   

            match self.orientation:
                case "CentreXY":
                    self.orientate_towards(obj, cursor - obj.location)
                case "-CentreXY":
                    self.orientate_towards(obj, obj.location - cursor)
                case "Source":
                    pass
                case _:
                    self.report({'WARNING'}, f"Unhandled orientation: {self.orientation}")
                    return {'CANCELLED'}

        if self.should_apply_transforms:
            self.apply_transforms(context)

        return {'FINISHED'}
    
class AlignAroundCursorOperator(bpy.types.Operator):
    bl_idname = "ntb.align_around_cursor"
    bl_label = "Align selected instances around cursor"
    bl_options = {'REGISTER', 'UNDO'}

    class Settings(bpy.types.PropertyGroup):
        angle_offset: bpy.props.FloatProperty(
            name="Angle offset",
            default=0.0,
            description="Angle offset"
        ) # type: ignore
        orientation: bpy.props.EnumProperty(
            name="Orientation",
            description="Alignment orientation",
            items=[
                ('Towards', "Towards", "Towards cursor"),
                ('Away', "Away", "Away from cursor"),
            ],
            default='Towards'
        ) # type: ignore
        orientation_fwd: bpy.props.StringProperty(
            name="Orientation Forward",
            description="The forward axis for alignment.",
            default="X"
        ) # type: ignore
        orientation_up: bpy.props.StringProperty(
            name="Orientation up",
            description="The up axis for alignment.",
            default="Z"
        ) # type: ignore
        orientation_offset: bpy.props.FloatVectorProperty(
            name="Orientation offset",
            description="Orientation offset (degrees)",
            default=Vector()
        ) # type: ignore

    def execute(self, context: bpy.types.Context) -> set[str]:
        n_selected_objects = len(context.selected_objects)
        if n_selected_objects < 1:
            self.report({'WARNING'}, f"{n_selected_objects} selected objects.")
            return {'CANCELLED'}
    
        self.props = cast(AlignAroundCursorOperator.Settings, context.scene.align_around_cursor_settings)
        self.angle_offset = cast(float, self.props.angle_offset)
        self.orientation = cast(str, self.props.orientation)
        self.orientation_fwd = cast(str, self.props.orientation_fwd)
        self.orientation_up = cast(str, self.props.orientation_up)
        self.orientation_fwd_up = (self.orientation_fwd, self.orientation_up)
        self.orientation_offset = cast(Vector, self.props.orientation_offset)


        cursor = context.scene.cursor.location
        self.angle_step = 2 * math.pi / n_selected_objects
        self.ref_obj = context.selected_objects[0]

        for i in range(n_selected_objects):
            obj = context.selected_objects[i]
            angle = (i * self.angle_step) + self.angle_offset

            translated = self.ref_obj.location - cursor
            rotation_matrix = mathutils.Matrix.Rotation(angle, 3, 'Z')
            rotated = rotation_matrix @ translated
            pos = rotated + cursor
            obj.location = pos

            match self.orientation:
                case "Towards":
                    ou.orientate_towards(obj, cursor - obj.location, self.orientation_fwd_up, self.orientation_offset)
                case "Away":
                    ou.orientate_towards(obj, obj.location - cursor, self.orientation_fwd_up, self.orientation_offset)
                case _:
                    self.report({'WARNING'}, f"Unhandled orientation: {self.orientation}")
                    return {'CANCELLED'}

        return {'FINISHED'}