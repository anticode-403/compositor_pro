import bpy
import bpy.utils.previews # I don't understand why this fixes an issue, when it shouldn't do anything, but whatever
import os
from os.path import join, dirname, realpath, normpath, exists
import re

preview_collections = {}
main_dir = dirname(realpath(__file__))
data_dir = join(main_dir,'data')
blender_file = join(data_dir,'Compositor_Pro.blend')
file_path_node_tree = join(blender_file,'NodeTree')
preview_dir = join(main_dir,'thumbnails')
preview_dirs = {
    'mixed_dir': join(preview_dir,'mixed'),
    'unmixed_dir': join(preview_dir,'unmixed'),
    'color_dir': join(preview_dir,'color'),
    'batches_dir': join(preview_dir,'batches'),
    'utilities_dir': join(preview_dir,'utilities'),
    'dev_dir': join(preview_dir,'dev_tools'),
}
favorite_regexp = r'[^:]+:[^:]+;'

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

def get_active_node_path(choice):
    return 'bpy.context.scene.compositor_pro_props.comp_{}'.format(choice)

def preview_all():
    enum_items = []

    if bpy.context is None:
        return enum_items

    directory = preview_dir

    if directory and exists(directory):
        image_paths = []
        for cat_folder in os.listdir(directory):
            if cat_folder.endswith('.png') or cat_folder == 'dev_tools':
                continue
            cfpath = join(directory, cat_folder)
            for fn in os.listdir(cfpath):
                if fn.lower().endswith('.png'):
                    image_paths.append(join(cat_folder, fn))
        for i, name in enumerate(image_paths):
            filepath = join(directory, name)
            node_name = os.path.basename(name)
            icon = all_col.get(node_name)
            if not icon:
                thumb = all_col.load(node_name, filepath, 'IMAGE')
            else:
                thumb = all_col[node_name]
            enum_items.append((node_name.removesuffix('.png'), node_name.removesuffix('.png'), '', thumb.icon_id, i))
    enum_items.sort(key=lambda e: e[0])
    all_col.my_previews = enum_items
    return all_col.my_previews

def previews_from_directory_items(prev_col):
    enum_items = []

    if bpy.context is None:
        return enum_items

    directory = prev_col.my_previews_dir

    if directory and exists(directory):
        image_paths = []
        for fn in os.listdir(directory):
            if fn.lower().endswith(".png"):
                image_paths.append(fn)

        for i, name in enumerate(image_paths):
            filepath = join(directory, name)
            icon = all_col.get(name)
            if not icon:
                thumb = all_col.load(name, filepath, 'IMAGE')
            else:
                thumb = all_col[name]
            enum_items.append((name.removesuffix('.png'), name.removesuffix('.png'), '', thumb.icon_id, i))
    prev_col.my_previews = enum_items
    prev_col.my_previews_dir = directory
    return prev_col.my_previews

def previews_from_favorites(self, context):
    prev_col = preview_collections['fav']
    enum_items = []

    if bpy.context is None or not has_favorites(context):
        return enum_items

    return prev_col.my_previews

def recursive_node_fixer (node_group, context):
    node_group.name = 'CompPro_{}'.format(node_group.node_tree.name)
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
        if is_b3_cm():
            for subnode in node_group.node_tree.nodes:
                if subnode.name == 'Convert Colorspace.001':
                    subnode.to_color_space = 'Filmic Log'
                    subnode.from_color_space = 'Linear'
                elif subnode.name == 'Convert Colorspace.002':
                    subnode.to_color_space = 'Linear'
                    subnode.from_color_space = 'Filmic Log'
        else:
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
                continue
            recursive_node_fixer(node, context)
            continue
    return

def get_preferences(context):
    return context.preferences.addons[__package__].preferences

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

def add_favorite(context, category, node):
    favorite_string = get_preferences(context).favorites
    favs = re.findall(favorite_regexp, favorite_string)
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
    for i, favorite in enumerate(favs):
        cat, fnode = favorite.removesuffix(';').split(':')
        fnode_icon = fnode + '.png'
        filepath = join(preview_dir, join(cat, fnode_icon))
        icon = all_col.get(fnode_icon)
        if not icon:
            thumb = all_col.load(fnode_icon, filepath, 'IMAGE')
        else:
            thumb = all_col[fnode_icon]
        item = (fnode, fnode, '', thumb.icon_id, i)
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
    if has_favorites(context):
        cat_list.append(None)
        cat_list.append(('fav', 'Favorites', 'Your favorite nodes', 'SOLO_ON', len(cat_list)))
    if get_preferences(context).dev_tools:
        if not has_favorites(context):
            cat_list.append(None)
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

def is_b3_cm():
    return not (has_color_management() or bpy.app.version >= (4, 0, 0))

def is_broken_cm():
    cm_tuple = tuple(map(color_management_list_to_strings, bpy.types.ColorManagedInputColorspaceSettings.bl_rna.properties['name'].enum_items))
    if is_b3_cm():
        return not ('Filmic Log' in cm_tuple)
    else:
        return not ('AgX Log' in cm_tuple)

def get_default_process_space():
    if is_b3_cm():
        return 'Filmic Log'
    else:
        return 'AgX Log'