bl_info = {
    "name": "My Test Add-on",
    "blender": (5, 0, 0),
    "category": "Object",
}

def register():
    print("Hello World")
def unregister():
    print("Goodbye World")

if __name__ == "__main__":
    register()