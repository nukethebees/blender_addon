import math

import bpy
import mathutils

Vector = mathutils.Vector

def orientate_towards(obj:bpy.types.Object, 
                      direction:Vector, 
                      orientation: tuple[str, str]=("X", "Z"),
                      offset:Vector = Vector()
                      ) -> None:
    rot = direction.to_track_quat(*orientation)
    obj.rotation_euler = rot.to_euler()

    offset = Vector(math.radians(d) for d in offset)
    obj.rotation_euler.x += offset.x
    obj.rotation_euler.y += offset.y
    obj.rotation_euler.z += offset.z