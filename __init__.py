bl_info = {
    "name" : "Compositor Pro",
    "author" : "Riley Rivera, Nihal Rahman",
    "location": "Blender Compositor",
    "blender" : (4, 0, 0),
    "version" : (1, 0, 0),
    "category" : "Compositing",
    "doc_url": "https://comppro.anticode.me/",
}

if 'bpy' in locals(): # This means that an older version of the addon was previously installed
    import importlib
    if 'utility' in locals():
        importlib.reload(utility)
    if 'preferences' in locals():
        importlib.reload(preferences)

import bpy
import webbrowser
from bpy.types import Operator, Menu, Panel, PropertyGroup
from bpy.props import StringProperty, FloatProperty, EnumProperty, PointerProperty
from bpy_extras.io_utils import ImportHelper
from . utility import *
from . preferences import *

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
    
    def draw_header(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.operator('comp_pro.open_docs', text='', icon='QUESTION')
        row.operator('comp_pro.join_discord', text='', icon_value=utility_icons['Discord_icon.png'].icon_id)

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
                optimization_menu = panel.box()
                optimization_menu.label(text="Optimization Menu")
                optimization_menu.operator('comp_pro.enable_optimizations', text="Enable Optimizations", icon='ERROR')
                panel.separator()

            add_panel = panel.box()
            add_panel.label(text="Add Compositor Pro Node")
            add_panel.prop(props, 'search_string')
            add_panel = add_panel.column(align=True)
            add_panel.prop(props, 'categories', text='')
            add_panel.template_icon_view(props, 'comp_{}'.format(props.categories), show_labels=True, scale_popup=prefs.thumbnail_size)
            add_button = add_panel.row(align=True)
            add_button.operator('comp_pro.add_node', text="Add {}".format(eval(get_active_node_path(props.categories)))).choice = props.categories
            # add_button.operator('comp_pro.open_info', text='', icon='QUESTION').choice = props.categories # This is the documentation button. Docs aren't ready.
            add_button.operator(
                'comp_pro.toggle_favorite',
                text='',
                icon='SOLO_OFF' if not check_favorite(context, eval(get_active_node_path(props.categories))) else 'SOLO_ON',
                depress=check_favorite(context, eval(get_active_node_path(props.categories)))
            ).choice = props.categories
            panel.separator()
            mixer_panel = panel.box()
            mixer_panel.label(text="Add Mix Node")
            mixer_panel = mixer_panel.column(align=True)
            mixer_options = mixer_panel.row(align=True)
            mixer_options.prop(props, 'mixer_blend_type', text='')
            mixer_options.prop(props, 'mixer_fac', text='')
            mixer_panel.operator('comp_pro.add_mixer', text="Add")

            panel.separator()
            credit_box = panel.box()
            version_row = credit_box.row()
            version_row.alignment = 'CENTER'
            version_row.label(text="Compositor Pro {}.{}.{}".format(bl_info['version'][0], bl_info['version'][1], bl_info['version'][2]))
            credits_row = credit_box.row()
            credits_row.alignment = 'CENTER'
            credits_row.scale_y = 0.25
            credits_row.enabled = False
            credits_row.label(text="Riley Rivera")
            nihal_row = credit_box.row()
            nihal_row.alignment = 'CENTER'
            nihal_row.scale_y = 0.25
            nihal_row.enabled = False
            nihal_row.label(text="Nihal Rahman")

class compositor_pro_props(PropertyGroup):
    categories: EnumProperty(
        name='Category',
        items=make_cat_list
    )
    n_categories: EnumProperty(
        name='Category',
        items=(
            ('fav_rad', 'Favorites', 'Your favorite nodes'),
            ('custom_rad', 'Custom Nodes', 'Nodes you made yourself')
        ),
        default='fav_rad'
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
    search_string: StringProperty(
        name='Search',
        update=update_search_cat
    )

    def import_fav_rad(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='fav_rad')

    def import_custom_rad(self, context):
        bpy.ops.comp_pro.add_node('INVOKE_DEFAULT', choice='custom_rad')

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
    comp_custom_rad: EnumProperty(
        items=previews_from_custom,
        update=import_custom_rad
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
        desired_mode = 'OBJECT' if bpy.app.version < (4, 1, 0) else 'SELECT'
        if bpy.context.active_object != None and bpy.context.active_object.mode != desired_mode:
            bpy.ops.object.mode_select(mode=desired_mode)
        #append
        if not bpy.data.node_groups.get(group_name):
            if self.choice != 'custom' and not (self.choice == 'fav' and get_fav_dir(context, group_name) == 'custom'):
                bpy.ops.wm.append(filename=group_name, directory=file_path_node_tree)
            else:
                bpy.ops.wm.append(filename=group_name, directory=join(get_custom_path(group_name), 'NodeTree'))
        #add to scene
        new_group = nodes.new(type='CompositorNodeGroup')
        new_group.node_tree = bpy.data.node_groups.get(group_name)
        if bpy.data.node_groups.get(group_name) is not None:
            new_group.node_tree.use_fake_user = False
        else:
            self.report({'ERROR'}, 'This node does not exist in data file.')
        #fix nodes
        recursive_node_fixer(new_group, context)
        #attatch to cursor
        new_group.width = get_preferences(context).node_width
        new_group.location = context.space_data.cursor_location
        for n in nodes:
            n.select = n == new_group
        bpy.ops.node.translate_attach('INVOKE_DEFAULT')
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
            add_favorite(context, node)
        return {'FINISHED'}

class compositor_pro_open_info(Operator):
    bl_idname = 'comp_pro.open_info'
    bl_description = 'Open the documentation for the given node'
    bl_category = 'Node'
    bl_label = 'Open Info'

    choice: StringProperty()

    def invoke(self, context, event):
        node = eval(get_active_node_path(self.choice))
        node_link = node.lower().replace(' ', '_')
        cat = self.choice
        if self.choice == 'fav':
            cat = get_category_from_node(node)
        webbrowser.open('https://comppro.anticode.me/nodes/{}/{}.html'.format(cat, node_link))
        return {'FINISHED'}

class compositor_pro_open_docs(Operator):
    bl_idname = 'comp_pro.open_docs'
    bl_description = 'Open Compositor Pro documentation'
    bl_category = 'Node'
    bl_label = 'Open Documentation'

    def invoke(self, context, event):
        webbrowser.open(bl_info['doc_url'])
        return {'FINISHED'}

class compositor_pro_join_discord(Operator):
    bl_idname = 'comp_pro.join_discord'
    bl_description = 'Join the Artum Discord for Compositor Pro'
    bl_category = 'Node'
    bl_label = 'Join Discord'

    def invoke(self, context, event):
        webbrowser.open('https://discord.gg/g5tUfzjqaj')
        return {'FINISHED'}

classes = [ NodeColors, compositor_pro_add_mixer, compositor_pro_enable_optimizations,
            compositor_pro_enable_nodes, compositor_pro_add_node, main_panel, compositor_pro_props,
            compositor_pro_open_info, compositor_pro_toggle_favorite,
            compositor_pro_join_discord, compositor_pro_open_docs,
            compositor_pro_addon_preferences ]

kmd = [None, None]

def register():
    if is_broken_cm():
        raise 'IF YOU SEE THIS ERROR, READ THIS: You have an invalid config.ocio configuration. Please add Filmic Log for Blender 3.x or AgX Log for Blender 4.x to your config.ocio'
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.compositor_pro_props = PointerProperty(type=compositor_pro_props)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.compositor_pro_props
    utility.cleanup()

if __name__ == "__main__":
    register()
