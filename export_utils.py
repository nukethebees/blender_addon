import os
from pathlib import Path

import bpy
BpyObject = bpy.types.Object


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

class Duplicator:
    def __init__(self, 
                 context: bpy.types.Context, 
                 duplicate_prefix:str="",
                 original_prefix:str="",
                 debug_mode:bool=False):
        self.duplicate_prefix = duplicate_prefix
        self.original_prefix = original_prefix
        self.context = context
        self.new_objects: list[BpyObject] = []
        self.debug_mode = debug_mode

    def duplicate_hierarchy(self, 
                            obj:BpyObject, 
                            parent:BpyObject=None) -> BpyObject:
        name = obj.name
        if self.original_prefix:
            prefixed_obj_name = f"{self.original_prefix}{name}"
            obj.name = prefixed_obj_name
            if self.debug_mode:
                print(f"Renamed object from {name} to {obj.name}")

        new_obj = obj.copy()
        new_obj.data = obj.data  # share mesh
        self.context.collection.objects.link(new_obj)

        if parent:
            new_obj.parent = parent
            new_obj.matrix_parent_inverse = parent.matrix_world.inverted()

        new_obj_original_name = new_obj.name          
        new_obj.name = f"{self.duplicate_prefix}{name}"

        if self.debug_mode:
            print(f"Created copy: {new_obj_original_name}")
            print(f"Renamed copy: {new_obj.name}")
            print(f"Original obj cur name: {obj.name}")
        

        for child in obj.children:
            self.duplicate_hierarchy(child, new_obj)

        self.new_objects.append(new_obj)

        return new_obj