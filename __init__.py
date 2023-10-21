bl_info = {
    "name" : "Compositor Pro",
    "author" : "anticode-403, Nihal Rahman",
    "blender" : (3, 6, 0),
    "version" : (0, 0, 8),
    "category" : "Compositing"
}

import bpy
from bpy_extras.io_utils import ImportHelper
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
            panel.operator('comp_pro.enable_nodes', text="Enable Nodes")
        else:
            compositor = context.scene.node_tree
            panel = panel.column()
            if bpy.app.version < (4, 0, 0) and context.scene.display_settings.display_device in ['sRGB', 'XYZ', 'None']:
                panel.label(text="Update to Blender to 4.0 or install CM+6.1")
            if not compositor.use_groupnode_buffer or not compositor.use_two_pass:
                panel.operator('comp_pro.enable_optimizations', text="Enable Optimizations")
            panel.prop(settings, 'categories', expand=True)
            panel.template_icon_view(settings, 'comp_'+str(settings.categories), show_labels=True)
            add_button = panel.row(align=True)
            add_button.operator('comp_pro.add_node', text="Add").choice = settings.categories
            add_button.prop(settings, 'quick_add', text='', icon='TIME')
            if compositor.nodes.active.bl_idname == 'CompositorNodeGroup' and compositor.nodes.active.node_tree.name == 'Grain+':
                panel.operator('comp_pro.replace_grain', text="Replace Grain Texture")

class compositor_pro_props(bpy.types.PropertyGroup):
    def import_effects(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='effects')
    def import_utilities(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='utilities')
    def import_batches(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='batches')
    def import_dev(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='dev')

    def quick_add_effects(self, context):
        if context.scene.compositor_pro_props.quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='effects')
    def quick_add_utilities(self, context):
        if context.scene.compositor_pro_props.quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='utilities')
    def quick_add_batches(self, context):
        if context.scene.compositor_pro_props.quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='batches')
    def quick_add_dev(self, context):
        if context.scene.compositor_pro_props.quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='dev')

    quick_add: bpy.props.BoolProperty(
        name = 'Quick Add',
        description = '',
        default = False
    )

    categories: bpy.props.EnumProperty(
        name='Category',
        items=(
            ('effects', 'Effects', 'effects'),
            ('utilities', 'Utilities', 'utilities'),
            ('batches', 'Batches', 'batches'),
            ('dev', 'Dev Tools', 'dev'),
        ),
        default='effects'
    )
    comp_utilities: bpy.props.EnumProperty(
        items=previews_from_directory_items(preview_collections['utilities']),
        update=quick_add_utilities
    )
    comp_effects: bpy.props.EnumProperty(
        items=previews_from_directory_items(preview_collections['effects']),
        update=quick_add_effects
    )
    comp_batches: bpy.props.EnumProperty(
        items=previews_from_directory_items(preview_collections['batches']),
        update=quick_add_batches
    )
    comp_dev: bpy.props.EnumProperty(
        items=previews_from_directory_items(preview_collections['dev']),
        update=quick_add_dev
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

class compositor_pro_replace_grain(bpy.types.Operator, ImportHelper):
    bl_idname = 'comp_pro.replace_grain'
    bl_description = 'Replace the grain texture in the Grain+ NG'
    bl_category = 'Node'
    bl_label = 'Replace Grain Texture'

    filter_glob = bpy.props.StringProperty(
        default='*' + ';*'.join(bpy.path.extensions_image),
        options={'HIDDEN'},
    )

    # def invoke(self, context, event):
    #     context.window_manager.fileselect_add(self)
    #     return {'RUNNING_MODAL'}

    def execute(self, context):
        grain_node = context.scene.node_tree.nodes.active
        grain_texture_node = None
        for node in grain_node.node_tree.nodes:
            if node.name == 'Grain':
                grain_texture_node = node
        new_texture = bpy.data.images.load(filepath = self.filepath)
        grain_texture_node.image = new_texture
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

class compositor_pro_enable_nodes(bpy.types.Operator):
    bl_idname = 'comp_pro.enable_nodes'
    bl_description = 'Enable compositor nodes'
    bl_category = 'Node'
    bl_label = 'Enable Nodes'

    def invoke(self, context, event):
        context.scene.use_nodes = True
        return {'FINISHED'}


classes = [ compositor_pro_replace_grain, compositor_pro_enable_optimizations, compositor_pro_enable_nodes, compositor_pro_add_node, main_panel, compositor_pro_props ]

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
