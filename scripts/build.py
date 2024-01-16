import argparse
import os
import logging
import json
import yaml
import shutil
import zipfile
from datetime import datetime
from atlas import AtlasHandler
from PIL import Image, ImageFilter
import numpy as np
import cv2

def setup_logging(log_directory):
    backup_directory = os.path.join(log_directory, 'backup')

    # Create log directory if it doesn't exist
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_directory):
        os.makedirs(backup_directory)

    # Check for existing log file and move it to backup
    current_log_file = os.path.join(log_directory, 'current_log.txt')
    if os.path.exists(current_log_file):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_log_file = os.path.join(backup_directory, f"log_{timestamp}.txt")
        shutil.move(current_log_file, backup_log_file)

    # Configure new log file
    logging.basicConfig(filename=current_log_file, level=logging.INFO, format='%(asctime)s: %(message)s')

def load_yml_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config
    
def load_version_to_pack_format(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def format_pack_version_number(version_list):
    return '.'.join(str(number) for number in version_list)

def load_uid_mappings(uid_mapping_file, current_version):
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

def load_mappings(version, mappings_dir):
    """ Load all mapping files for a specific version """
    mappings = []
    version_dir = os.path.join(mappings_dir, version)
    logging.warning(f"Loading mappings from: {version_dir}")
    if not os.path.exists(version_dir):
        logging.warning(f"Warning: No mappings found for version {version}")
        return mappings
    logging.warning(f"Files in the directory: {os.listdir(version_dir)}")  # Debug print
    for category_file in os.listdir(version_dir):
        if category_file.endswith('.json'):
            with open(os.path.join(version_dir, category_file), 'r') as file:
                mappings.extend(json.load(file))
        else:
            logging.warning(f"Warning: Ignoring non-JSON file: {category_file}")
    return mappings

def replace_variables_in_file(file_path, variables):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        for key, value in variables.items():
            content = content.replace(f"%{key}%", str(value))
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def find_resolution_specific_texture(source_dir, version_relative_path, target_height):
    """Find if there is a resolution-specific texture available in the source directory."""
    base, ext = os.path.splitext(version_relative_path)
    logging.warning(f"target_height: {target_height}")
    resolution_suffix = f"_{target_height}px{ext}"
    logging.warning(f"resolution_suffix: {resolution_suffix}")
    resolution_specific_path = os.path.join(source_dir, f"{base.replace('/', os.sep)}{resolution_suffix}")

    logging.warning(f"Checking for {target_height}px height texture version of: {version_relative_path}")
    logging.warning(f"At location: {resolution_specific_path}")

    if os.path.exists(resolution_specific_path):
        logging.warning(f"Found resolution-specific texture: {resolution_specific_path}")
        return True, resolution_specific_path
    else:
        logging.warning(f"Resolution-specific texture not found, using original: {os.path.join(source_dir, version_relative_path)}")
        return False, os.path.join(source_dir, version_relative_path)

def bleed_alpha(img, bleed_distance, background_color='black'):
    """Bleed the colors of the RGB channels into the transparent regions."""
    if img.mode != 'RGBA':
        return img

    # Split the image into RGB and Alpha channels
    rgb, alpha = img.split()[:3], img.split()[3]
    rgb = Image.merge("RGB", rgb)

    # Create an opaque mask from the alpha channel
    opaque_mask = alpha.point(lambda p: 255 if p > 0 else 0)
    
    # Convert the mask to a NumPy array for OpenCV processing
    opaque_mask_np = np.array(opaque_mask)

    # Apply dilation using OpenCV
    kernel = np.ones((3,3), np.uint8)
    dilated_mask_np = cv2.dilate(opaque_mask_np, kernel, iterations=bleed_distance)

    # Convert the dilated mask back to PIL Image
    dilated_mask = Image.fromarray(dilated_mask_np)

    # Create a new RGB image with the specified background color
    bleed_rgb = Image.new("RGB", img.size, background_color)

    # Paste the original RGB using the dilated mask onto the background
    bleed_rgb.paste(rgb, mask=dilated_mask)

    # Optionally, apply smoothing filter
    #bleed_rgb = bleed_rgb.filter(ImageFilter.SMOOTH_MORE)

    # Merge the bleed RGB with the original alpha channel
    return Image.merge("RGBA", (*bleed_rgb.split(), alpha))

def scale_texture_with_separate_channels(img, scale_factor, bleed_distance=16):
    """Scale RGB and alpha channels separately with alpha bleeding."""
    if img.mode == 'RGBA':
        img_bleeded = bleed_alpha(img, bleed_distance)
        rgb, alpha = img_bleeded.split()[:3], img_bleeded.split()[3]
        rgb = Image.merge("RGB", rgb)
        rgb_resized = rgb.resize((int(rgb.width * scale_factor), int(rgb.height * scale_factor)), Image.LANCZOS)
        alpha_resized = alpha.resize((int(alpha.width * scale_factor), int(alpha.height * scale_factor)), Image.NEAREST)
        img_resized = Image.merge("RGBA", (*rgb_resized.split(), alpha_resized))
    else:
        img_resized = img.resize((int(img.width * scale_factor), int(img.height * scale_factor)), Image.LANCZOS)
    return img_resized

def process_file(source_dir, dest_dir, original_path, uid_info, scale_factor, variables):
    full_source_path = os.path.join(source_dir, original_path.replace('/', os.sep))
    full_dest_path = os.path.join(dest_dir, original_path.replace('/', os.sep))

    # Check if file exists
    if not os.path.exists(full_source_path):
        logging.warning(f"Warning: Source file not found - {full_source_path}")
        return

    # Ensure the destination directory exists
    os.makedirs(os.path.dirname(full_dest_path), exist_ok=True)

    # Ensure the destination directory exists
    os.makedirs(os.path.dirname(full_dest_path), exist_ok=True)

    # Skip resizing if 'downsample' is set to FALSE
    if uid_info.get('downsample') == "FALSE":
        logging.info(f"Skipping downsample for: {original_path}")
        shutil.copy(full_source_path, full_dest_path)
    elif full_source_path.lower().endswith('.png'):
        # For PNG files, proceed with resizing and processing
        img_height = Image.open(full_source_path).height
        target_height = int(img_height * scale_factor)
        override_exists, resolution_specific_texture = find_resolution_specific_texture(source_dir, original_path, target_height)
        
        with Image.open(resolution_specific_texture) as img:
            if not override_exists:
                img = scale_texture_with_separate_channels(img, scale_factor)
            img.save(full_dest_path)
    else:
        # Copy non-PNG files directly
        shutil.copy(full_source_path, full_dest_path)

    # Handle 'inject' flag
    if uid_info.get('inject') == "TRUE":
        replace_variables_in_file(full_dest_path, variables)

def resolution_adjustments(source_dir, dest_dir, mappings, uid_mappings, scale_factor, pack_variables):
    os.makedirs(dest_dir, exist_ok=True)
    total_files = len(mappings)
    warnings=[]

    for i, mapping in enumerate(mappings, 1):
        if mapping.get('type') == 'grid':
            # Process grid type atlas
            for uid in mapping['source']:
                uid_info = uid_mappings.get(uid, {})
                original_path = uid_info.get('path', '')
                if original_path:
                    logging.warning(f"Processing grid UID '{uid}': {original_path}")
                    downsample = uid_info.get('downsample', '')
                    logging.warning(f"Downsample '{uid}'?: {downsample}")
                    process_file(source_dir, dest_dir, original_path, uid_info, scale_factor, pack_variables)
        elif mapping.get('type') in ['stamp', 'tga']:
            # Process stamp type atlas
            for atlas_mapping in mapping['source']:
                uid = atlas_mapping['uid']
                uid_info = uid_mappings.get(uid, {})
                original_path = uid_info.get('path', '')
                if original_path:
                    logging.warning(f"Processing stamp UID '{uid}': {original_path}")
                    downsample = uid_info.get('downsample', '')
                    logging.warning(f"Downsample '{uid}'?: {downsample}")
                    process_file(source_dir, dest_dir, original_path, uid_info, scale_factor, pack_variables)
        else:
            # Process regular texture
            uid = mapping['source']
            uid_info = uid_mappings.get(uid, {})
            original_path = uid_info.get('path', '')
            if original_path:
                logging.warning(f"Processing regular texture '{uid}': {original_path}")
                downsample = uid_info.get('downsample', '')
                logging.warning(f"Downsample '{uid}'?: {downsample}")
                process_file(source_dir, dest_dir, original_path, uid_info, scale_factor, pack_variables)

        print(f"\r[{i}/{total_files}] source files found...", end="")

def apply_mappings(resolution_dir, dest_dir, mappings, uid_mappings):
    total_files = len(mappings)
    logging.warning(f"Processing version in {dest_dir}:")
    print(f"Processing version in {dest_dir}:")
    warnings = []

    for i, mapping in enumerate(mappings, 1):
        if mapping.get('type') in ['grid', 'stamp', 'tga']:
            atlas_handler = AtlasHandler()

            atlas_mappings = mapping['source']
            dest_path = os.path.join(dest_dir, mapping['destination'])
            atlas_type = mapping['type']

            if atlas_type == 'grid':
                grid_size = tuple(mapping['grid_size'])
                atlas_handler.compile_atlas(resolution_dir, atlas_mappings, dest_path, atlas_type, uid_mappings, grid_size)
            elif atlas_type in ['stamp', 'tga']:
                canvas_size = tuple(mapping['canvas_size'])
                atlas_handler.compile_atlas(resolution_dir, atlas_mappings, dest_path, atlas_type, uid_mappings, canvas_size=canvas_size)
            else:
                logging.warning(f"Warning: Unknown atlas type - {atlas_type}")

            print(f"\r[{i}/{total_files}] atlas compiled...", end="")
        else:
            uid = mapping['source']
            uid_info = uid_mappings.get(uid, {})
            original_path = uid_info.get('path', '')
            if original_path:
                source_path = os.path.join(resolution_dir, original_path.replace('/', os.sep))
                dest_path = os.path.join(dest_dir, mapping['destination'].replace('/', os.sep))

                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                if os.path.exists(source_path):
                    shutil.copy2(source_path, dest_path)
                    print(f"\r[{i}/{total_files}] files copied...", end="")
                else:
                    logging.warning(f"Warning: Source file not found - {source_path}")

def create_zip_from_folder(folder_path, zip_path):
    """ Create a zip file from a folder """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, folder_path))

def main(config_path):
    build_config = load_yml_config(config_path)

    source_dir = build_config['source_dir']
    mappings_dir = build_config['mappings_dir']
    output_dir = build_config['output_dir']
    tempfile_dir = build_config['tempfile_dir']
    log_output_dir = build_config['log_output_dir']
    source_mapping_file = build_config['source_mapping_file']
    version_mappings_file = build_config['version_mappings_file']
    pack_config_file = build_config['pack_config_file']

    #Load pack config for using as variables
    pack_variables = load_yml_config(pack_config_file)

    #Add a few variables to the list
    pack_name = pack_variables["name"]
    pack_version_number = f"{pack_variables['pack_version_number'][0]}.{pack_variables['pack_version_number'][1]}.{pack_variables['pack_version_number'][2]}"

    resolutions = pack_variables['resolutions']

    #Configure logging
    setup_logging(log_output_dir)
    logging.info("Starting the resource pack generator...")

    version_to_pack_format_data = load_version_to_pack_format(version_mappings_file)
    
    for platform, versions in version_to_pack_format_data.items():
        platform_mappings_dir = os.path.join(mappings_dir, platform)

        for version, version_info in versions.items():
            pack_variables["pack_format"] = version_info["pack_format"]
            zip_extension = version_info.get("zip_extension", ".zip")

            if os.path.exists(os.path.join(platform_mappings_dir, version)):
                platform_mappings_dir = os.path.join(mappings_dir, platform)
                pack_variables["version"] = format_pack_version_number(version)

                for scale_key, scale_name in resolutions.items():
                    pack_variables["resolution"] = scale_name
                    scale_key = int(scale_key)
                    scale_factor = 0.5 ** scale_key if scale_key > 0 else 1
                    version_dir = os.path.join(tempfile_dir, f"{platform}_{version}_{scale_name}")

                    uid_mappings = load_uid_mappings(source_mapping_file, version)

                    mappings = load_mappings(version, platform_mappings_dir)
                    resolution_dir = os.path.join(tempfile_dir, f"{source_dir}_{platform}_{version}_{scale_name}")

                    resolution_adjustments(source_dir, resolution_dir, mappings, uid_mappings, scale_factor, pack_variables)
                    apply_mappings(resolution_dir, version_dir, mappings, uid_mappings)

                    # Update pack.mcmeta and create zip file for each version
                    zip_file_name = f"[{platform}][{version}][{scale_name}]{pack_name}_{pack_version_number}{zip_extension}"
                    create_zip_from_folder(version_dir, os.path.join(output_dir, zip_file_name))
                    logging.warning(f"Created zip file: {os.path.join(output_dir, zip_file_name)}")
                    
                    # Remove the folder after creating the zip file
                    shutil.rmtree(resolution_dir)
                    shutil.rmtree(version_dir)
        
        else:
            logging.warning(f"Warning: {version} version for {platform} platform could not be found in {mappings_dir} Mapping Directory so it could not be created.")
            print(f"Warning: {version} version for {platform} platform could not be found in {mappings_dir} Mapping Directory so it could not be created.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Resource Pack Generator')
    parser.add_argument('config', help='Path to the build configuration file')
    args = parser.parse_args()
    
    main(args.config)
