bl_info = {
    "name" : "Compositor Pro",
    "author" : "anticode-403, Nihal Rahman",
    "blender" : (3, 3, 0),
    "version" : (0, 0, 1),
    "category" : "Compositing"
}

import bpy
from . utility import previews_from_directory_items, preview_collections, file_path_node_tree

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
            panel = panel.column()
            panel.prop(settings, 'categories')
            panel.template_icon_view(settings, 'comp_'+str(settings.categories), show_labels=True)
            panel.operator('comp_pro.add_nodes', text="Add").choice = settings.categories
            

class compositor_pro_props(bpy.types.PropertyGroup):
    def import_name(self, context):
        bpy.ops.comp_pro.add_nodes('INVOKE_DEFAULT', choice='name')

    categories: bpy.props.EnumProperty(
        name='Category',
        items=(
            ('name', 'DisplayName', 'name'),
        ),
        default='name'
    )
    comp_name: bpy.props.EnumProperty(
        items=previews_from_directory_items(preview_collections['name']),
        update=import_name
    )

class compositor_pro_add_nodes(bpy.types.Operator):
    bl_idname = 'comp_pro.add_nodes'
    bl_description = 'Add Compositor Node'
    bl_category = 'Node'
    bl_label = 'Add Node'

    choice: bpy.props.StringProperty()

    def invoke(self, context, event):
        group_name = eval('bpy.context.scene.compositor_pro_props.comp_{}'.format(self.choice))
        node_tree = context.scene.node_tree
        nodes = node_tree.nodes
        if not bpy.data.node_groups.get(group_name):
            bpy.ops.wm.append(filename=group_name, directory=file_path_node_tree)
        new_group = nodes.new(type='CompositorNodeGroup')
        new_group.node_tree = bpy.data.node_groups.get(group_name)
        # new_group.position = context.scene.camera.position
        return {'FINISHED'}

# def previews_from_directory_items(pcoll):
#     enum_items = []

#     if bpy.context is None:
#         return enum_items
    
#     directory = pcoll.my_previews_dir

#     if directory and os.path.exists(directory):
#         image_paths = []
#         for fn in os.listdir(directory):
#             if fn.lower().endswith(".jpg"):
#                 image_paths.append(fn)
        

classes = [ compositor_pro_add_nodes, main_panel, compositor_pro_props ]

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
