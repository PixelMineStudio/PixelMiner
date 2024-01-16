import os
from PIL import Image, ImageOps, ImageChops
from statistics import median
import logging

class AtlasPacker:
    def compile_atlas(self, source_dir, atlas_mappings, output_path, atlas_type, uid_mappings, grid_size=None, canvas_size=None):
        if atlas_type == 'grid':
            # Calculate the total size of the grid based on the largest image in each dimension
            max_width = max_height = 0
            image_data = []  # Store images and their positions

            # Load images, calculate the total canvas size, and store them
            for uid in atlas_mappings:
                uid_info = uid_mappings.get(uid, {})
                img_path = os.path.join(source_dir, uid_info.get("path", ""))

                logging.info(f"Attempting to open {uid} image at path: {img_path}")

                if os.path.exists(img_path):
                    with Image.open(img_path) as img:
                        image_data.append((img.copy(), img.width, img.height))  # Copy the image and store its dimensions
                        max_width = max(max_width, img.width)
                        max_height = max(max_height, img.height)

            # Ensure the canvas size is based on the grid
            canvas_size = (grid_size[0] * max_width, grid_size[1] * max_height)
            atlas = Image.new('RGBA', canvas_size, (0, 0, 0, 0))

            # Place images in the grid
            x_offset = y_offset = 0
            for i, (img, width, height) in enumerate(image_data):
                atlas.paste(img, (x_offset, y_offset))
                x_offset += width
                if (i + 1) % grid_size[0] == 0:  # Move to next row after reaching the grid's end
                    x_offset = 0
                    y_offset += height

            # Ensure the destination directory exists before saving the file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            atlas.save(output_path)

        elif atlas_type in ['stamp', 'tga']:
            # Initialize variables to check uniformity of scale factors
            scale_factors_info = []

            # Load images and check their scale factors
            for mapping in atlas_mappings:
                uid = mapping['uid']
                uid_info = uid_mappings.get(uid, {})
                img_path = os.path.join(source_dir, uid_info.get("path", ""))
                specified_resolution = uid_info.get("resolution", None)

                logging.info(f"Attempting to open {uid} image at path: {img_path}")

                if os.path.exists(img_path) and specified_resolution:
                    with Image.open(img_path) as img:
                        actual_resolution = (img.width, img.height)
                        scale_factor = (actual_resolution[0] / specified_resolution[0], actual_resolution[1] / specified_resolution[1])
                        scale_factors_info.append((scale_factor, img_path, specified_resolution, actual_resolution))

            # Calculate the median scale factor for each axis
            median_scale_factor_x = median([sf[0] for sf, _, _, _ in scale_factors_info])
            median_scale_factor_y = median([sf[1] for sf, _, _, _ in scale_factors_info])

            # Create an empty atlas with the specified canvas size, scaled
            scaled_canvas_size = (int(canvas_size[0] * median_scale_factor_x), int(canvas_size[1] * median_scale_factor_y))
            
            if atlas_type == 'tga':
                atlas = Image.new('RGBA', scaled_canvas_size, (1, 1, 1, 1))
            else:
                atlas = Image.new('RGBA', scaled_canvas_size, (0, 0, 0, 0))

            # Initialize a variable to store the alpha channel
            alpha_channel = None
            
            # Process each mapping in the atlas
            for mapping in atlas_mappings:
                uid = mapping['uid']
                uid_info = uid_mappings.get(uid, {})
                img_path = os.path.join(source_dir, uid_info.get("path", ""))

                if os.path.exists(img_path):
                    with Image.open(img_path) as img:
                        # Perform operations: Copy, Rotate, and Flip
                        copy_area = tuple(mapping.get('copy', (0, 0, img.width, img.height)))
                        if mapping.get('copy'):
                            copy_area = (
                                int(copy_area[0]) * median_scale_factor_x,
                                int(copy_area[1]) * median_scale_factor_y, 
                                int(copy_area[2]) * median_scale_factor_x, 
                                int(copy_area[3]) * median_scale_factor_y
                                )
                        cropped_img = img.crop(copy_area)

                        rotate_angle = mapping.get('rotate', 0)
                        
                        if abs(rotate_angle) == 90:
                            x, y = cropped_img.size
                            if x > y:
                                cropped_img = cropped_img.resize((x, x))
                            else:
                                cropped_img = cropped_img.resize((y, y))
                            rotated_img = cropped_img.rotate(-rotate_angle)
                            rotated_img = rotated_img.resize((y,x))
                        else:
                            rotated_img = cropped_img.rotate(-rotate_angle)

                        flip_direction = mapping.get('flip')
                        if flip_direction == "Horizontal":
                            rotated_img = ImageOps.mirror(rotated_img)
                        if flip_direction == "Vertical":
                            rotated_img = ImageOps.flip(rotated_img)

                        # Calculate scaled position
                        position = tuple(mapping.get('position', (0, 0)))
                        scaled_pos = (int(position[0] * median_scale_factor_x), int(position[1] * median_scale_factor_y))

                        if mapping.get("use_for_alpha", False):
                            # Handle alpha channel separately
                            alpha_channel = rotated_img.split()[3]
                        elif "alpha_add" in mapping:
                            # Add to the alpha channel with specified opacity
                            alpha_addition = rotated_img.split()[3].point(lambda p: int(p * mapping["alpha_add"]))
                            alpha_channel = ImageChops.add(alpha_channel, alpha_addition)
                        else:
                            # Convert to 'RGBA' only if not used for alpha channel
                            if rotated_img.mode != 'RGBA':
                                rotated_img = rotated_img.convert('RGBA')
                            atlas.paste(rotated_img, scaled_pos, rotated_img)

                else:
                    logging.info(f"Error: Missing image file for UID '{uid}' in atlas '{output_path}'.")
                    raise ValueError(f"Missing image file for UID '{uid}'.")

            # Merge alpha channel if it's set
            if alpha_channel:
                atlas.putalpha(alpha_channel)

            # Ensure the destination directory exists before saving the file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Check if the output format should be TGA
            if output_path.lower().endswith(".tga"):
                # Save in TGA format
                atlas.save(output_path, format="TGA")
            else:
                # Save in default format
                atlas.save(output_path)
        
        # Add an else clause for cases where atlas_type doesn't match any known types
        else:
            raise ValueError(f"Unknown atlas type '{atlas_type}'")

        # Return the atlas if it has been created
        return atlas
