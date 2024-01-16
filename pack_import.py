import os
import sys
import shutil
import zipfile
import json
import yaml
import tempfile
from PIL import Image

class PackImporter:
    def __init__(self, new_pack_name, pack_import_path, template_source_mapping, template_pack_config, template_build_config):
        self.new_pack_name = new_pack_name
        self.pack_import_path = pack_import_path
        self.template_source_mapping = template_source_mapping
        self.template_pack_config = template_pack_config
        self.template_build_config = template_build_config
        
        self.source_dir = new_pack_name.lower().replace(" ","_").replace(".","")
        self.mappings_dir = 'Version_Mappings'
        self.pack_format_to_version_file = 'Version_Mappings/version_mappings.json'

    def _load_pack_format_to_version(self, file_path):
        with open(file_path, 'r') as file:
            return json.load(file)

    #Read the pack.mcmeta file to determine the pack version
    def _read_pack_version(self, pack_import_path, version_to_pack_format):
        #Inverts the version_to_pack_format mapping for easier access.
        def invert_pack_format_mappings(version_to_pack_format):
            inverted = {}
            for platform, versions in version_to_pack_format.items():
                inverted[platform] = {info['pack_format']: version for version, info in versions.items()}
            return inverted
    
        mcmeta_path = os.path.join(pack_import_path, 'pack.mcmeta')
        json_path = os.path.join(pack_import_path, 'version.json')
        manifest_path = os.path.join(pack_import_path, 'manifest.json')

        inverted_format = invert_pack_format_mappings(version_to_pack_format)

        if os.path.isfile(mcmeta_path):
            with open(mcmeta_path, 'r') as file:
                meta_info = json.load(file)
                pack_format = meta_info.get('pack', {}).get('pack_format')
                minecraft_version = inverted_format['Java'].get(pack_format, '')
                print(f"Found pack_format/minecraft_version: {pack_format}/{minecraft_version}")
                return "Java", minecraft_version
        elif os.path.isfile(json_path):
            with open(json_path, 'r') as file:
                meta_info = json.load(file)
                pack_format = meta_info.get('pack_version', {}).get('resource')
                minecraft_version = inverted_format['Java'].get(pack_format, '')
                print(f"Found pack_format/minecraft_version: {pack_format}/{minecraft_version}")
                return "Java", minecraft_version
        elif os.path.isfile(manifest_path):
            with open(manifest_path, 'r') as file:
                meta_info = json.load(file)
                pack_format = meta_info.get('format_version')
                minecraft_version = inverted_format['Bedrock'].get(pack_format, '')
                print(f"Found pack_format/minecraft_version: {pack_format}/{minecraft_version}")
                return "Bedrock", minecraft_version
        else:
            print(f"pack_format not found")
            return

    #Load all mapping files for a specific version
    def _load_mappings(self, platform, version, mappings_dir):
        mappings = []
        version_dir = os.path.join(mappings_dir, platform, version)
        print(f"Loading mappings from: {version_dir}")
        if not os.path.exists(version_dir):
            print(f"No mappings found for version {version}")
            return mappings
        print(f"Files in the directory: {os.listdir(version_dir)}")
        for category_file in os.listdir(version_dir):
            if category_file.endswith('.json'):
                with open(os.path.join(version_dir, category_file), 'r') as file:
                    category_mappings = json.load(file)
                    mappings.extend(category_mappings)
                    print(f"Loaded {len(category_mappings)} mappings from {category_file}")
            else:
                print(f"Ignoring non-JSON file: {category_file}")
        return mappings

    #Load the UID to file path mappings
    def _load_uid_mappings(self, uid_mapping_file, current_version):
        """Load the UID to file path mappings with version handling, including inheritance from previous versions."""
        with open(uid_mapping_file, 'r') as file:
            all_uid_mappings = json.load(file)
            uid_mappings = {}

            def parse_version(version_str):
                return tuple(map(int, version_str.split('.')))

            current_version_tuple = parse_version(current_version)

            for uid, data in all_uid_mappings.items():
                version_specific_data = data.get("versions", {})
                merged_data = data.copy()  # Start with default data

                if version_specific_data:
                    # Sort versions in ascending order
                    sorted_versions = sorted(version_specific_data.keys(), key=parse_version)

                    # Iterate through sorted versions and apply overrides
                    for version in sorted_versions:
                        if current_version_tuple <= parse_version(version):
                            merged_data.update(version_specific_data[version])  # Apply version-specific overrides

                uid_mappings[uid] = merged_data

        return uid_mappings

    def deconstruct_atlas(self, source_dir, atlas_path, mapping, uid_mappings, atlas_type, grid_size=None, canvas_size=None, scale_factor=None):
        with Image.open(atlas_path) as atlas:
            if atlas_type == 'grid':
                for index, uid in enumerate(mapping['source']):
                    row = index // grid_size[0]
                    column = index % grid_size[0]
                    width, height = atlas.width // grid_size[0], atlas.height // grid_size[1]
                    x, y = column * width, row * height
                    region = (x, y, x + width, y + height)

                    extracted_image = atlas.crop(region)
                    uid_info = uid_mappings.get(uid, {})
                    output_path = os.path.join(source_dir, uid_info.get('path', ''))

                    # Ensure the destination directory exists before saving the file
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    extracted_image.save(output_path)

            elif atlas_type == 'stamp':
                for item in reversed(mapping['source']):
                    uid = item['uid']
                    uid_info = uid_mappings.get(uid, {})
                    output_path = os.path.join(source_dir, uid_info.get('path', ''))

                    # Create or load an image canvas
                    if os.path.exists(output_path):
                        img_canvas = Image.open(output_path)
                    else:
                        resolution = uid_info.get('resolution', (atlas.width, atlas.height))
                        img_canvas = Image.new('RGBA', resolution, (0, 0, 0, 0))

                    # Perform operations: Copy, Rotate, and Flip
                    copy_area = tuple(item.get('position', (0, 0)))
                    paste_area = tuple(item.get('copy', (0, 0, atlas.width, atlas.height)))
                    copy_width = paste_area[2] - paste_area[0]
                    copy_height = paste_area[3] - paste_area[1]
                    if scale_factor:
                        copy_area = (
                            int(copy_area[0] * scale_factor[0]),
                            int(copy_area[1] * scale_factor[1]),
                            int((copy_area[0] + copy_width) * scale_factor[0]),
                            int((copy_area[1] + copy_height) * scale_factor[1])
                        )
                    cropped_img = atlas.crop(copy_area)

                    rotate_angle = item.get('rotate', 0)
                    
                    if abs(rotate_angle) == 90:
                        x, y = cropped_img.size
                        if x > y:
                            cropped_img = cropped_img.resize((x, x))
                        else:
                            cropped_img = cropped_img.resize((y, y))
                        rotated_img = cropped_img.rotate(rotate_angle)
                        rotated_img = rotated_img.resize((y,x))
                    else:
                        rotated_img = cropped_img.rotate(rotate_angle)

                    flip_direction = item.get('flip')
                    if flip_direction == "Horizontal":
                        rotated_img = ImageOps.mirror(rotated_img)
                    elif flip_direction == "Vertical":
                        rotated_img = ImageOps.flip(rotated_img)

                    # Calculate scaled position and paste into the canvas
                    paste_loc = tuple(item.get('copy', (0, 0, atlas.width, atlas.height)))
                    if scale_factor:
                        paste_loc = (int(paste_loc[0] * scale_factor[0]), int(paste_loc[1] * scale_factor[1]))
                    
                    if rotated_img.mode != 'RGBA':
                        rotated_img = rotated_img.convert('RGBA')
                    img_canvas.paste(rotated_img, paste_loc, rotated_img)

                    # Ensure the destination directory exists before saving the file
                    directory = os.path.dirname(output_path)
                    os.makedirs(directory, exist_ok=True)
                    img_canvas.save(output_path)
            else:
                print(f"Unknown atlas type '{atlas_type}'")
                return

        print("Atlas deconstruction completed.")

    def calculate_scale_factor_for_atlas(self, atlas_path, mapping, uid_mappings, atlas_type, grid_size=None, canvas_size=None):
        # Load the actual atlas image to get its size
        with Image.open(atlas_path) as atlas_img:
            actual_width, actual_height = atlas_img.size

        # Calculate expected atlas size
        if atlas_type == 'grid':
            # Assuming all images in the grid have the same resolution
            sample_uid = mapping['source'][0]  # Get the first UID as a sample
            resolution = uid_mappings[sample_uid].get('resolution', (16, 16))
            expected_width, expected_height = resolution[0] * grid_size[0], resolution[1] * grid_size[1]
        elif atlas_type in ['stamp', 'tga']:
            expected_width, expected_height = canvas_size

        # Calculate scale factor
        scale_factor_x = actual_width / expected_width
        scale_factor_y = actual_height / expected_height

        return [int(scale_factor_x), int(scale_factor_y)]
    
    #Copy files from resource pack to source directory based on UID mappings
    def _import_resource_pack(self, pack_import_path, source_dir, mappings, uid_mappings):
        print(f"Starting import from {pack_import_path} to {source_dir}")
        missing_textures = []  # List to store missing textures

        for mapping in mappings:
            if 'type' in mapping:  # Check if UID is part of an atlas
                print(f"Converting {mapping['destination']} texture atlas to textures type: {mapping['type']}")
                atlas_type = mapping['type']
                grid_size = mapping.get("grid_size")
                canvas_size = mapping.get("canvas_size")
                atlas_path = os.path.join(pack_import_path, mapping['destination'])
                scale_factor = self.calculate_scale_factor_for_atlas(atlas_path, mapping, uid_mappings, atlas_type, grid_size, canvas_size)
                self.deconstruct_atlas(source_dir, atlas_path, mapping, uid_mappings, atlas_type, grid_size, canvas_size, scale_factor)
            else:
                uid = mapping['source']
                uid_info = uid_mappings.get(uid, None)
                if not uid_info:
                    print(f"Warning: No UID found - {uid}")
                    continue
                else:
                    actual_dest_path = uid_info.get("path", "")
                    if not actual_dest_path:
                        print(f"Warning: No path found for UID - {uid}")
                        continue
                    else:
                        dest_path = os.path.join(source_dir, actual_dest_path)
                        source_path = os.path.join(pack_import_path, mapping['destination'])

                        if os.path.exists(source_path):
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            shutil.copy2(source_path, dest_path)
                            print(f"Copied {source_path} to {dest_path}")
                        else:
                            missing_textures.append(source_path)  # Add missing texture to the list

        # Print all missing textures at once
        if missing_textures:
            print("\nMissing Textures:")
            for texture in missing_textures:
                print(texture)

        print("Import process completed.")
        
    #Extract a zip file to a temporary directory
    def _extract_zip_to_temp(self, zip_path):
        temp_dir = tempfile.mkdtemp()
        print(f"Extracting {zip_path} to temporary directory {temp_dir}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        return temp_dir

    def _create_new_config_files(self, new_pack_name, template_source_mapping, template_pack_config, template_build_config, new_source_dir, pack_import_path):
        # Create new source directory
        os.makedirs(new_source_dir, exist_ok=True)

        # Copy template source_mapping.json and update it if needed
        with open(template_source_mapping, 'r') as file:
            source_mapping_data = json.load(file)
        # Update source_mapping_data if needed
        source_mapping_file = os.path.join(new_source_dir, 'source_mapping.json')
        with open(source_mapping_file, 'w') as file:
            json.dump(source_mapping_data, file, indent=4)

        # Create pack.config based on template
        with open(template_pack_config, 'r') as file:
            pack_config_data = yaml.safe_load(file)
        pack_config_data['name'] = new_pack_name
        pack_config_data['description'] = ""
        pack_config_data['pack_version_number'] = [0, 0, 0]
        pack_config_data['resolutions'] = {"0": "16x"}
        pack_config_data['pack_uuid'] = ""
        pack_config_data['module_uuid'] = ""

        # Update pack_config_data with specific details
        pack_config_file = os.path.join(new_source_dir, 'pack.config')
        with open(pack_config_file, 'w') as file:
            json.dump(pack_config_data, file, indent=4)

        # Create build.config based on template
        with open(template_build_config, 'r') as file:
            build_config_data = yaml.safe_load(file)

        # Update build_config_data with specific details
        build_config_data['source_dir'] = new_source_dir
        build_config_data['source_mapping_file'] = source_mapping_file
        build_config_data['pack_config_file'] = pack_config_file

        build_config_file = f'{new_source_dir}.config'

        with open(build_config_file, 'w') as file:
            json.dump(build_config_data, file, indent=4)

        print(f"Created new config files and source directory for {new_pack_name}")

    def import_pack(self):
        pack_import_path = self.pack_import_path
        if zipfile.is_zipfile(pack_import_path):
            pack_import_path = self._extract_zip_to_temp(pack_import_path)
        
        pack_format_to_version = self._load_pack_format_to_version(self.pack_format_to_version_file)

        platform, pack_version = self._read_pack_version(pack_import_path, pack_format_to_version)
        source_mappings = self._load_uid_mappings(self.template_source_mapping, pack_version)
        
        if pack_version:
            mappings = self._load_mappings(platform, pack_version, self.mappings_dir)
            if mappings:
                self._create_new_config_files(self.new_pack_name, self.template_source_mapping, self.template_pack_config, self.template_build_config, self.source_dir, pack_import_path)
                self._import_resource_pack(pack_import_path, self.source_dir, mappings, source_mappings)
        else:
            print("Pack version could not be determined from pack.mcmeta")
