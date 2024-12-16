import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, FloatProperty, EnumProperty
from . utility import *

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