import bpy
import os
from os.path import join, dirname, realpath

preview_collections = {}
preview_dir = join(dirname(realpath(__file__)),'thumbnails')
name_dir = join(preview_dir,'name')

prev_col = bpy.utils.previews.new()
prev_col.my_previews_dir = name_dir
prev_col.my_previews = ()
preview_collections['name'] = prev_col

def previews_from_directory_items(prev_col):
    enum_items = []

    if bpy.context is None:
        return enum_items

    directory = prev_col.my_previews_dir

    if directory and os.path.exists(directory):
        image_paths = []
        for fn in os.listdir(directory):
            if fn.lower().endswith(".jpg"):
                image_paths.append(fn)
        
        for i, name in enumerate(image_paths):
            filepath = os.path.join(directory, name)
            icon = prev_col.get(name)
            if not icon:
                thumb = prev_col.load(name, filepath, 'IMAGE')
            else:
                thumb = prev_col[name]
            enum_items.append((name.split('.jpg')[0], name.split('.jpg')[0], "", thumb.icon_id, i))
    prev_col.my_previews = enum_items
    prev_col.my_previews_dir = directory
    return prev_col.my_previews