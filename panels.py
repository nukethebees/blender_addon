import bpy

from . import operators as ops
from . import registration

class NPanel(bpy.types.Panel):
    """
    Will appear in the N-panel.
    """
    bl_label = "N Panel Menu"
    bl_idname = "NTB_PT_NPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'NukeTheBees'

    def draw(self, context: bpy.types.Context):
        for op in (ops.PrintHelloOperator,
                   ):
            registration.register_menu_operator(self, op)

class MenuBar(bpy.types.Menu):
    bl_label = "NukeTheBees"
    bl_idname = "NTB_MT_MenuBar"

    def draw(self, context: bpy.types.Context):
        for op in (ops.PrintHelloOperator, 
                   ops.ReloadScriptsOperator, 
                   ops.UnrealExportAllMeshesSeparatelyOperator):
            registration.register_menu_operator(self, op)

def draw_menu_button(self, context: bpy.types.Context):
    self.layout.menu(MenuBar.bl_idname)
