import os
from pathlib import Path

import bpy

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