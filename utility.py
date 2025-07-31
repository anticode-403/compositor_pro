import bpy
import bpy.utils.previews # I don't understand why this fixes an issue, when it shouldn't do anything, but whatever
import os
from os.path import join, dirname, realpath, normpath, exists
import re
import json

preview_collections = {}
main_dir = dirname(realpath(__file__))
data_dir = join(main_dir,'data')
blender_file = join(data_dir,'Compositor_Pro.blend')
custom_node_folder = join(data_dir, 'customs')
custom_node_folder = join(data_dir, 'customs')
file_path_node_tree = join(blender_file,'NodeTree')
manifest_file = join(main_dir, 'blender_manifest.toml')
preview_dir = join(main_dir,'thumbnails')
preview_dirs = {
    'mixed_dir': join(preview_dir,'mixed'),
    'unmixed_dir': join(preview_dir,'unmixed'),
    'color_dir': join(preview_dir,'color'),
    'batches_dir': join(preview_dir,'batches'),
    'utilities_dir': join(preview_dir,'utilities'),
    'dev_dir': join(preview_dir,'dev'),
}
favorite_regexp = r'[^:]+:[^:]+;'
customs_regexp = r'[^;]+;'
customs_regexp = r'[^;]+;'

for key in preview_dirs.keys():
    prev_col = bpy.utils.previews.new()
    prev_col.my_previews_dir = preview_dirs[key]
    prev_col.my_previews = ()
    preview_collections[key.removesuffix('_dir')] = prev_col
prev_col = bpy.utils.previews.new()
prev_col.my_previews = []
preview_collections['fav'] = prev_col
all_col = bpy.utils.previews.new()
search_col = bpy.utils.previews.new()
custom_col = bpy.utils.previews.new()
custom_col.my_previews = []
utility_icons = bpy.utils.previews.new()
utility_icons.load('Discord_icon.png', join(data_dir, 'Discord_icon.png'), 'IMAGE')

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

def get_active_node_path(choice):
    return 'bpy.context.scene.compositor_pro_props.comp_{}'.format(choice)

def preview_all():
    data = get_node_data()

    enum_items = []

    if bpy.context is None:
        return enum_items

    directory = preview_dir

    for cat in data.keys():
        if cat == 'dev':
            continue
        for node in data[cat]:
            sub_location = ''
            is_default = False
            if node['override_thumb'] and node['thumb'] != 'default.png':
                cat, thumb = node['thumb'].split('/')
                sub_location = join(cat, thumb)
            elif node['override_thumb'] and node['thumb'] != 'default.png':
                is_default = True
            else:
                sub_location = join(cat, '{}.png'.format(node['name']))
            filepath = join(directory, sub_location)
            thumbname = node['name'] + '.png'
            if is_default:
                thumbname = 'default.png'
            icon = all_col.get(thumbname)
            thumb = None
            if not icon:
                thumb = all_col.load(thumbname, filepath, 'IMAGE')
            else:
                thumb = all_col[thumbname]
            enum_items.append((node['name'], node['name'], node['description'], thumb.icon_id, len(enum_items)))
    enum_items.sort(key=lambda e: e[0])
    all_col.my_previews = enum_items
    return all_col.my_previews

def previews_from_directory_items(prev_col):
    data = get_node_data()
    enum_items = []

    if bpy.context is None:
        return enum_items

    directory = prev_col.my_previews_dir

    cat = os.path.basename(directory)

    for node in data[cat]:
        sub_location = ''
        is_default = False
        if node['override_thumb'] and node['thumb'] != 'default.png':
            cat, thumb = node['thumb'].split('/')
            sub_location = join(cat, thumb)
        elif node['override_thumb'] and node['thumb'] != 'default.png':
            is_default = True
        else:
            sub_location = join(cat, '{}.png'.format(node['name']))
        filepath = join(directory, sub_location)
        thumbname = node['name'] + '.png'
        if is_default:
            thumbname = 'default.png'
        icon = all_col.get(thumbname)
        thumb = None
        if not icon:
            thumb = all_col.load(thumbname, filepath, 'IMAGE')
        else:
            thumb = all_col[thumbname]
        enum_items.append((node['name'], node['name'], node['description'], thumb.icon_id, len(enum_items)))
    prev_col.my_previews = enum_items
    prev_col.my_previews_dir = directory
    return prev_col.my_previews

def previews_from_favorites(self, context):
    prev_col = preview_collections['fav']
    enum_items = []

    if bpy.context is None or not has_favorites(context):
        return enum_items

    return prev_col.my_previews

def name_and_color_node(node_group, context):
    cat, data = get_all_from_node(node_group.node_tree.name)
    if data:
        node_group.name = 'CompPro_{}'.format(node_group.node_tree.name)
    else:
        node_group.name = 'Custom_{}'.format(node_group.node_tree.name)
        cat = 'custom'
    if get_preferences(context).color_nodes:
        node_group.use_custom_color = True
        node_group.color = eval('get_preferences(context).node_colors.{}'.format(cat))

def recursive_node_fixer (node_group, context):
    name_and_color_node(node_group, context)
    if node_group.node_tree.name == 'Global Drivers':
        driver_scene_name = 'Driver Scene'
        for fcurve in node_group.node_tree.animation_data.drivers:
            for var in fcurve.driver.variables:
                driver_scene_name = var.targets[0].id.name
                var.targets[0].id = context.scene
        if 'Driver' in driver_scene_name and bpy.data.scenes[driver_scene_name] is not None:
            bpy.data.scenes.remove(bpy.data.scenes[driver_scene_name])
        return
    if node_group.node_tree.name == 'Global Colorspace Conversion':
        for subnode in node_group.node_tree.nodes:
            if subnode.name == 'Convert Colorspace.001':
                subnode.from_color_space = 'Linear Rec.709'
            elif subnode.name == 'Convert Colorspace.002':
                subnode.to_color_space = 'Linear Rec.709'
        return
    for node in node_group.node_tree.nodes:
        if node.bl_idname == 'CompositorNodeGroup':
            if node.node_tree.name.endswith('.001'):
                node.node_tree = bpy.data.node_groups.get(node.node_tree.name[0:-4])
                name_and_color_node(node, context)
                continue
            recursive_node_fixer(node, context)
            continue
    node.show_options = False
    return

def get_preferences(context):
    return context.preferences.addons[__package__].preferences

def is_custom_node(node):
    if not node:
        return False
    return node.bl_idname == 'CompositorNodeGroup' and not node.name.startswith('CompPro_')

def has_color_management ():
    color_management_dir = ''
    ocio_path = os.environ.get('OCIO')
    if not ocio_path or not os.path.isfile(ocio_path):
        bl_dir = dirname(bpy.app.binary_path)
        ocio_dir = join(bl_dir, '{}.{}'.format(bpy.app.version[0], bpy.app.version[1]), 'datafiles', 'colormanagement')
        ocio_path = join(ocio_dir, 'config.ocio')
    if not os.path.isfile(ocio_path):
        if len(bpy.utils.script_paths()) == 2:
            color_management_dir = normpath(join(dirname(bpy.utils.script_paths()[0]), 'datafiles', 'colormanagement'))
        else:
            color_management_dir = normpath(join(dirname(bpy.utils.script_paths()[1]), 'datafiles', 'colormanagement'))
        ocio_path = join(color_management_dir, 'config.ocio')
    ocio_file = open(ocio_path, 'r')
    return ocio_file.read(18) == '# Color Management'

def color_management_list_to_tuples(enum_item):
    return (enum_item.identifier, enum_item.name, enum_item.description)

def color_management_list_to_strings(enum_item):
    return enum_item.name

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

def process_favorites_previews(favs):
    prev_col = preview_collections['fav']
    items = []
    for favorite in favs:
        cat, fnode = favorite.removesuffix(';').split(':')
        fnode_icon = fnode + '.png'
        filepath = join(preview_dir, join(cat, fnode_icon))
        icon = all_col.get(fnode_icon)
        if not icon:
            thumb = all_col.load(fnode_icon, filepath, 'IMAGE')
        else:
            thumb = all_col[fnode_icon]
        node_data = get_data_from_node(cat, fnode)
        item = (fnode, fnode, node_data['description'], thumb.icon_id, len(items))
        if item not in prev_col.my_previews:
            prev_col.my_previews.append(item)
        items.append(item)
    if len(items) != len(prev_col.my_previews):
        for preview in prev_col.my_previews:
            if preview not in items:
                prev_col.my_previews.remove(preview)
    prev_col.my_previews.sort(key=lambda e: e[0])

def update_search_cat(self, context):
    search = self.search_string
    if search == '':
        self.categories = 'all'
    else:
        self.categories = 'search'
        enum_items = []
        for item in all_col.my_previews:
            if search.upper() in item[0].upper():
                enum_items.append(item)
        search_col.my_previews = enum_items
    return

def previews_from_search(self, context):
    if search_col.my_previews is None:
        update_search_cat(self, context)
    return search_col.my_previews

def previews_from_custom(self, context):
    if custom_col.my_previews is None:
        process_custom_previews(context)
    return custom_col.my_previews

def process_custom_previews(context, clean = False):
    if clean:
        custom_col.my_previews = []
    thumb = custom_col.get('custom')
    if not thumb:
        thumb = custom_col.load('custom', join(preview_dir, 'default.png'), 'IMAGE')
    else:
        thumb = custom_col['custom']
    customs = re.findall(customs_regexp, get_preferences(context).customs)
    for i, custom_entry in enumerate(customs):
        custom = custom_entry.removesuffix(';')
        item = (custom, custom, '', thumb.icon_id, i)
        if item not in custom_col.my_previews:
            custom_col.my_previews.append(item)
    if len (customs) != len(custom_col.my_previews):
        for preview in custom_col.my_previews:
            if '{};'.format(preview[0]) not in customs:
                custom_col.my_previews.remove(preview)
    get_preferences(context).customs = ''.join(customs)
    return

def has_custom_nodes(context):
    if get_preferences(context).customs != '':
        if len(custom_col.my_previews) == 0:
            process_custom_previews(context)
        return True
    return False

def deep_process_custom_previews(context):
    customs = []
    if exists(custom_node_folder):
        for node in os.listdir(custom_node_folder):
            if node.endswith('.blend'): # processes out junk data and blend1 files.
                customs.append('{};'.format(node.removesuffix('.blend')))
    get_preferences(context).customs = ''.join(customs)
    process_custom_previews(context, True)

def make_cat_list(self, context):
    cat_list = [
        ('all', 'All', 'Every node in our addon'),
        None,
        ('mixed', 'Mixed Effects', 'Nodes that have the effects mixed in with the output of the node, similar to how you\'d expect a built-in node to behave'),
        ('unmixed', 'Unmixed Effects', 'Nodes that only output the effect without mixing in the source image. These effects can be mixed with any mixing method'),
        ('color', 'Color', 'Nodes related to color grading operations'),
        ('batches', 'Batches', 'Nodes that are preset groups of effects that are compiled together'),
        ('utilities', 'Utilities', 'Nodes that offer different utility functions, but not are not effects themselves'),
    ]
    has_fav = has_favorites(context)
    has_custom = has_custom_nodes(context)
    dev_tools = get_preferences(context).dev_tools
    if has_fav or has_custom or dev_tools:
        cat_list.append(None)
        if has_fav:
            cat_list.append(('fav', 'Favorites', 'Your favorite nodes', 'SOLO_ON', len(cat_list)))
        if has_custom:
            cat_list.append(('custom', 'Custom Nodes', 'Nodes you made yourself', 'GREASEPENCIL', len(cat_list)))
        if dev_tools:
            cat_list.append(('dev', 'Dev Tools', 'Nodes that are used to create many of the basic Comp Pro nodes', 'MODIFIER_ON', len(cat_list)))
    if self.search_string != '':
        cat_list.append(None)
        cat_list.append(('search', 'Search Results', 'The results of your search query', 'VIEWZOOM', len(cat_list)))
    return cat_list

def get_hotkey_entry_item(km, kmi_name, kmi_value):
    for i, km_item in enumerate(km.keymap_items):
        if km.keymap_items.keys()[i] == kmi_name:
            if km.keymap_items[i].properties.name == kmi_value:
                return km_item
    return None

def cleanup():
    for preview_col in preview_collections.values():
        bpy.utils.previews.remove(preview_col)
    bpy.utils.previews.remove(all_col)
    bpy.utils.previews.remove(custom_col)
    bpy.utils.previews.remove(search_col)
    bpy.utils.previews.remove(utility_icons)

def get_custom_path(node_name):
    return join(custom_node_folder, '{}.blend'.format(node_name))

def write_custom_node(nodegroup):
    bpy.data.libraries.write(get_custom_path(nodegroup.node_tree.name), {nodegroup.node_tree}, fake_user=True, path_remap='RELATIVE')
    return

def delete_custom_node(node_name):
    node_path = get_custom_path(node_name)
    try:
        os.remove(node_path)
        bpy.data.libraries.remove(bpy.data.libraries[os.path.basename(node_path)])
    except:
        print('Could not find custom node. Did something go wrong?')

def get_default_process_space():
    cm_tuple = tuple(map(color_management_list_to_strings, bpy.types.ColorManagedInputColorspaceSettings.bl_rna.properties['name'].enum_items))
    if 'AgX Log' in cm_tuple:
        return 'AgX Log'
    else:
        return cm_tuple[0][0]

def get_comppro_version():
    manifest = open(manifest_file, 'r')
    return manifest.readlines()[2][11:-2]

def has_global_textures():
    ngs = bpy.data.node_groups
    return ngs.get('Global Textures') is not None or ngs.get('Grain') is not None