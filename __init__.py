bl_info = {
    "name":         "Whill Data Format",
    "author":       "Gabriel Wang",
    "blender":      (2,6,2),
    "version":      (0,0,1),
    "location":     "File > Import-Export",
    "description":  "Export whill data format",
    "category":     "Import-Export"
}

# Ensure that we reload our dependencies if we ourselves are reloaded by Blender
if "bpy" in locals():
    import imp;
    if "exporter" in locals():
        imp.reload(exporter);
        
import bpy;
from . import exporter;



def menu_func(self, context):
    self.layout.operator(exporter.Exporter.bl_idname, text="Whill Model Format(.wmh)");

def register():
    bpy.utils.register_module(__name__);
    bpy.types.INFO_MT_file_export.append(menu_func);
    
def unregister():
    bpy.utils.unregister_module(__name__);
    bpy.types.INFO_MT_file_export.remove(menu_func);

if __name__ == "__main__":
    register()
