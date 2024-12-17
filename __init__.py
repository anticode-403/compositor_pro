if 'bpy' in locals(): # This means that an older version of the addon was previously installed
    import importlib
    if 'utility' in locals():
        importlib.reload(utility)
    if 'preferences' in locals():
        importlib.reload(preferences)
    if 'properties' in locals():
        importlib.reload(properties)
    if 'operators' in locals():
        importlib.reload(operators)
    if 'menus' in locals():
        importlib.reload(menus)

import bpy
from bpy.props import PointerProperty
from . preferences import NodeColors, compositor_pro_addon_preferences
from . properties import compositor_pro_props
from . menus import *
from . operators import *
from . utility import cleanup

classes = [ NodeColors, compositor_pro_add_mixer, compositor_pro_replace_grain,
            compositor_pro_enable_nodes, compositor_pro_add_node, main_panel, compositor_pro_props, compositor_pro_remove_custom,
            compositor_pro_add_process_colorspace, compositor_pro_open_info, compositor_pro_toggle_favorite, compositor_pro_add_custom,
            compositor_pro_join_discord, compositor_pro_open_docs, compositor_pro_rebuild_customs, COMPPRO_MT_radial_menu, 
            compositor_pro_pack_files, compositor_pro_localize_files, COMPPRO_MT_Mixed_Menu, COMPPRO_MT_Unmixed_Menu, COMPPRO_MT_Color_Menu,
            COMPPRO_MT_Batches_Menu, COMPPRO_MT_Utilities_Menu, compositor_pro_add_node_direct,
            compositor_pro_addon_preferences ]

kmd = [None, None]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.compositor_pro_props = PointerProperty(type=compositor_pro_props)
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Node Generic', space_type='NODE_EDITOR', region_type='WINDOW')
    kmi = km.keymap_items.new('wm.call_menu_pie','V','PRESS')
    kmi.properties.name = 'COMPPRO_MT_radial_menu'
    kmi.active = True
    kmd[0] = km
    kmd[1] = kmi

    bpy.types.NODE_MT_compositor_node_add_all.append(add_node_hook)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.compositor_pro_props
    wm = bpy.context.window_manager
    kmd[0].keymap_items.remove(kmd[1])
    wm.keyconfigs.addon.keymaps.remove(kmd[0])
    cleanup()

    bpy.types.NODE_MT_compositor_node_add_all.remove(add_node_hook)

if __name__ == "__main__":
    register()
