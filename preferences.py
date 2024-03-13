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
    customs: StringProperty(
        name='Custom Nodes',
        description="A list of your custom nodes",
        default=''
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
        box.label(text="Keyboard Shortcuts")
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user
        km = kc.keymaps['Node Generic']
        kmi = get_hotkey_entry_item(km, 'wm.call_menu_pie', 'COMPPRO_MT_radial_menu')
        if kmi:
            box.context_pointer_set('keymap', km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, box, 0)
        box = layout.box()
        box.label(text="Other Options")
        box.prop(self, 'dev_tools')
        # box = layout.box()
        # box.label(text="Developer Insights")
        # box.prop(self, 'favorites')
        # box.prop(self, 'customs')
