bl_info = {
    "name" : "Compositor Pro",
    "author" : "anticode-403, Nihal Rahman",
    "blender" : (3, 6, 0),
    "version" : (0, 0, 10),
    "category" : "Compositing"
}

import bpy
from bpy_extras.io_utils import ImportHelper
from . utility import previews_from_favorites, get_active_node_path, rem_favorite, add_favorite, check_favorite, color_management_list_to_tuples, recursive_node_fixer, previews_from_directory_items, has_color_management, preview_collections, file_path_node_tree

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
            if bpy.app.version < (4, 0, 0) and not has_color_management():
                panel.label(text="Update to Blender to 4.0 or install CM+6.1")
            if not compositor.use_groupnode_buffer or not compositor.use_two_pass:
                panel.operator('comp_pro.enable_optimizations', text="Enable Optimizations")
            add_panel = panel.box()
            add_panel.prop(settings, 'categories')
            icon_view_row = add_panel.row(align=True)
            favorite_info_col = icon_view_row.column(align=True)
            favorite_info_col.operator(
                'comp_pro.toggle_favorite',
                text='',
                icon='HEART' if not check_favorite(eval(get_active_node_path(settings.categories))) else 'FUND',
                depress=check_favorite(eval(get_active_node_path(settings.categories)))
            ).choice = settings.categories
            favorite_info_col.operator('comp_pro.open_info', text='', icon='QUESTION').choice = settings.categories
            icon_view_row.template_icon_view(settings, 'comp_'+str(settings.categories), show_labels=True, scale_popup=8)
            add_button = add_panel.row(align=True)
            add_button.operator('comp_pro.add_node', text="Add").choice = settings.categories
            add_button.prop(settings, 'quick_add', text='', icon='TIME')
            if compositor.nodes.active is not None and compositor.nodes.active.bl_idname == 'CompositorNodeGroup' and compositor.nodes.active.node_tree.name == 'Grain+':
                panel.separator()
                panel.operator('comp_pro.replace_grain', text="Replace Grain Texture")
            panel.separator()
            mixer_panel = panel.box()
            mixer_panel.label(text="Add Mix Node")
            mixer_options = mixer_panel.row(align=True)
            mixer_options.prop(settings, 'mixer_blend_type', text='')
            mixer_options.prop(settings, 'mixer_fac', text='')
            mixer_panel.operator('comp_pro.add_mixer', text="Add")
            panel.separator()
            colorgrade_panel = panel.box()
            colorgrade_panel.label(text="Color Grading")
            create_active_colorspace = colorgrade_panel.row(align=True)
            create_active_colorspace.prop(settings, 'create_active_colorspace_sequencer', text='')
            create_active_colorspace.operator('comp_pro.create_active_colorspace', text="Create Active Colorspace")

class compositor_pro_props(bpy.types.PropertyGroup):
    categories: bpy.props.EnumProperty(
        name='Category',
        items=(
            ('mixed', 'Mixed Effects', 'mixed'),
            ('unmixed', 'Unmixed Effects', 'unmixed'),
            ('color', 'Color Grading', 'color'),
            ('batches', 'Batches', 'batches'),
            ('utilities', 'Utilities', 'utilities'),
            ('dev', 'Dev Tools', 'dev'),
            ('favorites', 'Favorites', 'favorites'),
        ),
        default='mixed'
    )
    quick_add: bpy.props.BoolProperty(
        name = 'Quick Add',
        description = '',
        default = False
    )
    mixer_blend_type: bpy.props.EnumProperty(
        name='Mixer Blend Type',
        items=(
            ('MIX', 'Mix', 'MIX'),
            ('ADD', 'Add', 'ADD'),
        ),
        default='MIX'
    )
    mixer_fac: bpy.props.FloatProperty(
        name='Mixer Factor',
        subtype='FACTOR',
        max=1.0,
        min=0.0,
        default=0.1
    )
    create_active_colorspace_sequencer: bpy.props.EnumProperty(
        name='Active Colorspace Sequencer',
        items=tuple(map(color_management_list_to_tuples, bpy.types.ColorManagedInputColorspaceSettings.bl_rna.properties['name'].enum_items)),
        default='AgX Base Log'
    )

    def import_mixed(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='mixed')
    def import_unmixed(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='unmixed')
    def import_color(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='color')
    def import_batches(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='batches')
    def import_utilities(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='utilities')
    def import_dev(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='dev')
    def import_fav(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='fav')

    def quick_add_mixed(self, context):
        if context.scene.compositor_pro_props.quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='mixed')
    def quick_add_unmixed(self, context):
        if context.scene.compositor_pro_props.quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='unmixed')
    def quick_add_color(self, context):
        if context.scene.compositor_pro_props.quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='color')
    def quick_add_batches(self, context):
        if context.scene.compositor_pro_props.quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='batches')
    def quick_add_utilities(self, context):
        if context.scene.compositor_pro_props.quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='utilities')
    def quick_add_dev(self, context):
        if context.scene.compositor_pro_props.quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='dev')
    def quick_add_fav(self, context):
        if context.scene.compositor_pro_props.quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='fav')

    comp_mixed: bpy.props.EnumProperty(
        items=previews_from_directory_items(preview_collections['mixed']),
        update=quick_add_mixed
    )
    comp_unmixed: bpy.props.EnumProperty(
        items=previews_from_directory_items(preview_collections['unmixed']),
        update=quick_add_unmixed
    )
    comp_color: bpy.props.EnumProperty(
        items=previews_from_directory_items(preview_collections['color']),
        update=quick_add_color
    )
    comp_batches: bpy.props.EnumProperty(
        items=previews_from_directory_items(preview_collections['batches']),
        update=quick_add_batches
    )
    comp_utilities: bpy.props.EnumProperty(
        items=previews_from_directory_items(preview_collections['utilities']),
        update=quick_add_utilities
    )
    comp_dev: bpy.props.EnumProperty(
        items=previews_from_directory_items(preview_collections['dev']),
        update=quick_add_dev
    )
    comp_fav: bpy.props.EnumProperty(
        items=previews_from_favorites(preview_collections['fav']),
        update=quick_add_fav
    )

class compositor_pro_add_node(bpy.types.Operator):
    bl_idname = 'comp_pro.add_node'
    bl_description = 'Add Compositor Node'
    bl_category = 'Node'
    bl_label = 'Add Node'

    choice: bpy.props.StringProperty()

    def invoke(self, context, event):
        #find node
        group_name = eval(get_active_node_path(self.choice))
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

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        grain_node = context.scene.node_tree.nodes.active
        grain_texture_node = None
        for node in grain_node.node_tree.nodes:
            if node.name == 'Grain':
                grain_texture_node = node
        new_texture = bpy.data.images.load(filepath = self.filepath)
        grain_texture_node.image = new_texture
        return {'FINISHED'}

class compositor_pro_add_mixer(bpy.types.Operator):
    bl_idname = 'comp_pro.add_mixer'
    bl_description = 'Add Mix node, with connections if possible.'
    bl_category = 'Node'
    bl_label = 'Add Mixer'

    def invoke(self, context, event):
        props = context.scene.compositor_pro_props
        node_tree = context.scene.node_tree
        nodes = node_tree.nodes
        mixer = nodes.new(type='CompositorNodeMixRGB')
        selected_nodes = []
        for n in nodes:
            if not n.select or n == mixer:
                continue
            if len(n.outputs) == 0:
                continue
            selected_nodes.append(n)
        if len(selected_nodes) == 1:
            node_tree.links.new(eval(selected_nodes[0].outputs[0].path_from_id()), eval(mixer.inputs[1].path_from_id()))
        elif len(selected_nodes) == 2:
            primary_node = selected_nodes[0]
            secondary_node = selected_nodes[1]
            if nodes.active in selected_nodes:
                selected_nodes.remove(nodes.active)
                secondary_node = nodes.active
                primary_node = selected_nodes[0]
            node_tree.links.new(eval(primary_node.outputs[0].path_from_id()), eval(mixer.inputs[1].path_from_id()))
            node_tree.links.new(eval(secondary_node.outputs[0].path_from_id()), eval(mixer.inputs[2].path_from_id()))
        mixer.inputs[0].default_value = props.mixer_fac
        mixer.blend_type = props.mixer_blend_type
        mixer.location = context.space_data.cursor_location
        for n in nodes:
            n.select = n == mixer
        bpy.ops.node.translate_attach('INVOKE_DEFAULT')
        return {'FINISHED'}

class compositor_pro_create_active_colorspace(bpy.types.Operator):
    bl_idname='comp_pro.create_active_colorspace'
    bl_description='Create an active colorspace node block'
    bl_category='Node'
    bl_label='Create Active Colorspace'

    def invoke(self, context, event):
        props = context.scene.compositor_pro_props
        node_tree = context.scene.node_tree
        nodes = node_tree.nodes
        to_active = nodes.new(type='CompositorNodeConvertColorSpace') # from Linear Rec.709 to create_active_colorspace_sequencer
        from_active = nodes.new(type='CompositorNodeConvertColorSpace') # from create_active_colorspace_sequencer to Linear Rec.709
        to_active.from_color_space = 'Linear Rec.709'
        to_active.to_color_space = props.create_active_colorspace_sequencer
        from_active.from_color_space = props.create_active_colorspace_sequencer
        from_active.to_color_space = 'Linear Rec.709'
        if nodes.active and nodes.active.select and len(nodes.active.inputs) != 0 and len(nodes.active.outputs) != 0:
            input_socket = nodes.active.inputs[0]
            for socket in nodes.active.inputs:
                if socket.type == 'RGBA':
                    input_socket = socket
                    break
            for link in nodes.active.internal_links:
                if link.to_socket == nodes.active.outputs[0]:
                    input_socket = link.from_socket
            for link in node_tree.links.values():
                if link.to_node == nodes.active and link.to_socket.type == 'RGBA':
                    node_tree.links.new(eval(link.from_socket.path_from_id()), eval(to_active.inputs[0].path_from_id()))
                elif link.from_node == nodes.active and link.from_socket == nodes.active.outputs[0]:
                    node_tree.links.new(eval(from_active.outputs[0].path_from_id()), eval(link.to_socket.path_from_id()))
            node_tree.links.new(eval(from_active.inputs[0].path_from_id()), eval(nodes.active.outputs[0].path_from_id()))
            node_tree.links.new(eval(input_socket.path_from_id()), eval(to_active.outputs[0].path_from_id()))
            to_active.location = (nodes.active.location.x - to_active.width - 100, nodes.active.location.y)
            from_active.location = (nodes.active.location.x + nodes.active.width + 100, nodes.active.location.y)
        else:
            node_tree.links.new(eval(to_active.outputs[0].path_from_id()), eval(from_active.inputs[0].path_from_id()))
            to_active.location = (context.space_data.cursor_location.x - 150, context.space_data.cursor_location.y)
            from_active.location = (context.space_data.cursor_location.x + 150, context.space_data.cursor_location.y)
            for n in nodes:
                n.select = n == to_active or n == from_active
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

class compositor_pro_enable_nodes(bpy.types.Operator):
    bl_idname = 'comp_pro.enable_nodes'
    bl_description = 'Enable compositor nodes'
    bl_category = 'Node'
    bl_label = 'Enable Nodes'

    def invoke(self, context, event):
        context.scene.use_nodes = True
        return {'FINISHED'}

class compositor_pro_toggle_favorite(bpy.types.Operator):
    bl_idname = 'comp_pro.toggle_favorite'
    bl_description = 'Add a node to your favorites list'
    bl_category = 'Node'
    bl_label = 'Add Favorite'

    choice: bpy.props.StringProperty()

    def invoke(self, context, event):
        node = eval(eval(get_active_node_path(self.choice)))
        is_fav = check_favorite(node)
        if is_fav:
            rem_favorite(node)
        else:
            add_favorite(self.choice, node)
        return {'FINISHED'}

class compositor_pro_open_info(bpy.types.Operator):
    bl_idname = 'comp_pro.open_info'
    bl_description = 'Open the documentation for the given node'
    bl_category = 'Node'
    bl_label = 'Open Info'

    choice: bpy.props.StringProperty()

    def invoke(self, context, event):
        node = eval(eval(get_active_node_path(self.choice)))
        print(node)
        return {'FINISHED'}

classes = [ compositor_pro_add_mixer, compositor_pro_replace_grain, compositor_pro_enable_optimizations,
            compositor_pro_enable_nodes, compositor_pro_add_node, main_panel, compositor_pro_props,
            compositor_pro_create_active_colorspace, compositor_pro_open_info, compositor_pro_toggle_favorite ]

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
