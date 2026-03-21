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

    def draw(self, context: bpy.types.Context):
        ro = registration.register_menu_operator

        reg_ops = (
            ops.PrintHelloOperator,
        )
        for op in reg_ops:
            ro(self, op)

        self.layout.separator()
        ro(self, ops.UnrealExportMeshesOperator)
        export_mesh_props: ops.UnrealExportMeshesOperator.Settings = context.scene.unreal_export_meshes_settings
        self.layout.prop(export_mesh_props, "mesh_mode")

        self.layout.separator()
        ro(self, ops.DuplicateAroundCursorOperator)
        dupe_around_props: ops.DuplicateAroundCursorOperator.Settings = context.scene.duplicate_around_cursor_settings
        self.layout.prop(dupe_around_props, "count")
        self.layout.prop(dupe_around_props, "radius")
        self.layout.prop(dupe_around_props, "apply_transforms")
        self.layout.prop(dupe_around_props, "orientation")

class MenuBar(bpy.types.Menu):
    bl_label = "NukeTheBees"
    bl_idname = "NTB_MT_MenuBar"

    def draw(self, context: bpy.types.Context):
        for op in (ops.PrintHelloOperator, 
                   ops.ReloadScriptsOperator):
            registration.register_menu_operator(self, op)

def draw_menu_button(self, context: bpy.types.Context):
    self.layout.menu(MenuBar.bl_idname)
