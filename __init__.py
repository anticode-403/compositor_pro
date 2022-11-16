bl_info = {
    "name" : "Compositor Pro",
    "author" : "anticode-403, Nihal Rahman",
    "blender" : (3, 3, 0),
    "version" : (0, 0, 1),
    "category" : "Compositing"
}

import bpy

class main_panel(bpy.types.Panel):
    bl_label = "Compositor Pro"
    bl_category = "Compositor Pro"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_idname = "AC_PT_Comp_Pro"

    @classmethod
    def poll(cls, context):
        if (context.space_data.tree_type == 'CompositorNodeTree'):
            return True
        else:
            return False

    def draw(self, context): # Create 3D View panel
        layout = self.layout
        settings = context.scene.compositor_pro_props

        panel = layout.row()
        if not context.space_data.tree_type == 'CompositorNodeTree':
            return
        if not context.scene.use_nodes:
            panel.label(text="Please enable nodes.")
        else:
            panel.prop(settings, 'categories')
            

class compositor_pro_props(bpy.types.PropertyGroup):
    categories: bpy.props.EnumProperty(
        name='Category',
        items=(
            ('name', 'DisplayName', 'name'),
        ),
        default='name'
    )

classes = [ main_panel ]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.compositor_pro_props = bpy.props.PointerProperty(type=compositor_pro_props)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.compositor_pro_props

if __name__ == "__main__":
    register()
