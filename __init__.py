bl_info = {
    "name" : "Compositor Pro",
    "author" : "anticode-403, Nihal Rahman",
    "blender" : (3, 3, 0),
    "version" : (0, 0, 3),
    "category" : "Compositing"
}

import bpy
from . utility import previews_from_directory_items, has_color_management, preview_collections, file_path_node_tree

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
            panel.operator('comp_pro.add_node', text="Add").choice = settings.categories
            #panel.operator('comp_pro.enable_optimizations', text="Enable Optimizations")


class compositor_pro_props(bpy.types.PropertyGroup):
    def import_effects(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='effects')
    def import_utilities(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='utilities')
    def import_batches(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='batches')

    categories: bpy.props.EnumProperty(
        name='Category',
        items=(
            ('effects', 'Effects', 'effects'),
            ('utilities', 'Utilities', 'utilities'),
            ('batches', 'Batches', 'batches'),
        ),
        default='effects'
    )
    comp_utilities: bpy.props.EnumProperty(
        items=previews_from_directory_items(preview_collections['utilities']),
    )
    comp_effects: bpy.props.EnumProperty(
        items=previews_from_directory_items(preview_collections['effects']),
    )
    comp_batches: bpy.props.EnumProperty(
        items=previews_from_directory_items(preview_collections['batches']),
    )

class compositor_pro_add_node(bpy.types.Operator):
    bl_idname = 'comp_pro.add_node'
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
        new_group.position = context.space_data.cursor_location
        for n in nodes:
            n.select = n == new_group
        return {'FINISHED'}


classes = [ compositor_pro_add_node, main_panel, compositor_pro_props ]

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
