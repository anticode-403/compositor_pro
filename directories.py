from os.path import dirname, realpath, join

# Directory management stuff.
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