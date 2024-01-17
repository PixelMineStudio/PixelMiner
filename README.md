![PIXELMINER](https://github.com/PixelMineStudio/PixelMiner/assets/6824189/dae85673-d7bf-42f5-8485-ce790923c45f)
# PixelMiner

Build Process for Texture Packs

![image](https://github.com/PixelMineStudio/PixelMiner/assets/6824189/4c984fce-561d-4dba-b8df-76e8f5b576c4)

Been working on a project over the holidays that I've wanted to make for about 5 years. It's a resource pack builder. So it takes your textures in your resource pack and let's you organize them into a more artist friendly set of source file directories, then compiles versions of those textures for all minecraft versions, java and bedrock.

### Installation

1. Download the latest release here: https://github.com/PixelMineStudio/PixelMiner/releases/latest
2. Copy to your preferred working dirctory
3. Run PixelMiner.exe
4. Some folders and files should be automatically created
5. Import an existing resource pack: https://github.com/PixelMineStudio/PixelMiner/wiki/Importing-Resource-Packs
6. Edit your pack as needed
7. Build to various minecraft versions: https://github.com/PixelMineStudio/PixelMiner/wiki/Building-Versions

### Features

So far the list of features is something like this:

- **Mostly data-driven**: very little is hard coded, technically you could use it for ANY game or project where you need to manipulate images or files of any kind.
- **Source Files**: Keep Source Files in any folder structure and even in different UV layouts.
- **Custom File Locations**: Work from any drive of folder path.
- **Community-driven Conversions**: If a new pack format for Minecraft comes out you can edit the mapping files yourself without having to wait for any updates.
- **Variable Injection** Text files can be injected with custom variables for things like pack.mcmeta or manifest.json files.
- **File Fallbacks** Specify fallback files to be used during the build process if the pack is missing those files.
- **Complex Atlas Creation**: 
    - Grid style, where you either specify a list of images and it populates the grid
    - Sticker style, where you load each image and tell it exactly where you want it to go within a canvas
    - Remap style, where you can cut parts out of existing texture(s) and paste them onto a canvas. This is mostly used for changing models from one UV layout to another.
    - TGAs style, mostly for Bedrock where the RGB is a combination of multiple textures and the alpha is taken from multiple textures and made separately.
- **Complete Pack Builds**: Zips and renames the output as you decide, for example .MCPACK files.
- **Downsample Textures**: Creates downsampled resolutions of packs
- **Version and Resolution Overrides**: Allows for resolution and version specific texture overrides. Version overrides are inclusive of lower versions.
- **Pack Importer**: You can import multiple resource packs and the importer will rename and move all textures as specified in your pack mapping.
- **Source Explorer**: The GUI allows you to explore all source files and open then directly or their source folder.

### Limitations & Things to Improve

- TGA files are currently made by combining the Java PNGs in a destructive manner, meaning that the import of these files doesn't allow for their creation to be reversed.
- Version Mapping files are very time consuming to edit, since they contain a lot of duplicate data.
- While it is technically possible to include model files in the version mappings there is no system for automatically importing the textures used by those models, so you need to add entries in source and version mappings for for each model you want to add any new textures used by those models.

