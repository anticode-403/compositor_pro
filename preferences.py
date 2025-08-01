import bpy
import rna_keymap_ui
import json
import re
from bpy.types import AddonPreferences, PropertyGroup
from bpy.props import StringProperty, BoolProperty, FloatProperty, FloatVectorProperty, PointerProperty
from os import remove
from os.path import join
from . previews import data_dir, custom_node_folder, process_favorites_previews

favorite_regexp = r'[^:]+:[^:]+;'
customs_regexp = r'[^;]+;'

def add_favorite(context, node):
    favorite_string = get_preferences(context).favorites
    favs = re.findall(favorite_regexp, favorite_string)
    category = get_category_from_node(node)
    favs.append('{}:{};'.format(category, node))
    new_string = ''.join(favs)
    get_preferences(context).favorites = new_string
    process_favorites_previews(favs)
    return

def rem_favorite(context, node):
    favorite_string = get_preferences(context).favorites
    favs = re.findall(favorite_regexp, favorite_string)
    for favorite in favs:
        cat, fnode = favorite.removesuffix(';').split(':')
        if fnode == node:
            favs.remove(favorite)
    new_string = ''.join(favs)
    get_preferences(context).favorites = new_string
    if len(favs) != 0:
        process_favorites_previews(favs)
    return

def check_favorite(context, node):
    favorite_string = get_preferences(context).favorites
    favs = re.findall(favorite_regexp, favorite_string)
    if len(favs) == 0:
        return False
    process_favorites_previews(favs)
    for favorite in favs:
        cat, fnode = favorite.removesuffix(';').split(':')
        if fnode == node:
            return True
    return False

def get_fav_dir(context, node):
    favorite_string = get_preferences(context).favorites
    favs = re.findall(favorite_regexp, favorite_string)
    for favorite in favs:
        cat, fnode = favorite.removesuffix(';').split(':')
        if fnode == node:
            return cat

def has_favorites(context):
    favorite_string = get_preferences(context).favorites
    favs = re.findall(favorite_regexp, favorite_string)
    if len(favs) == 0:
        return False
    else:
        return True
    
def get_node_data():
    raw = open(join(data_dir, 'nodes.json'))
    data = json.load(raw)
    raw.close()
    return data

def get_data_from_node(category, node_name):
    data = get_node_data()
    for node in data[category]:
        if node['name'] == node_name:
            return node

def get_custom_path(node_name):
    return join(custom_node_folder, '{}.blend'.format(node_name))

def write_custom_node(nodegroup):
    bpy.data.libraries.write(get_custom_path(nodegroup.node_tree.name), {nodegroup.node_tree}, fake_user=True, path_remap='RELATIVE')
    return

def delete_custom_node(node_name):
    node_path = get_custom_path(node_name)
    try:
        remove(node_path)
        bpy.data.libraries.remove(bpy.data.libraries[os.path.basename(node_path)])
    except:
        print('Could not find custom node. Did something go wrong?')

def get_hotkey_entry_item(km, kmi_name, kmi_value):
    for i, km_item in enumerate(km.keymap_items):
        if km.keymap_items.keys()[i] == kmi_name:
            if km.keymap_items[i].properties.name == kmi_value:
                return km_item
    return None

def get_preferences(context):
    return context.preferences.addons[__package__].preferences

def get_all_from_node(node_name):
    data = get_node_data()
    for cat in data.keys():
        for node in data[cat]:
            if node['name'] == node_name:
                return cat, node
    return None, None

def get_category_from_node(node_name):
    data = get_node_data()
    for cat in data.keys():
        for node in data[cat]:
            if node['name'] == node_name:
                return cat

def has_custom_nodes(context):
    if get_preferences(context).customs != '':
        if len(custom_col.my_previews) == 0:
            process_custom_previews(context)
        return True
    return False

class NodeColors(PropertyGroup):
    mixed: FloatVectorProperty(
        name="Mixed",
        subtype='COLOR',
        default=[0.345098, 0.152941, 0.113725],
        soft_min=0,
        soft_max=1
    )
    unmixed: FloatVectorProperty(
        name="Unmixed",
        subtype='COLOR',
        default=[0.101961, 0.203922, 0.270588],
        soft_min=0,
        soft_max=1
    )
    color: FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=[0.25098, 0.105882, 0.168627],
        soft_min=0,
        soft_max=1
    )
    batches: FloatVectorProperty(
        name="Batches",
        subtype='COLOR',
        default=[0.176471, 0.160784, 0.25098],
        soft_min=0,
        soft_max=1
    )
    utilities: FloatVectorProperty(
        name="Utilities",
        subtype='COLOR',
        default=[0.098039, 0.184314, 0.176471],
        soft_min=0,
        soft_max=1
    )
    dev: FloatVectorProperty(
        name="Dev Tools",
        subtype='COLOR',
        default=[0.090196, 0.090196, 0.090196],
        soft_min=0,
        soft_max=1
    )
    custom: FloatVectorProperty(
        name="Custom",
        subtype='COLOR',
        default=[0.090196, 0.090196, 0.090196],
        soft_min=0,
        soft_max=1
    )

class compositor_pro_addon_preferences(AddonPreferences):

    bl_idname = __package__

    favorites: StringProperty(
        name="Favorites",
        description="A list of your favorite nodes",
        default=''
    )
    customs: StringProperty(
        name='Custom Nodes',
        description="A list of your custom nodes",
        default=''
    )
    quick_add: BoolProperty(
        name="Quick Add",
        description="Add nodes instantly when selected",
        default=False
    )
    dev_insights: BoolProperty(
        name="Developer Insights",
        description="Do not turn this on unless you are trying to debug and know what you are doing",
        default=False
    )
    dev_tools: BoolProperty(
        name="Dev Tools",
        description="A collection of nodes used for developing Compositor Pro",
        default=False
    )
    thumbnail_size: FloatProperty(
        name="Thumbnail Size",
        description="The size of node thumbnails when in the selection menu",
        default=6.0,
        min=1,
        max=100,
        subtype='UNSIGNED'
    )
    node_width: FloatProperty(
        name="Node Width",
        description="The width of nodes when they are imported",
        default=140,
        min=140,
        max=500,
        subtype='UNSIGNED'
    )
    color_nodes: BoolProperty(
        name="Use Colored Nodes",
        description="Color nodes by category. It just looks nice",
        default=True
    )
    node_colors: PointerProperty(
        name="Node Colors",
        type=NodeColors
    )
    
    invert_mix_options: BoolProperty(
        name="Invert Mix Order",
        description="Invert the order that Add Mix Node processes selections.",
        default=False
    )

    def draw(self, context):
        layout = self.layout
        # layout.label(text='Compositor Pro Preferences')
        box = layout.box()
        box.label(text="Addon Panel")
        box.prop(self, 'quick_add')
        box.prop(self, 'invert_mix_options')
        box.prop(self, 'color_nodes')
        if self.color_nodes:
            colors_box = box.box().column(align=True)
            colors_box.label(text="Node Colors")
            color_row = colors_box.row()
            color_row.prop(self.node_colors, 'mixed', icon='NODE_COMPOSITING')
            color_row = colors_box.row()
            color_row.prop(self.node_colors, 'unmixed', icon='NODE_COMPOSITING')
            color_row = colors_box.row()
            color_row.prop(self.node_colors, 'color', icon='NODE_COMPOSITING')
            color_row = colors_box.row()
            color_row.prop(self.node_colors, 'batches', icon='NODE_COMPOSITING')
            color_row = colors_box.row()
            color_row.prop(self.node_colors, 'utilities', icon='NODE_COMPOSITING')
            color_row = colors_box.row()
            color_row.prop(self.node_colors, 'custom', icon='NODE_COMPOSITING')
            if self.dev_tools:
                color_row = colors_box.row()
                color_row.prop(self.node_colors, 'dev')
        box.prop(self, 'thumbnail_size')
        box.prop(self, 'node_width')
        box = layout.box()
        box.label(text="Keyboard Shortcuts")
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user
        km = kc.keymaps['Node Generic']
        kmi = get_hotkey_entry_item(km, 'wm.call_menu_pie', 'COMPPRO_MT_radial_menu')
        if kmi:
            box.context_pointer_set('keymap', km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, box, 0)
        box = layout.box()
        box.label(text="Other Options")
        box.prop(self, 'dev_tools')
        box.prop(self, 'dev_insights')
        if self.dev_insights:
            box = layout.box()
            box.label(text="Developer Insights")
            box.prop(self, 'favorites')
            box.prop(self, 'customs')