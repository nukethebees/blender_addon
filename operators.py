import math
import os
from pathlib import Path
import re
from typing import cast

import bpy
BpyObject = bpy.types.Object
BpyContext = bpy.types.Context

import mathutils

Vector = mathutils.Vector

from . import selection_utils as su
from . import orientation_utils as ou
from . import export_utils as ex

class PrintHelloOperator(bpy.types.Operator):
    bl_idname = "ntb.print_hello"
    bl_label = "Print Hello"

    def execute(self, context: BpyContext):
        print("Hello, world!")
        return {'FINISHED'}
    
class ReloadScriptsOperator(bpy.types.Operator):
    bl_idname = "ntb.reload_scripts"
    bl_label = "Reload Scripts"

    def execute(self, context: BpyContext):
        bpy.ops.script.reload()
        return {'FINISHED'}

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
                ('NewSeparate', "NewSeparate", "Export meshes separately"),
            ],
            default='Combine'
        ) # type: ignore
        remove_copies: bpy.props.BoolProperty(
            name="Remove copies",
            default=True,
            description="Remove temporary copies after exporting"
        ) # type: ignore
        debug_mode: bpy.props.BoolProperty(
            name="Debug mode",
            default=False,
            description="Enable debug mode"
        ) # type: ignore

    def init_class_members(self, context: BpyContext) -> None:
        self.props = cast(UnrealExportMeshesOperator.Settings, context.scene.unreal_export_meshes_settings)

        self.original_objects: list[BpyObject] = list(context.scene.objects)
        self.empty_scales = {}
        self.to_remove: list[BpyObject] = []
        self.folder:str = ex.get_export_dir()
        self.export_objects: list[BpyObject] = []

        self.export_prefix = ""
        self.original_prefix = "ORIGINAL_"

    def shrink_empty_scales(self, context) -> None:
        self.empty_scales = {}
        for obj in context.scene.objects:
            if obj.type == 'EMPTY':
                self.empty_scales[obj.name] = obj.scale.copy()
                obj.scale = (0.01, 0.01, 0.01)  # shrink to tiny size for Unreal

    def restore_empty_scales(self) -> None:
        for name, scale in self.empty_scales.items():
            bpy.data.objects[name].scale = scale

    def export_cleanup(self, context: BpyContext) -> None:
        self.restore_empty_scales()

        for obj in self.to_remove:
            if obj:
                bpy.data.objects.remove(obj, do_unlink=True)
        for obj in self.export_objects:
            if obj:
                bpy.data.objects.remove(obj, do_unlink=True)      

    def get_file_path(self, file_name:str) -> str:
        return os.path.join(self.folder, file_name)

    def export_mesh_to_fbx(self, context: BpyContext, name:str) -> None:
        file_name = ex.make_fbx_name(name)
        file_path = self.get_file_path(file_name)
        self.run_fbx_export(context, file_path)

    def run_fbx_export(self, context: BpyContext, file_path: str):
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

    def add_prefix_original_objects(self):
        for obj in self.original_objects:
            obj.name = f"{self.original_prefix}{obj.name}"
    def remove_prefix_original_objects(self):
        if not self.props.remove_copies:
            for obj in self.export_objects:
                obj.name = f"EXPORTED_{obj.name}"

        for obj in self.original_objects:
            obj.name = obj.name.removeprefix(self.original_prefix)

    def copy_all_mesh_objects(self, context: BpyContext):
        scene_objects = list(o for o in context.scene.objects if o.parent is None)
        d = ex.Duplicator(context, 
                          self.export_prefix, 
                          self.original_prefix, 
                          debug_mode=self.props.debug_mode)

        for obj in scene_objects:
            new_obj = d.duplicate_hierarchy(obj)
            #self.export_objects.append(new_obj)
        
        self.export_objects = d.new_objects

    def execute(self, context: BpyContext) -> set[str]:
        self.init_class_members(context)
        
        original_mode = context.mode
        original_selected = context.selected_objects
        original_active = bpy.context.view_layer.objects.active

        if context.active_object:
            bpy.ops.object.mode_set(mode='OBJECT')

        match self.props.mesh_mode:
            case "Combine": 
                su.select_all_meshes_only(context)
                self.export_mesh_to_fbx(context, Path(bpy.data.filepath).stem)
                self.report({'INFO'}, f"Exported to FBX")
            case "Separate": 
                n_exported = 0
                for obj in su.get_all_meshes(context):
                    su.select_hierarchy(obj)
                    self.export_mesh_to_fbx(context, obj.name)
                    n_exported += 1

                self.report({'INFO'}, f"Exported {n_exported} objects to FBX")
            case "NewSeparate":
                n_exported = 0
                self.copy_all_mesh_objects(context)
                for obj in (o for o in self.export_objects if o.type == "MESH"):
                    su.select_hierarchy(obj)
                    name = obj.name
                    self.export_mesh_to_fbx(context, name)
                    if self.props.debug_mode:
                        print(f"Exported: {name} (type: {obj.type})")
                    n_exported += 1
                self.report({'INFO'}, f"Exported {n_exported} objects to FBX")
            case _:
                self.report({'WARNING'}, f"Unhandled mesh mode: {self.props.mesh_mode}")
                return {'CANCELLED'}
        
        if self.props.remove_copies:
            self.export_cleanup(context)
        self.remove_prefix_original_objects()
        su.unselect_all()
        su.select_objects(original_selected)
        if original_active is not None:
            bpy.context.view_layer.objects.active = original_active
        if context.active_object:
            bpy.ops.object.mode_set(mode=original_mode)

        return {'FINISHED'}
    
class PropFactory:
    @staticmethod
    def angle_offset():
        return bpy.props.FloatProperty(
            name="Angle offset",
            default=0.0,
            description="Angle offset"
        ) # type: ignore
    @staticmethod
    def orientation_fwd():
        return bpy.props.StringProperty(
            name="Orientation Forward",
            description="The forward axis for alignment.",
            default="X"
        ) # type: ignore
    @staticmethod
    def orientation_up(): 
        return bpy.props.StringProperty(
            name="Orientation up",
            description="The up axis for alignment.",
            default="Z"
        ) # type: ignore
    @staticmethod
    def orientation_offset():
        return bpy.props.FloatVectorProperty(
            name="Orientation offset",
            description="Orientation offset (degrees)",
            default=Vector()
        ) # type: ignore
    @staticmethod
    def orientation(): 
        return bpy.props.EnumProperty(
            name="Orientation",
            description="Alignment orientation",
            items=[
                ('Towards', "Towards", "Towards cursor"),
                ('Away', "Away", "Away from cursor"),
                ('Source', "Source", "Same as source object"),
            ],
            default='Towards'
        ) # type: ignore

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
        angle_offset: PropFactory.angle_offset()  # type: ignore
        orientation: PropFactory.orientation() # type: ignore
        orientation_fwd: PropFactory.orientation_fwd() # type: ignore
        orientation_up: PropFactory.orientation_up() # type: ignore
        orientation_offset: PropFactory.orientation_offset() # type: ignore
        

    def orientate_towards(self, obj:BpyObject, direction:Vector) -> None:
        return ou.orientate_towards(obj, direction, (self.orientation_fwd, self.orientation_up), self.orientation_offset)

    def apply_transforms(self, context: BpyContext):
        bpy.ops.object.select_all(action='DESELECT')
        for o in self.ring_objects:
            o.select_set(True)
        context.view_layer.objects.active = self.ring_objects[0]
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    def execute(self, context: BpyContext) -> set[str]:
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

        self.ring_objects: list[BpyObject] = []
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
                case "Towards":
                    self.orientate_towards(obj, cursor - obj.location)
                case "Away":
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
        orientation: PropFactory.orientation() # type: ignore
        orientation_fwd: PropFactory.orientation_fwd() # type: ignore
        orientation_up: PropFactory.orientation_up() # type: ignore
        orientation_offset: PropFactory.orientation_offset() # type: ignore

    def execute(self, context: BpyContext) -> set[str]:
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
                case "Source":
                    pass
                case _:
                    self.report({'WARNING'}, f"Unhandled orientation: {self.orientation}")
                    return {'CANCELLED'}

        return {'FINISHED'}
    
class AlignTowardsCursorOperator(bpy.types.Operator):
    bl_idname = "ntb.align_towards_cursor"
    bl_label = "Align selected instances towards cursor"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: BpyContext) -> set[str]:
        n_selected_objects = len(context.selected_objects)
        if n_selected_objects < 1:
            self.report({'WARNING'}, f"{n_selected_objects} selected objects.")
            return {'CANCELLED'}
    
        self.props = cast(AlignAroundCursorOperator.Settings, context.scene.align_around_cursor_settings)
        self.orientation = cast(str, self.props.orientation)
        self.orientation_fwd_up = cast(tuple[str,str], (self.props.orientation_fwd, self.props.orientation_up))
        self.orientation_offset = cast(Vector, self.props.orientation_offset)

        cursor = context.scene.cursor.location
        self.ref_obj = context.selected_objects[0]

        for i in range(n_selected_objects):
            obj = context.selected_objects[i]

            match self.orientation:
                case "Towards":
                    ou.orientate_towards(obj, cursor - obj.location, self.orientation_fwd_up, self.orientation_offset)
                case "Away":
                    ou.orientate_towards(obj, obj.location - cursor, self.orientation_fwd_up, self.orientation_offset)
                case "Source":
                    pass
                case _:
                    self.report({'WARNING'}, f"Unhandled orientation: {self.orientation}")
                    return {'CANCELLED'}

        return {'FINISHED'}