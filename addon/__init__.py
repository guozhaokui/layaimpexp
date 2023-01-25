bl_info = {
    "name": "Move X Axis",
    "blender": (2, 80, 0),
    "location": "File > Import > laya",
    "description": "Imports laya model",
    "warning": '',
    "category": "Import-Export",
}

import bpy
import os
import sys
from bpy.props import *


from bpy_extras.io_utils import (
        ImportHelper,
        )

from bpy.types import (
        Operator,
        OperatorFileListElement,
        )

class ObjectMoveX(bpy.types.Operator,ImportHelper):
    """My Object Moving Script"""      # Use this as a tooltip for menu items and buttons.
    bl_idname = "import_laya.mesh"        # Unique identifier for buttons and menu items to reference.
    bl_label = "加载"         # Display name in the interface.      选择文件的确定按钮
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.
    total: IntProperty(name="Steps", default=2, min=1, max=100)
    files       : CollectionProperty(name="File Path", type=bpy.types.OperatorFileListElement,)
    directory   : StringProperty(maxlen=1024, subtype='DIR_PATH', options={'HIDDEN', 'SKIP_SAVE'},)
    projTab     : EnumProperty(name="Geometry parameters",
                                 default = 'MANUAL',
                                 description="Reverse projection parameters",
                                 items=[('MANUAL',  "Manual", "Manual parameters of projection transform"),
                                        ('PROJMAT', "Matrix", "Exact projection matrix (from ripper log)"),
                                       ],
                                )


    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):        # execute() is called when running the operator.
        paths = [os.path.join(self.directory, name.name)
                 for name in self.files]

        # The original script
        scene = context.scene
        for obj in scene.objects:
            obj.location.x += 1.0

        return {'FINISHED'}            # Lets Blender know the operator finished successfully.

# def menu_func(self, context):
#     self.layout.operator(ObjectMoveX.bl_idname)

def menu_func(self, context):
    # 注意第一个参数必须是类似xx.xx的形式，必须有个点，根据这个找到operator
    self.layout.operator(ObjectMoveX.bl_idname, text = "import laya mesh lh")    

def register():
    bpy.utils.register_class(ObjectMoveX)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)

def unregister():
    bpy.utils.unregister_class(ObjectMoveX)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()