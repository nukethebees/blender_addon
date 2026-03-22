from typing import Any

import bpy

from . import operators as ops
from . import registration

class NPanel(bpy.types.Panel):
    """
    Will appear in the N-panel.
    """
    bl_label = "NukeTheBees"
    bl_idname = "NTB_PT_NPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'NukeTheBees'

    identifiers_to_ignore = set((
            "rna_type",
            "name",
        ))

    def split_prop(self, 
                   layout: bpy.types.UILayout, 
                   data: Any, 
                   disp_name:str, 
                   prop_name:str, 
                   factor:float=0.5):
        split = layout.split(factor=factor)
        split.label(text=disp_name)
        split.prop(data, prop_name, text="")

    def split_props(self, layout: bpy.types.UILayout, prop_group: bpy.types.PropertyGroup):
        for prop in prop_group.bl_rna.properties:
            if prop.identifier in self.identifiers_to_ignore:
                continue
            self.split_prop(layout, prop_group, prop.name, prop.identifier)

    def draw(self, context: bpy.types.Context):
        ro = registration.register_menu_operator

        reg_ops = (
            ops.PrintHelloOperator,
        )
        for op in reg_ops:
            ro(self.layout, op)

        

        export_box = self.layout.box()
        ro(export_box, ops.UnrealExportMeshesOperator)
        export_mesh_props: ops.UnrealExportMeshesOperator.Settings = context.scene.unreal_export_meshes_settings
        self.split_props(export_box, export_mesh_props)

        dupe_box = self.layout.box()
        ro(dupe_box, ops.DuplicateAroundCursorOperator)
        dupe_around_props: ops.DuplicateAroundCursorOperator.Settings = context.scene.duplicate_around_cursor_settings
        
        is_radius = dupe_around_props.positioning_mode == "Radius"
        radius_skips = set((
            "radius", "angle_offset"
        ))
        orientate_to_ignore = set(self.identifiers_to_ignore)
        orientate_to_ignore.add("orientation_fwd")
        orientate_to_ignore.add("orientation_up")
        for prop in dupe_around_props.bl_rna.properties:
            if prop.identifier in orientate_to_ignore:
                continue

            if not is_radius:
                if prop.identifier in radius_skips:
                    continue

            self.split_prop(dupe_box, dupe_around_props, prop.name, prop.identifier)

        orientation_row = dupe_box.row()
        orientation_row.label(text="Fwd/up")
        orientation_row.prop(dupe_around_props, "orientation_fwd", text="")
        orientation_row.prop(dupe_around_props, "orientation_up", text="")

        align_around_box = self.layout.box()
        ro(align_around_box, ops.AlignAroundCursorOperator)
        ro(align_around_box, ops.AlignTowardsCursorOperator)
        align_around_props: ops.AlignAroundCursorOperator.Settings = context.scene.align_around_cursor_settings
        self.split_props(align_around_box, align_around_props)

class MenuBar(bpy.types.Menu):
    bl_label = "NukeTheBees"
    bl_idname = "NTB_MT_MenuBar"

    def draw(self, context: bpy.types.Context):
        for op in (ops.PrintHelloOperator, 
                   ops.ReloadScriptsOperator):
            registration.register_menu_operator(self, op)

def draw_menu_button(self, context: bpy.types.Context):
    self.layout.menu(MenuBar.bl_idname)
