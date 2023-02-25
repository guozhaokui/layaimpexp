bl_info = {
    "name": "LayaImporter",
    "blender": (2, 80, 0),
    "location": "File > Import > laya",
    "description": "Imports laya model",
    "warning": '',
    "category": "Import-Export",
}

from email.policy import default
import bpy
import os
import sys
from bpy.props import *

#调试期间用这个，否则找不到 BlenderImporter
#真正运行的时候用zip应该没有问题
# TODO
sys.path.append('D:/work/layaimpexp/addon')

import BlenderImporter

from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        )

from bpy.types import (
        Operator,
        OperatorFileListElement,
        )

class LayaImporter(bpy.types.Operator,ImportHelper):
    """导入laya资源"""
    axis_forward='Z'
    axis_up='Y'
    bl_idname = "import_laya.mesh"        # Unique identifier for buttons and menu items to reference.
    bl_label = "加载"         # Display name in the interface.      选择文件的确定按钮
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.
    total: IntProperty(name="Steps", default=2, min=1, max=100)
    files       : CollectionProperty(name="File Path", type=bpy.types.OperatorFileListElement,)
    directory   : StringProperty(maxlen=1024, subtype='DIR_PATH', options={'HIDDEN', 'SKIP_SAVE'},)
    url   : StringProperty(maxlen=1024, 
        #default='https://oss.layabox1-beijing.layabox.com/upload/svn/resource/character/ohayoo_avatar/model/Role_taikong_01_head.lh'
        )
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

        imp = BlenderImporter.BlenderImporter()
        url = self.url or self.filepath
        ext:str = os.path.splitext(url)[-1]
        if(ext.lower()=='.lh'):
            imp.importLH(url)
        elif(ext.lower()=='.lm'):
            imp.importLm(url)
        return {'FINISHED'}            # Lets Blender know the operator finished successfully.


class LayaExporter(bpy.types.Operator,ExportHelper):
    """导出laya资源"""
    bl_idname = "export_laya.mesh"        # Unique identifier for buttons and menu items to reference.
    bl_label = "导出"         # Display name in the interface.      选择文件的确定按钮
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
    use_selection: BoolProperty(
        name='Selected Objects',
        description='Export selected objects only',
        default=False
    )

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):        # execute() is called when running the operator.
        paths = [os.path.join(self.directory, name.name)
                 for name in self.files]

        imp = BlenderImporter.BlenderImporter()
        ext:str = os.path.splitext(self.filepath)[-1]
        if(ext.lower()=='.lh'):
            imp.exportLH(BlenderImporter.ExportSetting(),self.filepath)
            pass
        elif(ext.lower()=='.lm'):
            pass
        return {'FINISHED'}                

# def menu_func(self, context):
#     self.layout.operator(ObjectMoveX.bl_idname)

def menu_func(self, context):
    # 注意第一个参数必须是类似xx.xx的形式，必须有个点，根据这个找到operator
    self.layout.operator(LayaImporter.bl_idname, text = "laya 3.0 (.lm/.lh)")    

def menu_export(self, context):
    #在layout：UILayout上添加一个新的按钮，用来调用相应的Operator
    self.layout.operator(LayaExporter.bl_idname, text = "laya 3.0 (.lh)")    
    pass

def register():
    bpy.utils.register_class(LayaImporter)
    bpy.utils.register_class(LayaExporter)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)
    bpy.types.TOPBAR_MT_file_export.append(menu_export)

def unregister():
    bpy.utils.unregister_class(LayaImporter)
    bpy.utils.unregister_class(LayaExporter)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)
    bpy.types.TOPBAR_MT_file_export.remove(menu_export)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()