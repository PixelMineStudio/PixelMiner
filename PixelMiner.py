import os
import sys
from pathlib import Path
import flet as ft
import json
import yaml
import zipfile
import tempfile
import shutil
from PIL import Image
from pack_import import PackImporter
import argparse
import subprocess
import glob
import threading
import tkinter as tk
from tkinter import filedialog
import easygui

selected_pack_icon_btn = None  # Global variable to keep track of selected pack icon
selected_folder_btn = None  # Global variable to keep track of selected folder button
is_building = False
build_btn = None  # Global variable for build button
build_dialog = None  # Global variable for build confirmation dialog

def main(page: ft.Page):
    global build_btn, build_dialog

    color_btn_pack_select = ft.colors.WHITE

    app_title = "PixelMiner Resource Packing Tool"
    page.title = app_title
    page.vertical_alignment = "start"
    page.horizontal_alignment = "start"
    page.window_height=1080
    page.window_width=1920
    page.padding=0
    page.spacing=0
    page.update()

    original_pack_configs = {}
    packs = {}

    def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    desired_path = 'Version_Mappings'
    internal_path = resource_path('Version_Mappings')

    if not os.path.exists(desired_path):
        shutil.copytree(internal_path, desired_path)
    
    desired_path = 'scripts'
    internal_path = resource_path('scripts')

    if not os.path.exists(desired_path):
        shutil.copytree(internal_path, desired_path)

    def open_file(path):
        os.startfile(path)  # For Windows. For MacOS, you might use `subprocess.call(["open", path])`

    def open_folder(path):
        folder = os.path.dirname(path)
        os.startfile(folder)  # For Windows. For MacOS, you might use `subprocess.call(["open", folder])`

    def import_pack(e):
        def show_new_pack_name_dialog(pack_path):
            pack_name_field = ft.TextField(label="Pack Name", value=Path(pack_path).stem)  # Define the text field here
            def on_cancel(e):
                pack_name_dialog.open = False
                page.update()
            def on_submit(e):
                pack_name = pack_name_field.value

                # Hide the name dialog and show the progress bar
                pack_name_dialog.open = False
                progress_bar.visible = True
                page.update()

                # Run the pack_import.py script
                template_source_mapping = 'assets/template_source_mapping.json'
                if not os.path.exists(template_source_mapping):
                    template_source_mapping = resource_path(template_source_mapping)
                template_pack_config = 'assets/template_pack.config'
                if not os.path.exists(template_pack_config):
                    template_pack_config = resource_path(template_pack_config)
                template_build_config = 'assets/template_build.config'
                if not os.path.exists(template_build_config):
                    template_build_config = resource_path(template_build_config)

                pack_importer = PackImporter(pack_name, pack_path, template_source_mapping, template_pack_config, template_build_config)
                pack_importer.import_pack()

                # After completion, hide the progress bar and refresh the packs list
                progress_bar.visible = False
                refresh_packs_list()

                first_pack = next(iter(packs.values()))
                update_details_view(first_pack)
                update_folder_buttons(first_pack)
                source_mapping = load_source_mapping(first_pack['source_mapping_file'], first_pack['source_dir'])
                top_level_folders = list_top_level_folders(first_pack['source_dir'])
                first_folder = top_level_folders[0]
                update_middle_panel(source_mapping, filter_folder=os.path.join(first_pack['source_dir'], first_folder))

                page.update()

            pack_name_dialog = ft.AlertDialog(
                title=ft.Text("Enter New Pack Name"),
                content=pack_name_field,  # Use the text field variable here
                actions=[
                    ft.TextButton("Submit", on_click=on_submit),
                    ft.TextButton("Cancel", on_click=on_cancel),
                ],
                modal=True
            )
            page.dialog = pack_name_dialog
            pack_name_dialog.open = True

            page.update()

        def handle_import(e: ft.FilePickerResultEvent):
            if e.files:
                file_path = e.files[0].path  # Assuming single file selection
                show_new_pack_name_dialog(file_path)
            else:
                print("Cancelled!")

        pick_files_dialog = ft.FilePicker(on_result=handle_import)
        page.overlay.append(pick_files_dialog)
        page.add(pick_files_dialog)
        pick_files_dialog.pick_files(file_type = ft.FilePickerFileType.CUSTOM, allowed_extensions = ["zip", "mcpack"], allow_multiple=False)

        # Create a progress bar
        progress_bar = ft.ProgressBar(visible=False)
        page.add(progress_bar)

    # Function to update the details view
    def update_details_view(pack, editable=False):
        details_view.controls.clear()
        if os.path.isfile(pack['icon']):
            details_view.controls.append(ft.Image(src=pack['icon'], width=256, height=256, fit=ft.ImageFit.CONTAIN))

        # Load fields from pack.config
        if pack['config']:
            for key, value in pack['config'].items():
                if key == "version":
                    # Handling version as a special case with NumberPicker or any other suitable control
                    pass  # Your logic for version
                elif key == "resolutions":
                    resolution_list = ft.ListView()
                    for res in value:
                        resolution_list.controls.append(ft.Text(value[res]))
                    details_view.controls.append(resolution_list)
                else:
                    text_field = ft.TextField(value=str(value), label=key.capitalize(), read_only=not editable, on_change=lambda e, p=pack, k=key: on_text_field_change(e, k, p))
                    details_view.controls.append(text_field)

        # Save the original config for revert functionality
        original_pack_configs[pack['pack_config_file']] = pack['config'].copy()

        # Add Edit, Save, Revert buttons to the details view
        edit_btn = ft.ElevatedButton("Edit", on_click=lambda e: on_edit_click(pack))
        save_btn = ft.ElevatedButton("Save", on_click=lambda e: on_save_click(pack), bgcolor=ft.colors.GREEN_500)
        revert_btn = ft.ElevatedButton("Revert", on_click=lambda e: on_revert_click(pack))

        # Add buttons to details view based on the editable flag
        if editable:
            details_view.controls.append(save_btn)
            details_view.controls.append(revert_btn)
        else:
            details_view.controls.append(edit_btn)

        page.update()

    # Event handler when the 'Edit' button is clicked
    def on_edit_click(pack):
        # Disable pack selection
        for pack_icon_btn in left_panel_contents.controls:
            pack_icon_btn.disabled = True

        # Enter edit mode
        update_details_view(pack, editable=True)

    # Event handler when the 'Save' button is clicked
    def on_save_click(pack):
        # Save the modified pack config
        save_config(pack['config'], pack['pack_config_file'])

        # Enable pack selection
        for pack_icon_btn in left_panel_contents.controls:
            pack_icon_btn.disabled = False

        # Exit edit mode and update the details view
        update_details_view(pack, editable=False)

    # Event handler when the 'Revert' button is clicked
    def on_revert_click(pack):
        # Revert changes using the original pack config
        pack['config'] = original_pack_configs[pack['pack_config_file']].copy()

        # Enable pack selection
        for pack_icon_btn in left_panel_contents.controls:
            pack_icon_btn.disabled = False

        # Exit edit mode and update the details view
        update_details_view(pack, editable=False)

    # Function to save the pack config
    def save_config(config_data, config_file_path):
        # Convert the pack config data to YAML format and save it to file
        with open(config_file_path, 'w') as file:
            yaml.dump(config_data, file, default_flow_style=False, sort_keys=False)

    # Event handler for text field change
    def on_text_field_change(e, key, pack):
        # Update the pack variable when the text field changes
        pack['config'][key] = e.control.value
       
    def load_source_mapping(source_mapping_file, source_dir):
        with open(source_mapping_file, 'r') as file:
            source_mapping = json.load(file)
        items = []
        for key, item in source_mapping.items():
            item['path'] = os.path.join(source_dir, item.get('path', ''))
            items.append((key, item))
        # Sort the list of tuples by the 'path' key in the item
        sorted_items = sorted(items, key=lambda x: x[1]['path'])
        return dict(sorted_items)

    
    # Function to toggle the visibility of overlay container's controls
    def toggle_visibility(container, visible):
        container.visible = visible
        container.update()

    def make_toggle_handler(container):
        return lambda e: toggle_visibility(container, True), lambda e: toggle_visibility(container, False)

    def upscale_image(image_path):
        with Image.open(image_path) as img:
            #Check image size
            image_size = max(img.width, img.height)

            if image_size < 256:
                # Calculate new dimensions
                scale_factor = round(256/image_size, 0)
                new_width = int(img.width * scale_factor)
                new_height = int(img.height * scale_factor)

                # Resize using NEAREST filter
                resized_img = img.resize((new_width, new_height), Image.NEAREST)

                # Save or return the image as needed
                resized_img_path = os.path.join("_temp_images", image_path)

                resized_img_dir = os.path.dirname(resized_img_path)
                if not os.path.exists(resized_img_dir): 
                    os.makedirs(resized_img_dir) 

                resized_img.save(resized_img_path)  # Example save path, modify as needed

                return resized_img_path

            else:
                return image_path

    def update_middle_panel(source_mapping, filter_folder=None):
        middle_panel_contents.controls.clear()
        grid = ft.GridView(
            runs_count=10,
            max_extent=256,
            child_aspect_ratio=1.0,
            auto_scroll=False,
        )

        for uid, item in source_mapping.items():

            if filter_folder is None or item['path'].startswith(filter_folder):
                image_path = item['path']
                file_exists = os.path.isfile(image_path)
                
                file_ext = os.path.splitext(image_path)[1]
                file_ext = file_ext.replace('.', '')

                if not file_exists or not file_ext in ["png", "tga"]:
                    missing_image_path = f"assets/missing_{file_ext}.png"
                    if not os.path.exists(missing_image_path):
                        missing_image_path = resource_path(missing_image_path)
                    if os.path.isfile(missing_image_path):
                        image_path = missing_image_path

                resized_image_path = upscale_image(image_path)

                # Image
                image = ft.Image(
                    src=resized_image_path,
                    fit=ft.ImageFit.CONTAIN,
                    width=256,
                    height=256,
                )

                # Action buttons (initially invisible)
                open_btn = ft.IconButton(icon=ft.icons.FOLDER_OPEN,
                                        on_click=lambda e, p=item['path']: open_file(p))
                folder_btn = ft.IconButton(icon=ft.icons.FOLDER, 
                                        on_click=lambda e, p=item['path']: open_folder(p))
    
                if not file_exists:
                    open_btn = ft.IconButton(icon=ft.icons.FOLDER_OPEN)
                    open_btn.disabled=True
                
                # Text and buttons container
                overlay_container = ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                f"{uid}",
                                color=ft.colors.WHITE,
                                size=10,
                                height=15,
                                weight=ft.FontWeight.BOLD,
                                overflow=ft.TextOverflow.CLIP
                            ),
                            ft.Text(
                                f"{item['path']}",
                                color=ft.colors.WHITE,
                                size=10,
                                height=15,
                                overflow=ft.TextOverflow.CLIP
                            ),
                            ft.Row([open_btn, folder_btn], alignment="center")
                        ],
                        spacing=0,
                        alignment=ft.MainAxisAlignment.END,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                    ),
                    margin=ft.margin.only(top=128),
                    visible=False,
                    alignment=ft.alignment.bottom_center,
                    bgcolor=ft.colors.with_opacity(0.75, ft.colors.BLACK)
                )

                # Create GestureDetector handlers
                on_enter_handler, on_exit_handler = make_toggle_handler(overlay_container)

                # GestureDetector to handle hover events
                gesture_detector = ft.GestureDetector(
                    on_enter=on_enter_handler,
                    on_exit=on_exit_handler,
                    content=ft.Stack([image, overlay_container])
                )

                # Item container
                item_container = ft.Container(
                    content=gesture_detector,
                    alignment=ft.alignment.bottom_center,
                    margin=0,
                    bgcolor=ft.colors.BLACK,
                )

                grid.controls.append(item_container)

        middle_panel_contents.controls.append(grid)
        page.update()

    def build_packs(e):
        global is_building, build_process

        def on_build_cancel(e):
            global is_building, build_process
            is_building = False

            if build_process:
                build_process.terminate()
                build_process = None

            # Reset UI elements
            build_btn.icon = ft.icons.CONSTRUCTION
            build_btn.bgcolor = '#0c74db'
            build_btn.on_click = build_packs
            progress_bar.visible = False
            page.update()

        def on_build_confirm(e):
            global build_dialog, is_building, build_process
            build_dialog.open = False

            is_building = True

            # Update UI elements
            build_btn.icon = ft.icons.CANCEL
            build_btn.bgcolor = ft.colors.RED
            build_btn.on_click = on_build_cancel
            progress_bar.visible = True
            page.update()

            start_build_process()

        def close_build_confirm(e):
            build_dialog.open = False
            page.update()

        def show_build_confirmation_dialog():
            global build_dialog
            build_dialog = ft.AlertDialog(
                title=ft.Text("Confirm Build"),
                actions=[
                    ft.TextButton("Confirm", on_click=on_build_confirm),
                    ft.TextButton("Cancel", on_click=close_build_confirm),
                ],
                modal=True
            )
            page.dialog = build_dialog
            build_dialog.open = True
            page.update()

        def start_build_process():
            global build_process

            def build_thread():
                global is_building, build_process
                for index, pack in enumerate(packs.values()):
                    if not is_building:
                        break

                    config_file = pack['config_file']
                    
                    #to run as a module the path needs to be /build as a script, but including the script in the exe and runnign it as a module it needs the full extension
                    build_script_path = 'scripts/build.py'
                    build_process = subprocess.Popen(['python', build_script_path, config_file])


                    # Wait for the process to complete
                    build_process.wait()
                    build_process = None

                    # Check if the build was cancelled
                    if not is_building:
                        break

            build_thread = threading.Thread(target=build_thread)
            build_thread.start()


        # Progress bar
        progress_bar = ft.ProgressBar(visible=False)
        page.add(progress_bar)
        
        if not is_building:
            # Show the build confirmation dialog
            show_build_confirmation_dialog()
        else:
            # Cancel the build process
            on_build_cancel(None)


    # Add folder buttons to the folder panel
    def on_folder_button_click(e, folder, selected_pack):
        global selected_folder_btn
        # Change the background color of the previously selected button back to normal
        if selected_folder_btn:
            selected_folder_btn.bgcolor = '#343434'
        selected_folder_btn = e.control  # Update the selected button
        selected_folder_btn.bgcolor = '#555555'  # Change the background color to indicate selection

        source_mapping = load_source_mapping(selected_pack['source_mapping_file'], selected_pack['source_dir'])
        update_middle_panel(source_mapping, filter_folder=folder)

    def list_top_level_folders(source_dir):
        return [d for d in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, d))]

    def update_folder_buttons(selected_pack):
        folder_panel_contents.controls.clear()
        source_dir = selected_pack['source_dir']
        top_level_folders = list_top_level_folders(source_dir)
        first = True
        
        for folder in top_level_folders:
            folder_path = os.path.join(source_dir, folder)
            folder_btn = ft.ElevatedButton(
                text=folder,
                on_click=lambda e, f=folder_path, s=selected_pack: on_folder_button_click(e, f, s),
                width=180,
                bgcolor="#2c3033",
                style=ft.ButtonStyle(
                    shape={
                        ft.MaterialState.DEFAULT: ft.RoundedRectangleBorder(radius=2),
                    },
                ),
            )
            folder_panel_contents.controls.append(folder_btn)

            # Automatically select the first folder button
            if first:
                global selected_folder_btn
                selected_folder_btn = folder_btn
                selected_folder_btn.bgcolor = '#555555'  # Highlight color
                first = False
                
    # When a pack icon is clicked
    def on_pack_icon_click(e):
        global selected_pack_icon_btn

        # Reset the background color of the previously selected button
        if selected_pack_icon_btn:
            selected_pack_icon_btn.bgcolor = ft.colors.TRANSPARENT

        selected_pack_icon_btn = e.control
        selected_pack_icon_btn.bgcolor = color_btn_pack_select  # Change the background color to indicate selection

        selected_pack = e.control.data
        source_mapping = load_source_mapping(selected_pack['source_mapping_file'], selected_pack['source_dir'])
        update_folder_buttons(selected_pack)  # Update folder buttons
        update_details_view(selected_pack, editable=False)

        # Get top-level folders and update the middle panel with the first one
        top_level_folders = list_top_level_folders(selected_pack['source_dir'])
        if top_level_folders:
            first_folder = top_level_folders[0]
            update_middle_panel(source_mapping, filter_folder=os.path.join(selected_pack['source_dir'], first_folder))

    def refresh_packs_list():
        global selected_pack_icon_btn, build_btn

        # Clear existing pack icons from the left panel
        left_panel_contents.controls.clear()

        import_btn = ft.Container(
                content=ft.IconButton(icon=ft.icons.ADD_CIRCLE_OUTLINE_OUTLINED, tooltip="Import Resource Pack", icon_size=44, width=60, height=60, bgcolor='#93ba11', icon_color=ft.colors.WHITE, on_click=import_pack),
                margin=ft.margin.only(left=10, right=10, top=5, bottom=5),
            )
        left_panel_contents.controls.append(import_btn)
        
        # Reset the packs dictionary
        packs.clear()

        first_pack = True

        # Find all .config files and load their names
        for config_file in glob.glob("*.config"):
            with open(config_file, 'r') as file:
                build_data = yaml.safe_load(file)
                pack_config_file = build_data.get("pack_config_file", None)
                config_data = None
                if pack_config_file:
                    with open(pack_config_file, 'r') as file:
                        config_data = yaml.safe_load(file)
                source_mapping_file = build_data.get("source_mapping_file", None)
                if source_mapping_file:
                    with open(source_mapping_file, 'r') as file:
                        source_mapping = json.load(file)
                    source_dir = build_data.get("source_dir", None)
                    pack_icon = source_mapping.get("TEXTURE_PACK", {}).get("path", "missing.png")
                    pack_icon_path = os.path.join(source_dir, pack_icon)
                else:
                    pack_icon_path = "unknown.png"
                
                packs[config_file] = {
                    "icon": pack_icon_path, 
                    "config": config_data,
                    "config_file": config_file,
                    "source_dir": source_dir, 
                    "source_mapping_file": source_mapping_file, 
                    "pack_config_file": pack_config_file
                }

                btn_highlight_color = ft.colors.TRANSPARENT

                if first_pack:
                    btn_highlight_color = color_btn_pack_select
                    first_pack = False
                    
                pack_icon_btn = ft.Container(
                    content=ft.Stack(
                        [
                            ft.Image(
                                src=packs[config_file]["icon"],
                                border_radius=30,
                                width=60,
                                height=60,
                            ),
                        ]
                    ),
                    data=packs[config_file],
                    on_click=on_pack_icon_click,
                    width=80,
                    height=70,
                    alignment=ft.alignment.center,
                    bgcolor=btn_highlight_color,
                )
                left_panel_contents.controls.append(pack_icon_btn)

        # After rebuilding the pack list
        if len(left_panel_contents.controls)>1:
            selected_pack_icon_btn = left_panel_contents.controls[1]

        # Build button at the bottom of the left panel
            
        build_btn_color = '#0c74db'
        build_btn_tooltip = "Build all Resource Packs"
        build_btn = ft.IconButton(icon=ft.icons.CONSTRUCTION, icon_color=ft.colors.WHITE, icon_size=40, tooltip=build_btn_tooltip, width=60, height=60, on_click=build_packs, bgcolor=build_btn_color)
        build_btn_container = ft.Container(
                content=build_btn,
                margin=ft.margin.only(left=10, right=10, top=5, bottom=5),
                alignment=ft.alignment.bottom_center,
            )
        if len(packs) > 0:
            left_panel_contents.controls.append(build_btn_container)

        page.update()
    
    # Create containers for layout
    left_panel_contents = ft.Column(spacing=0)
    left_panel = ft.Container(content=left_panel_contents, bgcolor='#121315', width=80, expand=False)

    details_view = ft.Column(spacing=10, expand=True)
    details_container = ft.Container(content=details_view, bgcolor='#121315', expand=False, width=256)
    
    middle_panel_contents = ft.Column(
            spacing=0,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            scroll=ft.ScrollMode.ALWAYS,
            expand=True
        )  
    middle_panel = ft.Container(
            content=middle_panel_contents, 
            alignment=ft.alignment.top_center,
            margin=10, 
            expand=True
        )

    refresh_packs_list()
        
    # Create a column for folder buttons
    folder_panel_contents = ft.Column(
            spacing=2, 
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            scroll=ft.ScrollMode.ALWAYS
        )
    folder_panel = ft.Container(
            content=folder_panel_contents,
            width=200,
            padding=10,
            alignment=ft.alignment.top_center,
            bgcolor='#16171a'
        )

    # Assembling the whole layout

    app_icon='assets/PixelMiner.ico'
    if not os.path.exists(app_icon):
        app_icon = resource_path(app_icon)
    header_row = ft.Row(
                    [
                        ft.Container(ft.Image(src=app_icon, width=40, height=40)),
                        ft.WindowDragArea(ft.Container(ft.Text("PixelMiner Resource Packing Tool"), bgcolor="#0a0a0b", padding=10), expand=True),
                        ft.Container(ft.IconButton(ft.icons.CLOSE, icon_color=ft.colors.WHITE, on_click=lambda _: page.window_close()), bgcolor="#0a0a0b")
                    ],
                    spacing=0
                )
    #disabled since you can't resize frameless windows which is annoying
    #page.window_frameless=True 
    #page.add(header_row)
        

    main_row = ft.Row([left_panel, details_container, folder_panel, middle_panel], spacing=0, expand=True)
    page.add(main_row)

    # Initially display details of the first pack
    if packs:
        first_pack = next(iter(packs.values()))
        source_mapping = load_source_mapping(first_pack['source_mapping_file'], first_pack['source_dir'])
        update_folder_buttons(first_pack)  # Update folder buttons

        top_level_folders = list_top_level_folders(first_pack['source_dir'])
        if top_level_folders:
            first_folder = top_level_folders[0]
            update_middle_panel(source_mapping, filter_folder=os.path.join(first_pack['source_dir'], first_folder))
        update_details_view(first_pack)

if __name__ == "__main__":
    ft.app(target=main)
