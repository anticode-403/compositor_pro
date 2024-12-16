import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
import webbrowser
from . utility import *

class compositor_pro_add_node(Operator):
    bl_idname = 'comp_pro.add_node'
    bl_description = 'Add Compositor Node'
    bl_category = 'Node'
    bl_label = 'Add Node'

    choice: StringProperty()

    def invoke(self, context, event):
        #find node
        group_name = eval(get_active_node_path(self.choice))
        if group_name == '':
            return {'CANCELLED'}
        node_tree = context.scene.node_tree
        nodes = node_tree.nodes
        desired_mode = 'OBJECT' if bpy.app.version != (4, 1, 0) else 'SELECT'
        if bpy.context.active_object != None and bpy.context.active_object.mode != desired_mode:
            bpy.ops.object.mode_set(mode=desired_mode)
        #append
        if not bpy.data.node_groups.get(group_name):
            if self.choice != 'custom' and not (self.choice == 'fav' and get_fav_dir(context, group_name) == 'custom'):
                bpy.ops.wm.append(filename=group_name, directory=file_path_node_tree)
            else:
                bpy.ops.wm.append(filename=group_name, directory=join(get_custom_path(group_name), 'NodeTree'))
        #add to scene
        new_group = nodes.new(type='CompositorNodeGroup')
        new_group.node_tree = bpy.data.node_groups.get(group_name)
        if bpy.data.node_groups.get(group_name) is not None:
            new_group.node_tree.use_fake_user = False
        else:
            self.report({'ERROR'}, 'This node does not exist in data file.')
        #fix nodes
        recursive_node_fixer(new_group, context)
        #attatch to cursor
        new_group.width = get_preferences(context).node_width
        new_group.location = context.space_data.cursor_location
        for n in nodes:
            n.select = n == new_group
        bpy.ops.node.translate_attach('INVOKE_DEFAULT')
        return {'FINISHED'}

class compositor_pro_replace_grain(Operator, ImportHelper):
    bl_idname = 'comp_pro.replace_grain'
    bl_description = 'Replace the grain texture in the Grain+ NG'
    bl_category = 'Node'
    bl_label = 'Replace Grain Texture'

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        grain_node = context.scene.node_tree.nodes.active
        grain_texture_node = None
        for node in grain_node.node_tree.nodes:
            if node.name == 'Grain':
                grain_texture_node = node
        new_texture = bpy.data.images.load(filepath = self.filepath)
        grain_texture_node.image = new_texture
        return {'FINISHED'}

class compositor_pro_add_mixer(Operator):
    bl_idname = 'comp_pro.add_mixer'
    bl_description = 'Add Mix node, with connections if possible.'
    bl_category = 'Node'
    bl_label = 'Add Mixer'

    def invoke(self, context, event):
        props = context.scene.compositor_pro_props
        node_tree = context.scene.node_tree
        nodes = node_tree.nodes
        mixer = nodes.new(type='CompositorNodeMixRGB')
        selected_nodes = []
        for n in nodes:
            if not n.select or n == mixer:
                continue
            if len(n.outputs) == 0:
                continue
            selected_nodes.append(n)
        if len(selected_nodes) == 1:
            node_tree.links.new(eval(selected_nodes[0].outputs[0].path_from_id()), eval(mixer.inputs[1].path_from_id()))
        elif len(selected_nodes) == 2:
            primary_node = selected_nodes[0]
            secondary_node = selected_nodes[1]
            if get_preferences(context).invert_mix_options:
                primary_node = selected_nodes[1]
                secondary_node = selected_nodes[0]
            if nodes.active in selected_nodes:
                selected_nodes.remove(nodes.active)
                if get_preferences(context).invert_mix_options:
                    primary_node = nodes.active
                    secondary_node = selected_nodes[0]
                else:
                    primary_node = selected_nodes[0]
                    secondary_node = nodes.active
            node_tree.links.new(eval(primary_node.outputs[0].path_from_id()), eval(mixer.inputs[1].path_from_id()))
            node_tree.links.new(eval(secondary_node.outputs[0].path_from_id()), eval(mixer.inputs[2].path_from_id()))
        mixer.inputs[0].default_value = props.mixer_fac
        mixer.blend_type = props.mixer_blend_type
        mixer.location = context.space_data.cursor_location
        for n in nodes:
            n.select = n == mixer
        bpy.ops.node.translate_attach('INVOKE_DEFAULT')
        return {'FINISHED'}

class compositor_pro_add_process_colorspace(Operator):
    bl_idname='comp_pro.add_process_colorspace'
    bl_description='Create an active colorspace node block'
    bl_category='Node'
    bl_label='Create Active Colorspace'

    def invoke(self, context, event):
        props = context.scene.compositor_pro_props
        node_tree = context.scene.node_tree
        nodes = node_tree.nodes
        to_active = nodes.new(type='CompositorNodeConvertColorSpace') # from Linear Rec.709 to add_process_colorspace_sequencer
        from_active = nodes.new(type='CompositorNodeConvertColorSpace') # from add_process_colorspace_sequencer to Linear Rec.709
        to_active.from_color_space = 'Linear Rec.709'
        to_active.to_color_space = props.add_process_colorspace_sequencer
        from_active.from_color_space = props.add_process_colorspace_sequencer
        from_active.to_color_space = 'Linear Rec.709'
        if nodes.active and nodes.active.select and len(nodes.active.inputs) != 0 and len(nodes.active.outputs) != 0:
            input_socket = nodes.active.inputs[0]
            for socket in nodes.active.inputs:
                if socket.type == 'RGBA':
                    input_socket = socket
                    break
            for link in nodes.active.internal_links:
                if link.to_socket == nodes.active.outputs[0]:
                    input_socket = link.from_socket
            for link in node_tree.links.values():
                if link.to_node == nodes.active and link.to_socket.type == 'RGBA':
                    node_tree.links.new(eval(link.from_socket.path_from_id()), eval(to_active.inputs[0].path_from_id()))
                elif link.from_node == nodes.active and link.from_socket == nodes.active.outputs[0]:
                    node_tree.links.new(eval(from_active.outputs[0].path_from_id()), eval(link.to_socket.path_from_id()))
            node_tree.links.new(eval(from_active.inputs[0].path_from_id()), eval(nodes.active.outputs[0].path_from_id()))
            node_tree.links.new(eval(input_socket.path_from_id()), eval(to_active.outputs[0].path_from_id()))
            to_active.location = (nodes.active.location.x - to_active.width - 100, nodes.active.location.y)
            from_active.location = (nodes.active.location.x + nodes.active.width + 100, nodes.active.location.y)
        else:
            node_tree.links.new(eval(to_active.outputs[0].path_from_id()), eval(from_active.inputs[0].path_from_id()))
            to_active.location = (context.space_data.cursor_location.x - 150, context.space_data.cursor_location.y)
            from_active.location = (context.space_data.cursor_location.x + 150, context.space_data.cursor_location.y)
            for n in nodes:
                n.select = n == to_active or n == from_active
            bpy.ops.node.translate_attach('INVOKE_DEFAULT')
        return {'FINISHED'}

class compositor_pro_enable_nodes(Operator):
    bl_idname = 'comp_pro.enable_nodes'
    bl_description = 'Enable compositor nodes'
    bl_category = 'Node'
    bl_label = 'Enable Nodes'

    def invoke(self, context, event):
        context.scene.use_nodes = True
        return {'FINISHED'}

class compositor_pro_toggle_favorite(Operator):
    bl_idname = 'comp_pro.toggle_favorite'
    bl_description = 'Add a node to your favorites list'
    bl_category = 'Node'
    bl_label = 'Add Favorite'

    choice: StringProperty()

    def invoke(self, context, event):
        node = eval(get_active_node_path(self.choice))
        is_fav = check_favorite(context, node)
        if is_fav:
            rem_favorite(context, node)
            if not has_favorites(context):
                context.scene.compositor_pro_props.categories = 'mixed'
        else:
            add_favorite(context, node)
        return {'FINISHED'}

class compositor_pro_open_info(Operator):
    bl_idname = 'comp_pro.open_info'
    bl_description = 'Open the documentation for the given node'
    bl_category = 'Node'
    bl_label = 'Open Info'

    choice: StringProperty()

    def invoke(self, context, event):
        node = eval(get_active_node_path(self.choice))
        node_link = node.lower().replace(' ', '_')
        cat = self.choice
        if self.choice == 'fav':
            cat = get_category_from_node(node)
        webbrowser.open('https://comppro.anticode.me/nodes/{}/{}.html'.format(cat, node_link))
        return {'FINISHED'}

class compositor_pro_open_docs(Operator):
    bl_idname = 'comp_pro.open_docs'
    bl_description = 'Open Compositor Pro documentation'
    bl_category = 'Node'
    bl_label = 'Open Documentation'

    def invoke(self, context, event):
        webbrowser.open('https://comppro.anticode.me')
        return {'FINISHED'}

class compositor_pro_join_discord(Operator):
    bl_idname = 'comp_pro.join_discord'
    bl_description = 'Join the Artum Discord for Compositor Pro'
    bl_category = 'Node'
    bl_label = 'Join Discord'

    def invoke(self, context, event):
        webbrowser.open('https://discord.gg/g5tUfzjqaj')
        return {'FINISHED'}

class compositor_pro_add_custom(Operator):
    bl_idname = 'comp_pro.add_custom'
    bl_description = 'Turn a nodegroup into a custom Compositor Pro node'
    bl_category = 'Node'
    bl_label = 'Add Custom Node'

    def invoke(self, context, event):
        nodegroup = context.scene.node_tree.nodes.active
        customs = re.findall(customs_regexp, get_preferences(context).customs)
        customs.append('{};'.format(nodegroup.node_tree.name))
        get_preferences(context).customs = ''.join(customs)
        write_custom_node(nodegroup)
        process_custom_previews(context)
        return {'FINISHED'}

class compositor_pro_rebuild_customs(Operator):
    bl_idname = 'comp_pro.rebuild_customs'
    bl_description = 'Deep refresh your custom nodes, in case some are missing or sticking behind when they shouldn\'t.'
    bl_category = 'Node'
    bl_label = 'Refresh Custom Nodes'

    def invoke(self, context, event):
        deep_process_custom_previews(context)
        return {'FINISHED'}

class compositor_pro_remove_custom(Operator):
    bl_idname = 'comp_pro.delete_custom'
    bl_description = 'Delete a custom Compositor Pro node'
    bl_category = 'Node'
    bl_label = 'Delete Custom Node'

    def invoke(self, context, event):
        customs = re.findall(customs_regexp, get_preferences(context).customs)
        node_name = context.scene.compositor_pro_props.comp_custom
        customs.remove('{};'.format(node_name))
        get_preferences(context).customs = ''.join(customs)
        delete_custom_node(node_name)
        process_custom_previews(context)
        if len(customs) == 0:
            context.scene.compositor_pro_props.categories = 'all'
        return {'FINISHED'}