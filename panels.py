import bpy

from . import operators

class NPanel(bpy.types.Panel):
    """
    Will appear in the N-panel.
    """
    bl_label = "N Panel Menu"
    bl_idname = "NTB_PT_NPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'NukeTheBees'

    def draw(self, context):
        layout = self.layout
        layout.operator("ntb.print_hello", text="Say Hello")

class MenuBar(bpy.types.Menu):
    bl_label = "NukeTheBees"
    bl_idname = "NTB_MT_MenuBar"

    def draw(self, context):
        layout = self.layout
        layout.operator("ntb.print_hello", text="Say Hello", icon='TEXT')
        layout.operator("ntb.reload_scripts", text="Reload Scripts", icon='TEXT')
        layout.operator("ntb.export_unreal", text="Export Unreal", icon='TEXT')
        

def draw_menu_button(self, context):
    self.layout.menu(MenuBar.bl_idname)