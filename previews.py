import bpy
import bpy.utils.previews # I don't understand why this fixes an issue, when it shouldn't do anything, but whatever
import os
import re
from os.path import join, dirname, realpath, exists
from . preferences import get_preferences, get_node_data, get_data_from_node, has_favorites, customs_regexp

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

def deep_process_custom_previews(context):
    customs = []
    if exists(custom_node_folder):
        for node in os.listdir(custom_node_folder):
            if node.endswith('.blend'): # processes out junk data and blend1 files.
                customs.append('{};'.format(node.removesuffix('.blend')))
    get_preferences(context).customs = ''.join(customs)
    process_custom_previews(context, True)