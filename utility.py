import bpy
import bpy.utils.previews # I don't understand why this fixes an issue, when it shouldn't do anything, but whatever
import os
from os.path import join, dirname, realpath

preview_collections = {}
main_dir = dirname(realpath(__file__))
data_dir = join(main_dir,'data')
blender_file = join(data_dir,'Compositor_Pro.blend')
favorite_file = join(data_dir, 'favorites.txt')
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

for key in preview_dirs.keys():
    prev_col = bpy.utils.previews.new()
    prev_col.my_previews_dir = preview_dirs[key]
    prev_col.my_previews = ()
    preview_collections[key[0:-4]] = prev_col
preview_collections['fav'] = bpy.utils.previews.new()

def get_active_node_path(choice):
    return 'bpy.context.scene.compositor_pro_props.comp_{}'.format(choice)

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
            icon = prev_col.get(name)
            if not icon:
                thumb = prev_col.load(name, filepath, 'IMAGE')
            else:
                thumb = prev_col[name]
            enum_items.append((name.split('.png')[0], name.split('.png')[0], '', thumb.icon_id, i))
    prev_col.my_previews = enum_items
    prev_col.my_previews_dir = directory
    return prev_col.my_previews

def previews_from_favorites(prev_col):
    enum_items = []

    if bpy.context is None:
        return enum_items

    if os.path.exists(favorite_file):
        favorites = open(favorite_file, 'r')
        image_paths = []
        image_names = []
        for fpath in favorites.readlines():
            image_paths.append(join(preview_dir, '{}.png'.format(fpath)))
            cat, name = fpath.split('/')
            image_names.append(name)
        for i, filepath in enumerate(image_paths):
            icon = prev_col.get(name)
            if not icon:
                thumb = prev_col.load(name, filepath, 'IMAGE')
            else:
                thumb = prev_col[name]
            enum_items.append((name, name, '', thumb.icon_id, i))
    prev_col.my_previews = enum_items
    return prev_col.my_previews

def recursive_node_fixer (node_group, context):
    print('Chatty recursive node fixer called on {}!'.format(node_group.node_tree.name))
    for node in node_group.node_tree.nodes:
        print('Found {}!'.format(node.bl_idname))
        if node.bl_idname == 'CompositorNodeGroup':
            print('Found a compositor node!')
            if node.node_tree.name.endswith('.001'):
                print('Replacing duplicate compositor pro node group!')
                node.node_tree = bpy.data.node_groups.get(node.node_tree.name[0:-4])
                continue
            if node.node_tree.name == '[ Utility ] Global Drivers':
                print('Fixing global drivers!')
                for fcurve in node.node_tree.animation_data.drivers:
                    for var in fcurve.driver.variables:
                        var.targets[0].id = context.scene
                continue
            print('Going deeper!')
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

def add_favorite(category, node):
    favorites = open(favorite_file, 'a')
    favorites.write('\m' + join(category, node))
    return

def rem_favorite(node):
    favorites_read = open(favorite_file, 'r')
    favorites_write = open(favorite_file, 'w')
    for fpath in favorites_read.readlines():
        if node in fpath:
            continue
        favorites_write.write(fpath)
    return

def check_favorite(node):
    if not os.path.exists(favorite_file):
        return False
    favorites = open(favorite_file, 'r')
    for fpath in favorites.readlines():
        cat, fnode = fpath.split('/')
        if fnode == node:
            return True
    return False