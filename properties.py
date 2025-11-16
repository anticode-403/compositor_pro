import bpy
import os
from bpy.types import PropertyGroup
from bpy.props import StringProperty, FloatProperty, EnumProperty
from os.path import join, dirname, normpath
from . preferences import get_preferences, has_custom_nodes, has_favorites
from . previews import *

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

def get_default_process_space():
    cm_tuple = tuple(map(color_management_list_to_strings, bpy.types.ColorManagedInputColorspaceSettings.bl_rna.properties['name'].enum_items))
    if 'AgX Log' in cm_tuple:
        return 'AgX Log'
    else:
        return cm_tuple[0][0]

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
    add_process_colorspace_sequencer: EnumProperty(
        name='Active Colorspace Sequencer',
        items=tuple(map(color_management_list_to_tuples, bpy.types.ColorManagedInputColorspaceSettings.bl_rna.properties['name'].enum_items)),
        default=get_default_process_space()
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