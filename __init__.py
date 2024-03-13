bl_info = {
    "name" : "Compositor Pro",
    "author" : "anticode-403, Nihal Rahman",
    "location": "Blender Compositor",
    "blender" : (3, 6, 0),
    "version" : (0, 5, 1),
    "category" : "Compositing",
    # "doc_url": "https://comppro.anticode.me/", # Docs aren't ready.
}

if 'bpy' in locals(): # This means that an older version of the addon was previously installed
    import importlib
    if 'utility' in locals():
        importlib.reload(utility)
    if 'preferences' in locals():
        importlib.reload(preferences)

import bpy
from bpy.types import Operator, Menu, Panel, PropertyGroup
from bpy.props import StringProperty, FloatProperty, EnumProperty, PointerProperty
from bpy_extras.io_utils import ImportHelper
from . utility import *
from . preferences import compositor_pro_addon_preferences

class main_panel(Panel):
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
        props = context.scene.compositor_pro_props
        prefs = get_preferences(context)

        panel = layout.row()
        if not context.space_data.tree_type == 'CompositorNodeTree':
            return
        if not context.scene.use_nodes:
            panel.operator('comp_pro.enable_nodes', text="Enable Nodes")
        else:
            compositor = context.scene.node_tree
            panel = panel.column()
            # if is_b3_cm():
            #     panel.label(text="Please update to Blender 4.0")
            if not compositor.use_groupnode_buffer or not compositor.use_two_pass or compositor.use_opencl:
                panel.operator('comp_pro.enable_optimizations', text="Enable Optimizations")
                panel.separator()
            add_panel = panel.box()
            add_panel.label(text="Add Compositor Pro Node")
            add_panel.prop(props, 'search_string')
            add_panel = add_panel.column(align=True)
            add_panel.prop(props, 'categories', text='')
            add_panel.template_icon_view(props, 'comp_{}'.format((props.categories)), show_labels=True, scale_popup=prefs.thumbnail_size)
            add_button = add_panel.row(align=True)
            add_button.operator('comp_pro.add_node', text="Add {}".format(eval(get_active_node_path(props.categories)))).choice = props.categories
            # add_button.operator('comp_pro.open_info', text='', icon='QUESTION').choice = props.categories # This is the documentation button. Docs aren't ready.
            if props.categories == 'custom':
                add_button.operator('comp_pro.delete_custom', text='', icon='TRASH')
            add_button.operator(
                'comp_pro.toggle_favorite',
                text='',
                icon='SOLO_OFF' if not check_favorite(context, eval(get_active_node_path(props.categories))) else 'SOLO_ON',
                depress=check_favorite(context, eval(get_active_node_path(props.categories)))
            ).choice = props.categories
            if compositor.nodes.active is not None and compositor.nodes.active.bl_idname == 'CompositorNodeGroup' and 'Grain' in compositor.nodes.active.node_tree.name:
                panel.separator()
                panel.operator('comp_pro.replace_grain', text="Replace Grain Texture")
            panel.separator()
            mixer_panel = panel.box()
            mixer_panel.label(text="Add Mix Node")
            mixer_panel = mixer_panel.column(align=True)
            mixer_options = mixer_panel.row(align=True)
            mixer_options.prop(props, 'mixer_blend_type', text='')
            mixer_options.prop(props, 'mixer_fac', text='')
            mixer_panel.operator('comp_pro.add_mixer', text="Add")
            panel.separator()
            colorgrade_panel = panel.box()
            colorgrade_panel.label(text="Color Grading")
            add_process_colorspace = colorgrade_panel.row(align=True)
            add_process_colorspace.prop(props, 'add_process_colorspace_sequencer', text='')
            add_process_colorspace.operator('comp_pro.add_process_colorspace', text="Add Process Space")
            panel.operator('comp_pro.add_custom')

class COMPPRO_MT_radial_menu(Menu):
    bl_label = 'Compositor Pro {}.{}.{}'.format(bl_info['version'][0], bl_info['version'][1], bl_info['version'][2])

    def draw(self, context):
        if not context.space_data.tree_type == 'CompositorNodeTree':
            return
        props = context.scene.compositor_pro_props
        prefs = get_preferences(context)

        pie = self.layout.menu_pie()
        box = pie.column(align=True)
        if has_favorites(context):
            box.label(text="Favorite Nodes")
            box.template_icon_view(props, 'comp_fav_rad', show_labels=True, scale_popup=prefs.thumbnail_size)
        box = pie.column(align=True)
        mixer_options = box.row(align=True)
        mixer_options.prop(props, 'mixer_fac', text='Fac')
        mixer_options.prop(props, 'mixer_blend_type', text='')
        box.operator('comp_pro.add_mixer', text="Add Mix Node")
        box.separator()
        add_process_colorspace = box.row(align=True)
        add_process_colorspace.operator('comp_pro.add_process_colorspace', text="Add Process Space")
        add_process_colorspace.prop(props, 'add_process_colorspace_sequencer', text='')

class compositor_pro_props(PropertyGroup):
    categories: EnumProperty(
        name='Category',
        items=make_cat_list
    )
    mixer_blend_type: EnumProperty(
        name='Mixer Blend Type',
        items=(
            ('MIX', 'Mix', 'Mix two outputs together'),
            ('ADD', 'Add', 'Add one output to another'),
            ('MULTIPLY', 'Multiply', 'Multiply two outputs together'),
            ('COLOR', 'Color', 'Mix only Hue/Saturation between two outputs'),
        ),
        default='MIX'
    )
    mixer_fac: FloatProperty(
        name='Mixer Factor',
        subtype='FACTOR',
        max=1.0,
        min=0.0,
        default=0.1
    )
    add_process_colorspace_sequencer: EnumProperty(
        name='Active Colorspace Sequencer',
        items=tuple(map(color_management_list_to_tuples, bpy.types.ColorManagedInputColorspaceSettings.bl_rna.properties['name'].enum_items)),
        default=get_default_process_space()
    )
    search_string: StringProperty(
        name='Search',
        update=update_search_cat
    )

    def import_fav_rad(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='fav_rad')

    def quick_add_all(self, context):
        if get_preferences(context).quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='all')
    def quick_add_mixed(self, context):
        if get_preferences(context).quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='mixed')
    def quick_add_unmixed(self, context):
        if get_preferences(context).quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='unmixed')
    def quick_add_color(self, context):
        if get_preferences(context).quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='color')
    def quick_add_batches(self, context):
        if get_preferences(context).quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='batches')
    def quick_add_utilities(self, context):
        if get_preferences(context).quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='utilities')
    def quick_add_dev(self, context):
        if get_preferences(context).quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='dev')
    def quick_add_fav(self, context):
        if get_preferences(context).quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='fav')
    def quick_add_search(self, context):
        if get_preferences(context).quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='search')
    def quick_add_custom(self, context):
        if get_preferences(context).quick_add:
            bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='custom')

    comp_all: EnumProperty(
        items=preview_all(),
        update=quick_add_all
    )
    comp_mixed: EnumProperty(
        items=previews_from_directory_items(preview_collections['mixed']),
        update=quick_add_mixed
    )
    comp_unmixed: EnumProperty(
        items=previews_from_directory_items(preview_collections['unmixed']),
        update=quick_add_unmixed
    )
    comp_color: EnumProperty(
        items=previews_from_directory_items(preview_collections['color']),
        update=quick_add_color
    )
    comp_batches: EnumProperty(
        items=previews_from_directory_items(preview_collections['batches']),
        update=quick_add_batches
    )
    comp_utilities: EnumProperty(
        items=previews_from_directory_items(preview_collections['utilities']),
        update=quick_add_utilities
    )
    comp_dev: EnumProperty(
        items=previews_from_directory_items(preview_collections['dev']),
        update=quick_add_dev
    )
    comp_fav: EnumProperty(
        items=previews_from_favorites,
        update=quick_add_fav
    )
    comp_fav_rad: EnumProperty(
        items=previews_from_favorites,
        update=import_fav_rad
    )
    comp_search: EnumProperty(
        items=previews_from_search,
        update=quick_add_search
    )
    comp_custom: EnumProperty(
        items=previews_from_custom,
        update=quick_add_custom
    )

class compositor_pro_add_node(Operator):
    bl_idname = 'comp_pro.add_node'
    bl_description = 'Add Compositor Node'
    bl_category = 'Node'
    bl_label = 'Add Node'

    choice: StringProperty()

    def invoke(self, context, event):
        #find node
        group_name = eval(get_active_node_path(self.choice))
        if group_name == '':
            return {'CANCELLED'}
        node_tree = context.scene.node_tree
        nodes = node_tree.nodes
        #append
        if not bpy.data.node_groups.get(group_name):
            if self.choice != 'custom' and (self.choice != 'fav' and get_fav_dir(group_name) != 'custom'):
                bpy.ops.wm.append(filename=group_name, directory=file_path_node_tree)
            else:
                bpy.ops.wm.append(filename=group_name, directory=join(custom_node_file, 'NodeTree'))
        #add to scene
        new_group = nodes.new(type='CompositorNodeGroup')
        new_group.node_tree = bpy.data.node_groups.get(group_name)
        try:
            new_group.node_tree.use_fake_user = False
        except:
            self.report('ERROR', 'This node does not exist in data file.')
        #fix nodes
        recursive_node_fixer(new_group, context)
        #attatch to cursor
        new_group.location = context.space_data.cursor_location
        for n in nodes:
            n.select = n == new_group
        bpy.ops.node.translate_attach('INVOKE_DEFAULT')
        return {'FINISHED'}

class compositor_pro_replace_grain(Operator, ImportHelper):
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

class compositor_pro_add_mixer(Operator):
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
            if get_preferences(context).invert_mix_options:
                primary_node = selected_nodes[1]
                secondary_node = selected_nodes[0]
            if nodes.active in selected_nodes:
                selected_nodes.remove(nodes.active)
                if get_preferences(context).invert_mix_options:
                    primary_node = nodes.active
                    secondary_node = selected_nodes[0]
                else:
                    primary_node = selected_nodes[0]
                    secondary_node = nodes.active
            node_tree.links.new(eval(primary_node.outputs[0].path_from_id()), eval(mixer.inputs[1].path_from_id()))
            node_tree.links.new(eval(secondary_node.outputs[0].path_from_id()), eval(mixer.inputs[2].path_from_id()))
        mixer.inputs[0].default_value = props.mixer_fac
        mixer.blend_type = props.mixer_blend_type
        mixer.location = context.space_data.cursor_location
        for n in nodes:
            n.select = n == mixer
        bpy.ops.node.translate_attach('INVOKE_DEFAULT')
        return {'FINISHED'}

class compositor_pro_add_process_colorspace(Operator):
    bl_idname='comp_pro.add_process_colorspace'
    bl_description='Create an active colorspace node block'
    bl_category='Node'
    bl_label='Create Active Colorspace'

    def invoke(self, context, event):
        props = context.scene.compositor_pro_props
        node_tree = context.scene.node_tree
        nodes = node_tree.nodes
        to_active = nodes.new(type='CompositorNodeConvertColorSpace') # from Linear Rec.709 to add_process_colorspace_sequencer
        from_active = nodes.new(type='CompositorNodeConvertColorSpace') # from add_process_colorspace_sequencer to Linear Rec.709
        if is_b3_cm():
            to_active.from_color_space = 'Linear'
        else:
            to_active.from_color_space = 'Linear Rec.709'
        to_active.to_color_space = props.add_process_colorspace_sequencer
        from_active.from_color_space = props.add_process_colorspace_sequencer
        if is_b3_cm():
            from_active.to_color_space = 'Linear'
        else:
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

class compositor_pro_enable_optimizations(Operator):
    bl_idname = 'comp_pro.enable_optimizations'
    bl_description = 'Enable Blender compositor optimizations'
    bl_category = 'Node'
    bl_label = 'Enable Optimizations'

    def invoke(self, context, event):
        compositor = context.scene.node_tree
        compositor.use_groupnode_buffer = True
        compositor.use_two_pass = True
        # if bpy.app.version > (4, 0, 0):
        #     compositor.use_opencl = True
        # else:
        compositor.use_opencl = False
        return {'FINISHED'}

class compositor_pro_enable_nodes(Operator):
    bl_idname = 'comp_pro.enable_nodes'
    bl_description = 'Enable compositor nodes'
    bl_category = 'Node'
    bl_label = 'Enable Nodes'

    def invoke(self, context, event):
        context.scene.use_nodes = True
        return {'FINISHED'}

class compositor_pro_toggle_favorite(Operator):
    bl_idname = 'comp_pro.toggle_favorite'
    bl_description = 'Add a node to your favorites list'
    bl_category = 'Node'
    bl_label = 'Add Favorite'

    choice: StringProperty()

    def invoke(self, context, event):
        node = eval(get_active_node_path(self.choice))
        is_fav = check_favorite(context, node)
        if is_fav:
            rem_favorite(context, node)
            if not has_favorites(context):
                context.scene.compositor_pro_props.categories = 'mixed'
        else:
            add_favorite(context, self.choice, node)
        return {'FINISHED'}

class compositor_pro_open_info(Operator):
    bl_idname = 'comp_pro.open_info'
    bl_description = 'Open the documentation for the given node'
    bl_category = 'Node'
    bl_label = 'Open Info'

    choice: StringProperty()

    def invoke(self, context, event):
        node = eval(get_active_node_path(self.choice))
        print(node)
        return {'FINISHED'}

class compositor_pro_add_custom(Operator):
    bl_idname = 'comp_pro.add_custom'
    bl_description = 'Turn a nodegroup into a custom Compositor Pro node'
    bl_category = 'Node'
    bl_label = 'Add Custom Node'

    def invoke(self, context, event):
        nodegroup = context.scene.node_tree.nodes.active
        customs = re.findall(customs_regexp, get_preferences(context).customs)
        customs.append('{};'.format(nodegroup.node_tree.name))
        get_preferences(context).customs = ''.join(customs)
        write_custom_node(nodegroup)
        process_custom_previews(context)
        return {'FINISHED'}

class compositor_pro_remove_custom(Operator):
    bl_idname = 'comp_pro.delete_custom'
    bl_description = 'Delete a custom Compositor Pro node'
    bl_category = 'Node'
    bl_label = 'Delete Custom Node'

    def invoke(self, context, event):
        customs = re.findall(customs_regexp, get_preferences(context).customs)
        node_name = context.scene.compositor_pro_props.comp_custom
        customs.remove('{};'.format(node_name))
        get_preferences(context).customs = ''.join(customs)
        process_custom_previews(context)
        if len(customs) == 0:
            context.scene.compositor_pro_props.categories = 'all'
        return {'FINISHED'}

classes = [ compositor_pro_addon_preferences, compositor_pro_add_mixer, compositor_pro_replace_grain, compositor_pro_enable_optimizations,
            compositor_pro_enable_nodes, compositor_pro_add_node, main_panel, compositor_pro_props, compositor_pro_remove_custom,
            compositor_pro_add_process_colorspace, compositor_pro_open_info, compositor_pro_toggle_favorite, compositor_pro_add_custom,
            COMPPRO_MT_radial_menu ]

kmd = [None, None]

def register():
    if is_broken_cm():
        raise 'IF YOU SEE THIS ERROR, READ THIS: You have an invalid config.ocio configuration. Please add Filmic Log for Blender 3.x or AgX Log for Blender 4.x to your config.ocio'
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.compositor_pro_props = PointerProperty(type=compositor_pro_props)
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Node Generic', space_type='NODE_EDITOR', region_type='WINDOW')
    kmi = km.keymap_items.new('wm.call_menu_pie','V','PRESS')
    kmi.properties.name = 'COMPPRO_MT_radial_menu'
    kmi.active = True
    kmd[0] = km
    kmd[1] = kmi

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.compositor_pro_props
    wm = bpy.context.window_manager
    kmd[0].keymap_items.remove(kmd[1])
    wm.keyconfigs.addon.keymaps.remove(kmd[0])
    utility.cleanup()

if __name__ == "__main__":
    register()
