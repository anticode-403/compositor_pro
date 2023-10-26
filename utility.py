import bpy
import bpy.utils.previews # I don't understand why this fixes an issue, when it shouldn't do anything, but whatever
import os
from os.path import join, dirname, realpath
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

def get_active_node_path(choice):
    return 'bpy.context.scene.compositor_pro_props.comp_{}'.format(choice)

def preview_all():
    enum_items = []

    if bpy.context is None:
        return enum_items

    directory = preview_dir

    if directory and os.path.exists(directory):
        image_paths = []
        for cat_folder in os.listdir(directory):
            if cat_folder.endswith('.png') or cat_folder == 'dev_tools':
                continue
            cfpath = join(directory, cat_folder)
            for fn in os.listdir(cfpath):
                if fn.lower().endswith('.png'):
                    image_paths.append(join(cat_folder, fn))
        for i, name in enumerate(image_paths):
            filepath = os.path.join(directory, name)
            node_name = name.split('\\')[1]
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

    if directory and os.path.exists(directory):
        image_paths = []
        for fn in os.listdir(directory):
            if fn.lower().endswith(".png"):
                image_paths.append(fn)

        for i, name in enumerate(image_paths):
            filepath = os.path.join(directory, name)
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
    for node in node_group.node_tree.nodes:
        if node.bl_idname == 'CompositorNodeGroup':
            if node.node_tree.name.endswith('.001'):
                node.node_tree = bpy.data.node_groups.get(node.node_tree.name[0:-4])
                continue
            if node.node_tree.name == '[ Utility ] Global Drivers':
                for fcurve in node.node_tree.animation_data.drivers:
                    for var in fcurve.driver.variables:
                        var.targets[0].id = context.scene
                continue
            recursive_node_fixer(node, context)
            continue
    return

def has_color_management ():
    color_management_dir = ''
    if len(bpy.utils.script_paths()) == 2:
        color_management_dir = os.path.normpath(os.path.join(os.path.dirname(bpy.utils.script_paths()[0]), 'datafiles', 'colormanagement'))
    else:
        color_management_dir = os.path.normpath(os.path.join(os.path.dirname(bpy.utils.script_paths()[1]), 'datafiles', 'colormanagement'))
    ocio_file_path = join(color_management_dir, 'config.ocio')
    ocio_file = open(ocio_file_path, 'r')
    return ocio_file.read(18) == '# Color Management'

def color_management_list_to_tuples(enum_item):
    return (enum_item.identifier, enum_item.name, enum_item.description)

def add_favorite(context, category, node):
    favorite_string = context.preferences.addons[__package__].preferences.favorites
    favs = re.findall(favorite_regexp, favorite_string)
    favs.append('{}:{};'.format(category, node))
    new_string = ''.join(favs)
    context.preferences.addons[__package__].preferences.favorites = new_string
    process_favorites_previews(favs)
    return

def rem_favorite(context, node):
    favorite_string = context.preferences.addons[__package__].preferences.favorites
    favs = re.findall(favorite_regexp, favorite_string)
    for favorite in favs:
        cat, fnode = favorite.removesuffix(';').split(':')
        if fnode == node:
            favs.remove(favorite)
    new_string = ''.join(favs)
    context.preferences.addons[__package__].preferences.favorites = new_string
    if len(favs) != 0:
        process_favorites_previews(favs)
    return

def check_favorite(context, node):
    favorite_string = context.preferences.addons[__package__].preferences.favorites
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
    favorite_string = context.preferences.addons[__package__].preferences.favorites
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

def make_cat_list(self, context):
    cat_list = [
        ('all', 'All', 'Every node in our addon'),
        None,
        ('mixed', 'Mixed Effects', 'Compositing effects that does not require any additional mixing. These effects will mix in the effect by default from the output'),
        ('unmixed', 'Unmixed Effects', 'Compositing effects that only output the raw effect. These effects require an additional mix node to be mixed with your source'),
        ('color', 'Color Grading', 'Compositing effects related to color grading operations'),
        ('batches', 'Batches', 'Preset effect configurations'),
        ('utilities', 'Utilities', 'Nodes that offer different utility functions, but not are not effects themselves'),
    ]
    if has_favorites(context):
        cat_list.append(None)
        cat_list.append(('fav', 'Favorites', 'Your favorite nodes', 'SOLO_ON', len(cat_list)))
    if context.preferences.addons[__package__].preferences.dev_tools:
        if not has_favorites(context):
            cat_list.append(None)
        cat_list.append(('dev', 'Dev Tools', 'Nodes that are used to create many of the basic Comp Pro nodes', 'MODIFIER_ON', len(cat_list)))
    return cat_list