from typing import Iterable

import bpy

def select_objects(objs: Iterable[bpy.types.Object]) -> None:
    first=True

    for obj in objs:
        obj.select_set(True)
        if first:
            bpy.context.view_layer.objects.active = obj
        first = False

def unselect_all() -> None:
    bpy.ops.object.select_all(action='DESELECT')

def get_all_meshes(context: bpy.types.Context) -> list[bpy.types.Object]:
    return [obj for obj in context.scene.objects if obj.type == 'MESH']

def select_all_meshes_only(context: bpy.types.Context) -> list[bpy.types.Object]:
    unselect_all()
    mesh_objects = get_all_meshes(context)
    for obj in mesh_objects:
        obj.select_set(True)
    return mesh_objects

def select_only(obj: bpy.types.Object) -> None:
    unselect_all()
    obj.select_set(True)

def select_hierarchy(root):
    bpy.ops.object.select_all(action='DESELECT')

    def recurse(obj):
        obj.select_set(True)
        for child in obj.children:
            recurse(child)

    recurse(root)