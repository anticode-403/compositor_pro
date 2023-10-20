import bpy
import os
from os.path import join, dirname, realpath

preview_collections = {}
main_dir = dirname(realpath(__file__))
preview_dir = join(main_dir,'thumbnails')
effects_dir = join(preview_dir,'effects')
utilities_dir = join(preview_dir,'utilities')
batches_dir = join(preview_dir,'batches')

blender_dir = join(main_dir,'data')
blender_file = join(blender_dir,'Compositor_Pro.blend')
file_path_node_tree = join(blender_file,'NodeTree')

prev_col = bpy.utils.previews.new()
prev_col.my_previews_dir = effects_dir
prev_col.my_previews = ()
preview_collections['effects'] = prev_col

prev_col = bpy.utils.previews.new()
prev_col.my_previews_dir = utilities_dir
prev_col.my_previews = ()
preview_collections['utilities'] = prev_col

prev_col = bpy.utils.previews.new()
prev_col.my_previews_dir = batches_dir
prev_col.my_previews = ()
preview_collections['batches'] = prev_col

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
            enum_items.append((name.split('.png')[0], name.split('.png')[0], "", thumb.icon_id, i))
    prev_col.my_previews = enum_items
    prev_col.my_previews_dir = directory
    return prev_col.my_previews

def has_color_management (context):
    color_management_plus = [
        'Camera Log',
        'Log',
        'RED IPP2',
        'ACES Display',
        'TCAMv2 Display',
        'AgX ( Filmic 2.0 ) Display',
        'Filmic Display'
    ]
    display_device = context.scene.display_settings.display_device
    if display_device in color_management_plus:
        return True
    else:
        return False