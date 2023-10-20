bl_info = {
    "name" : "Compositor Pro",
    "author" : "anticode-403, Nihal Rahman",
    "blender" : (3, 6, 0),
    "version" : (0, 0, 7),
    "category" : "Compositing"
}

import bpy
from . utility import recursive_node_fixer, previews_from_directory_items, has_color_management, preview_collections, file_path_node_tree

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
            compositor = context.scene.node_tree
            panel = panel.column()
            if bpy.app.version < (4, 0, 0) and context.scene.display_settings.display_device in ['sRGB', 'XYZ', 'None']:
                panel.label(text="Please update Blender to 4.0 or install Color Management+6")
            if not compositor.use_groupnode_buffer or not compositor.use_two_pass:
                panel.operator('comp_pro.enable_optimizations', text="Enable Optimizations")
            panel.prop(settings, 'categories')
            panel.template_icon_view(settings, 'comp_'+str(settings.categories), show_labels=True)
            panel.operator('comp_pro.add_node', text="Add").choice = settings.categories


class compositor_pro_props(bpy.types.PropertyGroup):
    def import_effects(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='effects')
    # def import_utilities(self, context):
    #     bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='utilities')
    def import_batches(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='batches')

    categories: bpy.props.EnumProperty(
        name='Category',
        items=(
            ('effects', 'Effects', 'effects'),
            # ('utilities', 'Utilities', 'utilities'),
            ('batches', 'Batches', 'batches'),
        ),
        default='effects'
    )
    # comp_utilities: bpy.props.EnumProperty(
    #     items=previews_from_directory_items(preview_collections['utilities']),
    # )
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
        #find node
        group_name = eval('bpy.context.scene.compositor_pro_props.comp_{}'.format(self.choice))
        node_tree = context.scene.node_tree
        nodes = node_tree.nodes
        #append
        if not bpy.data.node_groups.get(group_name):
            bpy.ops.wm.append(filename=group_name, directory=file_path_node_tree)
        #add to scene
        new_group = nodes.new(type='CompositorNodeGroup')
        new_group.node_tree = bpy.data.node_groups.get(group_name)
        new_group.node_tree.use_fake_user = False
        #fix nodes
        recursive_node_fixer(new_group, context)
        #attatch to cursor
        new_group.location = context.space_data.cursor_location
        for n in nodes:
            n.select = n == new_group
        bpy.ops.node.translate_attach('INVOKE_DEFAULT')
        return {'FINISHED'}

class compositor_pro_enable_optimizations(bpy.types.Operator):
    bl_idname = 'comp_pro.enable_optimizations'
    bl_description = 'Enable Blender compositor optimizations'
    bl_category = 'Node'
    bl_label = 'Enable Optimizations'

    def invoke(self, context, event):
        compositor = context.scene.node_tree
        compositor.use_groupnode_buffer = True
        compositor.use_two_pass = True
        if bpy.app.version > (4, 0, 0):
            compositor.use_opencl = True
        else:
            compositor.use_opencl = False
        return {'FINISHED'}


classes = [ compositor_pro_enable_optimizations, compositor_pro_add_node, main_panel, compositor_pro_props ]

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
