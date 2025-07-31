from bpy.types import Menu, Panel
from . utility import *

class main_panel(Panel):
    bl_label = "Compositor Pro"
    bl_category = "Compositor Pro"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_idname = "AC_PT_Comp_Pro"

    @classmethod
    def poll(cls, context):
        if context.space_data.tree_type == 'CompositorNodeTree':
            return True
        else:
            return False
    
    def draw_header(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.operator('comp_pro.open_docs', text='', icon='QUESTION')
        row.operator('comp_pro.join_discord', text='', icon_value=utility_icons['Discord_icon.png'].icon_id)

    def draw(self, context):
        layout = self.layout
        props = context.scene.compositor_pro_props
        prefs = get_preferences(context)

        panel = layout.row()
        if not context.space_data.tree_type == 'CompositorNodeTree':
            return
        if not context.scene.use_nodes:
            panel.operator('comp_pro.enable_nodes', text="Enable Nodes")
        else:
            compositor = context.scene.node_tree
            panel = panel.column()
            
            add_panel = panel.box()
            add_panel.label(text="Add Compositor Pro Node")
            add_panel.prop(props, 'search_string')
            add_panel = add_panel.column(align=True)
            add_panel.prop(props, 'categories', text='')
            add_panel.template_icon_view(props, 'comp_{}'.format(props.categories), show_labels=True, scale_popup=prefs.thumbnail_size)
            add_button = add_panel.row(align=True)
            add_button.operator('comp_pro.add_node', text="Add {}".format(get_active_node_name(props.categories))).choice = props.categories
            if props.categories == 'custom':
                add_button.operator('comp_pro.delete_custom', text='', icon='TRASH')
            else:
                add_button.operator('comp_pro.open_info', text='', icon='QUESTION').choice = props.categories
                add_button.operator(
                    'comp_pro.toggle_favorite',
                    text='',
                    icon='SOLO_OFF' if not check_favorite(context, get_active_node_name(props.categories)) else 'SOLO_ON',
                    depress=check_favorite(context, get_active_node_name(props.categories))
                ).choice = props.categories

            if compositor.nodes.active is not None and compositor.nodes.active.bl_idname == 'CompositorNodeGroup' and 'Grain' in compositor.nodes.active.node_tree.name:
                panel.separator()
                context_menu = panel.box()
                context_menu.label(text="Edit Node")
                context_menu.operator('comp_pro.replace_grain', text="Replace Grain Texture")

            panel.separator()
            mixer_panel = panel.box()
            mixer_panel.label(text="Add Mix Node")
            mixer_panel = mixer_panel.column(align=True)
            mixer_options = mixer_panel.row(align=True)
            mixer_options.prop(props, 'mixer_blend_type', text='')
            mixer_options.prop(props, 'mixer_fac', text='')
            mixer_panel.operator('comp_pro.add_mixer', text="Add")

            panel.separator()
            colorgrade_panel = panel.box()
            colorgrade_panel.label(text="Color Grading")
            add_process_colorspace = colorgrade_panel.row(align=True)
            add_process_colorspace.prop(props, 'add_process_colorspace_sequencer', text='')
            add_process_colorspace.operator('comp_pro.add_process_colorspace', text="Add Process Space")

            panel.separator()
            custom_nodes = panel.box()
            custom_nodes.label(text="Custom Node Management")
            custom_nodes = custom_nodes.column(align=True)
            add_custom = custom_nodes.row()
            add_custom.operator('comp_pro.add_custom')
            add_custom.enabled = is_custom_node(compositor.nodes.active)
            custom_nodes.operator('comp_pro.rebuild_customs')

            panel.separator()
            file_management = panel.box()
            file_management.label(text="File Management")
            file_packing = file_management.column(align=True)
            file_packing.operator('comp_pro.pack_files')
            file_packing.operator('comp_pro.localize_files')
            file_packing.enabled = has_global_textures()

            panel.separator()
            credit_box = panel.box()
            version_row = credit_box.row()
            version_row.alignment = 'CENTER'
            version_row.label(text="Compositor Pro {}".format(get_comppro_version()))
            credits_row = credit_box.row()
            credits_row.alignment = 'CENTER'
            credits_row.scale_y = 0.25
            credits_row.enabled = False
            credits_row.label(text="Riley Rivera")
            nihal_row = credit_box.row()
            nihal_row.alignment = 'CENTER'
            nihal_row.scale_y = 0.25
            nihal_row.enabled = False
            nihal_row.label(text="Nihal Rahman")

class COMPPRO_MT_radial_menu(Menu):
    bl_label = 'Compositor Pro {}'.format(get_comppro_version())

    @classmethod
    def poll(cls, context):
        if context.space_data.tree_type == 'CompositorNodeTree':
            return True
        else:
            return False

    def draw(self, context):
        props = context.scene.compositor_pro_props
        prefs = get_preferences(context)

        pie = self.layout.menu_pie()
        box = pie.column(align=True)
        if has_favorites(context) or has_custom_nodes(context):
            category = 'fav_rad'
            if has_favorites(context) and has_custom_nodes(context):
                box.label(text="Instant Node")
                categories = box.row(align=True)
                categories.prop(props, 'n_categories', expand=True)
                category = props.n_categories
            elif has_favorites(context):
                box.label(text="Favorite Nodes")
                category = 'fav_rad'
            else:
                box.label(text="Custom Nodes")
                category = 'custom_rad'
            box.template_icon_view(props, 'comp_{}'.format(category), show_labels=True, scale_popup=prefs.thumbnail_size)
        box = pie.column(align=True)
        mixer_options = box.row(align=True)
        mixer_options.prop(props, 'mixer_fac', text='Fac')
        mixer_options.prop(props, 'mixer_blend_type', text='')
        box.operator('comp_pro.add_mixer', text="Add Mix Node")
        box.separator()
        add_process_colorspace = box.row(align=True)
        add_process_colorspace.operator('comp_pro.add_process_colorspace', text="Add Process Space")
        add_process_colorspace.prop(props, 'add_process_colorspace_sequencer', text='')
        box = pie.column(align=True)
        box.label(text="Riley Rivera and Nihal Rahman")

class COMPPRO_MT_Mixed_Menu(Menu):
    bl_idname = 'COMPPRO_MT_Mixed_Menu'
    bl_label = 'Mixed'

    def draw(self, context):
        layout = self.layout
        nodes = get_node_data()['mixed']
        for node in nodes:
            add_node_type(layout, node['name'], node['description'])

class COMPPRO_MT_Unmixed_Menu(Menu):
    bl_idname = 'COMPPRO_MT_Unmixed_Menu'
    bl_label = 'Unmixed'

    def draw(self, context):
        layout = self.layout
        nodes = get_node_data()['unmixed']
        for node in nodes:
            add_node_type(layout, node['name'], node['description'])

class COMPPRO_MT_Color_Menu(Menu):
    bl_idname = 'COMPPRO_MT_Color_Menu'
    bl_label = 'Color'

    def draw(self, context):
        layout = self.layout
        nodes = get_node_data()['color']
        for node in nodes:
            add_node_type(layout, node['name'], node['description'])

class COMPPRO_MT_Batches_Menu(Menu):
    bl_idname = 'COMPPRO_MT_Batches_Menu'
    bl_label = 'Batches'

    def draw(self, context):
        layout = self.layout
        nodes = get_node_data()['batches']
        for node in nodes:
            add_node_type(layout, node['name'], node['description'])

class COMPPRO_MT_Utilities_Menu(Menu):
    bl_idname = 'COMPPRO_MT_Utilities_Menu'
    bl_label = 'Utilities'

    def draw(self, context):
        layout = self.layout
        nodes = get_node_data()['utilities']
        for node in nodes:
            add_node_type(layout, node['name'], node['description'])

def add_node_type(layout, node_name, description, *, poll=None, search_weight=0.0):
    if poll is True or poll is None:
        props = layout.operator("comp_pro.add_node_direct", text=node_name, search_weight=search_weight)
        props.node = node_name
        props.desc = description
        return props

def add_node_hook(self, context):
    layout = self.layout
    layout.separator()
    layout.label(text="Compositor Pro")
    layout.menu('COMPPRO_MT_Mixed_Menu')
    layout.menu('COMPPRO_MT_Unmixed_Menu')
    layout.menu('COMPPRO_MT_Color_Menu')
    layout.menu('COMPPRO_MT_Batches_Menu')
    layout.menu('COMPPRO_MT_Utilities_Menu')