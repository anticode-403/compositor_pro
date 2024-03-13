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
file_path_node_tree = join(blender_file,'NodeTree')
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

def round_vector(vector, t):
    return tuple(round(v_frag, t) for v_frag in vector)

def convert_ng(nodegroup):
    store_props = ['name', 'bl_idname', 'inputs', 'outputs', 'location']
    optional_props = {'hide': False, 'label': '', 'mute': False, 'parent': None, 'select': False, 'show_options': True,
        'show_preview': False, 'show_texture': False,
        'use_custom_color': False}
    ignored_props = ['bl_description', 'bl_icon', 'bl_label', 'type', 'bl_height_default', 'bl_height_max',
        'bl_height_min', 'bl_rna', 'bl_static_type', 'bl_width_default',
        'bl_width_max', 'bl_width_min', 'draw_buttons', 'draw_buttons_ext',
        'input_template', 'texture_mapping', 'uv_map', 'color_mapping',
        'internal_links', 'is_registered_node_type', 'output_template', 'poll', 'poll_instance',
        'rna_type', 'socket_value_update', 'update', 'image_user', 'dimensions',
        'width_hidden', 'interface', 'object', 'text', 'color', 'height', 'image',
        'width', 'filepath']
    node_tree = nodegroup.node_tree
    nodes = node_tree.nodes

    json_data = {}

    for node in nodes:
        properties = {}
        _props = {}
        for attr in dir(node):
            if hasattr(node, attr):
                _props[attr] = getattr(node, attr)

        for prop in _props:
            if prop in ignored_props:
                continue
            elif prop[:1] == '_':
                continue
            elif prop in store_props:
                if prop == 'inputs':
                    _inputs = {}
                    for i, inp in enumerate(node.inputs):
                        try:
                            try:
                                _inputs[i] = round(inp.default_value, 5)
                            except:
                                _inputs[i] = round_vector(inp.default_value, 5)
                        except Exception as e:
                            print('Node {} Input {} does not have a default value.'.format(node.name, str(i)))
                    if _inputs != {}:
                        properties[prop] = _inputs
                elif prop == 'outputs':
                    _outputs = {}
                    _output_dfv = {}
                    for i, out in enumerate(node.outputs):
                        try:
                            _output_dfv[i] = round(out.default_value, 5)
                        except:
                            _output_dfv[i] = round_vector(out.default_value, 5)
                        try:
                            if out.is_linked:
                                _links = {}
                                for link in out.links:
                                    target = link.to_socket.path_from_id()
                                    target = int((target.split('inputs['))[1][:-1])
                                    _ln = link.to_node.name
                                    if _ln in _links:
                                        try:
                                            _links[_ln] = _links.get(_ln) + (target,)
                                        except:
                                            _links[_ln] = (_links.get(_ln),) + (target,)
                                    else:
                                        _links[_ln] = target
                                _outputs[i] = _links
                        except:
                            _outputs[out] = str(out.links)
                    if _outputs != {}:
                        properties[prop] = _outputs
                    if _output_dfv != {}:
                        properties['out_dfv'] = _output_dfv
                elif prop == 'location':
                    try:
                        properties['loc'] = (round(_props[prop][0]), round(_props[prop][1]),)
                    except:
                        print('Node {} location dump failed.'.format(node.name))
                elif prop in optional_props:
                    value = _props[prop]
                    if value != optional_props[prop]:
                        if prop == 'parent':
                            properties[prop] = value.name
                            continue
                        properties[prop] = value
                        if prop == 'use_custom_color':
                            properties['color'] = round_vector(_props['color'])
                elif prop == 'node_tree':
                    try:
                        properties[prop] = _props[prop].name
                        json_data[_props[prop].name] = convert_ng(node)
                    except Exception as e:
                        print('Group node tree failed.')
                        print(e)
                elif prop == 'color_ramp':
                    _cr = {}
                    _els = {}
                    _cr['color_mode'] = _props[prop].color_mode
                    _cr['hue_interpolation'] = _props[prop].hue_interpolation
                    _cr['interpolation'] = _props[prop].interpolation
                    for element in _props[prop].elements:
                        _els[round(element.position, 5)] = round_vector(element.color, 5)
                    _cr['elements'] = _els
                    properties[prop] = _cr
                elif prop == 'mapping':
                    _mapping = {}
                    _curves = {}

                    _mapping['clip_max_x'] = _props[prop].clip_max_x
                    _mapping['clip_max_y'] = _props[prop].clip_max_y
                    _mapping['clip_min_x'] = _props[prop].clip_min_x
                    _mapping['clip_min_y'] = _props[prop].clip_min_y
                    _mapping['extend'] = _props[prop].extend
                    _mapping['tone'] = _props[prop].tone
                    _mapping['use_clip'] = _props[prop].use_clip

                    for i, curve in enumerate(_props.curves):
                        _points = {}
                        for idx, point in enumerate(curve.points):
                            _points[idx] = (round(point.location[0], 5), round(point.location[1], 5),)
                        _curves[i] = _points
                    _mapping['curves'] = _curves
                    properties[prop] = _mapping
                else: # Catch all for any nodes we missed.
                    if isinstance(_props[prop], (int, str, bool, float, tuple)):
                        properties[prop] = _props[prop]
                    else:
                        try:
                            properties[prop] = _props[prop].name
                        except:
                            pass
    return json_data