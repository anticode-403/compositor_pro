import bpy
from bpy.types import AddonPreferences
from bpy.props import StringProperty, BoolProperty, FloatProperty
import re
import rna_keymap_ui
from . utility import favorite_regexp, get_hotkey_entry_item

class compositor_pro_addon_preferences(AddonPreferences):
    def update_favorites(self, value):
        favs = re.findall(favorite_regexp, value)
        if len(favs) == 0:
            self['favorites'] = ''
            return
        if ''.join(favs) == value:
            self['favorites'] = value
            return

    def get_favorites(self):
        try:
            return self['favorites']
        except:
            self['favorites'] = self.favorites
            return self['favorites']

    bl_idname = __package__

    favorites: StringProperty(
        name="Favorites",
        description="A list of your favorite nodes",
        default='',
        set=update_favorites,
        get=get_favorites
    )
    quick_add: BoolProperty(
        name="Quick Add",
        description="Add nodes instantly when selected",
        default=False
    )
    dev_tools: BoolProperty(
        name="Dev Tools",
        description="A collection of nodes used for developing Compositor Pro",
        default=False
    )
    thumbnail_size: FloatProperty(
        name="Thumbnail Size",
        description="The size of node thumbnails when in the selection menu",
        default=6.0,
        min=1,
        max=100,
        subtype='UNSIGNED'
    )
    invert_mix_options: BoolProperty(
        name="Invert Mix Order",
        description="Invert the order that Add Mix Node processes selections.",
        default=False
    )

    def draw(self, context):
        layout = self.layout
        # layout.label(text='Compositor Pro Preferences')
        box = layout.box()
        box.label(text="Addon Panel")
        box.prop(self, 'quick_add')
        box.prop(self, 'invert_mix_options')
        box.prop(self, 'thumbnail_size')
        box = layout.box()
        box.label(text="Other Options")
        box.prop(self, 'dev_tools')
