![PIXELMINER](https://github.com/PixelMineStudio/PixelMiner/assets/6824189/dae85673-d7bf-42f5-8485-ce790923c45f)
# PixelMiner


Build Process for Texture Packs

![image](https://github.com/PixelMineStudio/PixelMiner/assets/6824189/4c984fce-561d-4dba-b8df-76e8f5b576c4)

Been working on a project over the holidays that I've wanted to make for about 5 years. It's a resource pack builder. So it takes your textures in your resource pack and let's you organize them into a more artist friendly set of source file directories, then compiles versions of those textures for all minecraft versions, java and bedrock.

## Installation

1. Download the latest release here: https://github.com/PixelMineStudio/PixelMiner/releases/latest
2. Copy to your preferred working dirctory
3. Run PixelMiner.exe
4. Some folders and files should be automatically created

## Features

So far the list of features is something like this:

- **Mostly data-driven**: very little is hard coded, technically you could use it for ANY game or project where you need to manipulate images or files of any kind.
- **Source Files**: Keep Source Files in any folder structure and even in different UV layouts.
- **Custom File Locations**: Work from any drive of folder path.
- **Community-driven Conversions**: If a new pack format for Minecraft comes out you can edit the mapping files yourself without having to wait for any updates.
- **Variable Injection** Text files can be injected with custom variables for things like pack.mcmeta or manifest.json files.
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

## Limitations & Things to Improve

- TGA files are currently made by combining the Java PNGs in a destructive manner, meaning that the import of these files doesn't allow for their creation to be reversed.
- Version Mapping files are very time consuming to edit, since they contain a lot of duplicate data.
- While it is technically possible to include model files in the version mappings there is no system for automatically importing the textures used by those models, so you need to add entries in source and version mappings for for each model you want to add any new textures used by those models.

## Importing Resource Packs

![image](https://github.com/PixelMineStudio/PixelMiner/assets/6824189/08dc6f33-8391-4f01-90dc-6279c8fce63a)

The pack importer looks up the pack_format and reverses the build process for that version, pushing the files into a specified source directory. You can do this with your existing resource_pack or any of the minecraft defaults.

**Note**: the version mappings are far from perfect and will take some work to become complete. So you might notice some missing images in the imported source that are present in the pack before importing. To correct this you can add the image to the version mapping files, create a UID for it and add it to the source_mapping.json and specify where you want the file to live. If you re-import your pack the file will be present.

**Note**: the atlas currently does not run on the importer. So if you are importing older pack_formats the imported images might be incorrect.

**[Pack].json**

This file lives in the root beside the exe and contains the paths for all things related to the imported pack. You can of course edit these and move the files if needed. By default all packs use the same version_mappings_file, but you could duplicate this directory and create a unique set of mappings for different needs.

```
#Resource Pack Build Config

#Directories
source_dir: "SmoothOperator"
mappings_dir: 'Version_Mappings'
output_dir: "Pack_Builds"
log_output_dir: "Pack_Builds/_logs"
tempfile_dir: "Pack_Builds/_temp"

#Files
pack_config_file: 'SmoothOperator/pack.config'
version_mappings_file: 'Version_Mappings/version_mappings.json'
source_mapping_file: 'SmoothOperator/source_mapping.json'
```

**[Pack]/Pack.json**

Inside the source_dir for the pack is the pack.json. This is sort of editable from within the GUI, but you can also edit it here.

You can add additional variables and they shoudl show up in the GUI. These variables can be injected into files (see below)

```
name: Smooth Operator
description: \u00A75PixelMine.com\u00A76
pack_version_number:
- 0
- 9
- 45
resolutions:
  0: 256x
  1: 128x
  2: 64x
  3: 32x
pack_uuid: 2ede356d-10de-49b7-90ca-486dc57c9e62
module_uuid: 649119bf-6fd5-4ee6-9c06-9c213e0b00f7
```

**Source_Mapping.json**

The source mapping file creates UIDs for every file in your resource pack, that is later used to match to a build UID mapping file for each version you want to build. This is a HUGE file with every texture and file that can be build for any version. Right now this is not connected to the editor, except that the editor looks at this file and loads all the file in it, if the file is missing it displays a placeholder image.

```
    "META_PACK_JAVA": {
        "path"  : "pack/pack.mcmeta",
        "inject": "TRUE"
    },
    "META_PACK_BEDROCK": {
        "path"  : "pack/manifest.json",
        "inject": "TRUE"
    },
    "TEXTURE_PACK": {
        "path": "pack/pack.png",
        "resolution": [128, 128]
    }
```

### Source File Organization

![image](https://github.com/PixelMineStudio/PixelMiner/assets/6824189/ba8e2134-986f-4700-b8e3-e5f1e50c50df)

Since the source files are connected through the build process by the UIDs, it is possible to reloacte any of the images to other folders in any way that you want. Just be careful to update the source_mapping.json when you do. Disconnected images won't display in the editor, so they will be hard to find.

You can have as many subdirectories as you want, although I would advise against it. All files are displayed in the editor by their root directory. So Mobs are all in their own subdirectories, but in the editor they all appear under the MOB folder.

## Resolution and Version Overrides

It is possible to create version overrides as well as 

**Version Overrides**

Here is an example of a version override in the [Pack]/source_mapping.json file for water. Version overrides are retroactive, meaning they apply to any earlier version as well.

```
    "TEXTURE_WATER_STILL": {
        "path": "vfx/water_still.png",
        "resolution": [16, 512],
        "versions": {
            "1.12.2": { "path": "vfx/water_still_legacy.png", "resolution": [16, 512] }
        }
    }
```

**Resolution Overrides**

Adding "_XXpx" to the end of any image file will force the build process to use this image for that exact resolution output of the image. This is **not** inclusive of higehr or lower resolutions, so it will only work at that specific reoslution.

```
sword_diamond.png <-- 256x256 resolution
sword_diamond_64px.png <-- 64x64 resolution
sword_diamond_32px.png <-- 32x32 resolution
```

In this example the original version is 256x256 pixels, to the 128px version would be a downsample of the original, the 64px and the 32px verisons would be used without rescale and the 16px version would be a downsample of the original.

## Placeholder previews

You can edit missing file placeholders that are in the "assets" folder.

**Fallback Files**

The source mapping file for each resource pack can include fallback files for any files that will be applied during the build process. This is primarily used for converting Java to Bedrock, since when you import a Bedrock pack it will not include a pack.mcmeta file by default.

```
    "META_PACK_JAVA": {
        "path": "pack/pack.mcmeta",
        "fallback": "assets/template_pack.mcmeta",
        "inject": "TRUE"
    }
```

## Variable Injections

Add "inject": "TRUE" to any source file definition will cause the build process to open the file (assuming it is a text file) and attempt to replace any %placeholder% variables with the same name as any of the variables defined in the pack.config. This is how the build process is able to handle pack.mcmeta, version.mcmeta and manifest.json file difference in various platforms and formats.

```
    "META_PACK_JAVA": {
        "path"  : "pack/pack.mcmeta",
        "inject": "TRUE"
    }
```

## Building Versions

![image](https://github.com/PixelMineStudio/PixelMiner/assets/6824189/e36092b4-3ac3-4507-b552-ddb411dd4e5d)

**Version_Mappings/version_mappings.json**

The verion mappings folder is where all the pack definitions live. This JSON file is what the build process looks at to determine what to build. It starts at the top and works it's way down the list. Technically, you could add more platforms/games at the top level.

```
{
    "Java": {
        "1.16.5": { "pack_format": 6 },
        "1.17.1": { "pack_format": 7 },
        "1.18.2": { "pack_format": 8 },
        "1.19.2": { "pack_format": 9 },
        "1.19.3": { "pack_format": 12 },
        "1.19.4": { "pack_format": 13 },
        "1.20.1": { "pack_format": 15 },
        "1.20.2": { "pack_format": 18 },
        "1.20.4": { "pack_format": 22 },
        "1.8.9": { "pack_format": 1 },
        "1.12.2": { "pack_format": 3 },
        "1.10.2": { "pack_format": 2 },
        "1.14.4": { "pack_format": 4 },
        "1.16.1": { "pack_format": 5 }
    },
    "Bedrock": {
        "1.20.50": { "pack_format": 2, "zip_extension": ".mcpack" }
    }
}
```

The first 2 levels of this JSON map directly to the expected folder structure.

**Java/1.20.4**

The pack folders contain any number of json files. It could be 1 it could be 100. Whatever is easiest for you to manage.

Each json item needs a "source" which is a UID and a "destination" which is the relative path location within the final pack.

```
    {
        "source": "TEXTURE_PACK",
        "destination": "pack.png"
    }
```

More complex definitions are possible using the "type" key and can be "grid", "stamp" or "tga" values.

#### GRID Atlas

The Grid type is the most simple atlas type. You give it a list of UIDs and a grid size and it places the textures into the grid. Just be careful that the number of textures does not exceed the total grid size. Shit explodes.

```
    {
        "type": "grid",
        "source": [
            "TEXTURE_EXPERIENCE_ORB_01",
            "TEXTURE_EXPERIENCE_ORB_02",
            "TEXTURE_EXPERIENCE_ORB_03",
            "TEXTURE_EXPERIENCE_ORB_04",
            "TEXTURE_EXPERIENCE_ORB_05",
            "TEXTURE_EXPERIENCE_ORB_06",
            "TEXTURE_EXPERIENCE_ORB_07",
            "TEXTURE_EXPERIENCE_ORB_08",
            "TEXTURE_EXPERIENCE_ORB_09",
            "TEXTURE_EXPERIENCE_ORB_10",
            "TEXTURE_EXPERIENCE_ORB_11",
            "TEXTURE_EXPERIENCE_ORB_12",
            "TEXTURE_EXPERIENCE_ORB_13",
            "TEXTURE_EXPERIENCE_ORB_14",
            "TEXTURE_EXPERIENCE_ORB_15",
            "TEXTURE_EXPERIENCE_ORB_16"
        ],
        "destination": "assets/minecraft/textures/entity/experience_orb.png",
        "grid_size": [
            4,
            4
        ]
    }
```

#### STAMP Atlas

The "stamp" type of atlas is one where the individual images are placed onto the atlas like stickers.

The old particles sheet is a good example of how a stamp atlas would look like, also the old paintings.png

```
    {
        "type": "stamp",
        "source": [
            { "uid": "TEXTURE_GENERIC_0"   , "position": [  0,   0] },
            { "uid": "TEXTURE_GENERIC_1"   , "position": [  8,   0] },
            { "uid": "TEXTURE_GENERIC_2"   , "position": [ 16,   0] },
            { "uid": "TEXTURE_GENERIC_3"   , "position": [ 24,   0] },
            { "uid": "TEXTURE_GENERIC_4"   , "position": [ 32,   0] },
            { "uid": "TEXTURE_GENERIC_5"   , "position": [ 40,   0] },
            { "uid": "TEXTURE_GENERIC_6"   , "position": [ 48,   0] },
            { "uid": "TEXTURE_GENERIC_7"   , "position": [ 56,   0] },
            { "uid": "TEXTURE_SPLASH_0"    , "position": [ 16,   8] },
            { "uid": "TEXTURE_SPLASH_1"    , "position": [ 24,   8] },
            { "uid": "TEXTURE_SPLASH_2"    , "position": [ 32,   8] },
            { "uid": "TEXTURE_BUBBLE"      , "position": [  0,  16] },
            { "uid": "TEXTURE_FISHING_HOOK", "position": [  8,  16] },
            { "uid": "TEXTURE_FLASH"       , "position": [ 32,  16] },
            { "uid": "TEXTURE_FLAME"       , "position": [  0,  24] },
            { "uid": "TEXTURE_LAVA"        , "position": [  8,  24] },
            { "uid": "TEXTURE_NOTE"        , "position": [  0,  32] },
            { "uid": "TEXTURE_CRITICAL_HIT", "position": [  8,  32] },
            { "uid": "TEXTURE_LAVA"        , "position": [ 16,  32] },
            { "uid": "TEXTURE_DAMAGE"      , "position": [ 24,  32] },
            { "uid": "TEXTURE_HEART"       , "position": [  0,  40] },
            { "uid": "TEXTURE_ANGRY"       , "position": [  8,  40] },
            { "uid": "TEXTURE_GLINT"       , "position": [ 16,  40] },
            { "uid": "TEXTURE_LAVA"        , "position": [ 24,  40] },
            { "uid": "TEXTURE_LAVA"        , "position": [  0,  48] },
            { "uid": "TEXTURE_LAVA"        , "position": [  8,  48] },
            { "uid": "TEXTURE_DRIP_HANG"   , "position": [  0,  56] },
            { "uid": "TEXTURE_DRIP_FALL"   , "position": [  8,  56] },
            { "uid": "TEXTURE_DRIP_LAND"   , "position": [ 16,  56] },
            { "uid": "TEXTURE_EFFECT_0"    , "position": [  0,  64] },
            { "uid": "TEXTURE_EFFECT_1"    , "position": [  8,  64] },
            { "uid": "TEXTURE_EFFECT_2"    , "position": [ 16,  64] },
            { "uid": "TEXTURE_EFFECT_3"    , "position": [ 24,  64] },
            { "uid": "TEXTURE_EFFECT_4"    , "position": [ 32,  64] },
            { "uid": "TEXTURE_EFFECT_5"    , "position": [ 40,  64] },
            { "uid": "TEXTURE_EFFECT_6"    , "position": [ 48,  64] },
            { "uid": "TEXTURE_EFFECT_7"    , "position": [ 56,  64] },
            { "uid": "TEXTURE_SPELL_0"     , "position": [  0,  72] },
            { "uid": "TEXTURE_SPELL_1"     , "position": [  8,  72] },
            { "uid": "TEXTURE_SPELL_2"     , "position": [ 16,  72] },
            { "uid": "TEXTURE_SPELL_3"     , "position": [ 24,  72] },
            { "uid": "TEXTURE_SPELL_4"     , "position": [ 32,  72] },
            { "uid": "TEXTURE_SPELL_5"     , "position": [ 40,  72] },
            { "uid": "TEXTURE_SPELL_6"     , "position": [ 48,  72] },
            { "uid": "TEXTURE_SPELL_7"     , "position": [ 56,  72] },
            { "uid": "TEXTURE_SPARK_0"     , "position": [  0,  80] },
            { "uid": "TEXTURE_SPARK_1"     , "position": [  8,  80] },
            { "uid": "TEXTURE_SPARK_2"     , "position": [ 16,  80] },
            { "uid": "TEXTURE_SPARK_3"     , "position": [ 24,  80] },
            { "uid": "TEXTURE_SPARK_4"     , "position": [ 32,  80] },
            { "uid": "TEXTURE_SPARK_5"     , "position": [ 40,  80] },
            { "uid": "TEXTURE_SPARK_6"     , "position": [ 48,  80] },
            { "uid": "TEXTURE_SPARK_7"     , "position": [ 56,  80] },
            { "uid": "TEXTURE_GLITTER_0"   , "position": [  0,  88] },
            { "uid": "TEXTURE_GLITTER_1"   , "position": [  8,  88] },
            { "uid": "TEXTURE_GLITTER_2"   , "position": [ 16,  88] },
            { "uid": "TEXTURE_GLITTER_3"   , "position": [ 24,  88] },
            { "uid": "TEXTURE_GLITTER_4"   , "position": [ 32,  88] },
            { "uid": "TEXTURE_GLITTER_5"   , "position": [ 40,  88] },
            { "uid": "TEXTURE_GLITTER_6"   , "position": [ 48,  88] },
            { "uid": "TEXTURE_GLITTER_7"   , "position": [ 56,  88] },
            { "uid": "TEXTURE_SGA_A"       , "position": [  8, 112] },
            { "uid": "TEXTURE_SGA_B"       , "position": [ 16, 112] },
            { "uid": "TEXTURE_SGA_C"       , "position": [ 24, 112] },
            { "uid": "TEXTURE_SGA_D"       , "position": [ 32, 112] },
            { "uid": "TEXTURE_SGA_E"       , "position": [ 40, 112] },
            { "uid": "TEXTURE_SGA_F"       , "position": [ 48, 112] },
            { "uid": "TEXTURE_SGA_G"       , "position": [ 56, 112] },
            { "uid": "TEXTURE_SGA_H"       , "position": [ 64, 112] },
            { "uid": "TEXTURE_SGA_I"       , "position": [ 72, 112] },
            { "uid": "TEXTURE_SGA_J"       , "position": [ 80, 112] },
            { "uid": "TEXTURE_SGA_K"       , "position": [ 88, 112] },
            { "uid": "TEXTURE_SGA_L"       , "position": [ 96, 112] },
            { "uid": "TEXTURE_SGA_M"       , "position": [104, 112] },
            { "uid": "TEXTURE_SGA_N"       , "position": [112, 112] },
            { "uid": "TEXTURE_SGA_O"       , "position": [120, 112] },
            { "uid": "TEXTURE_SGA_P"       , "position": [  0, 120] },
            { "uid": "TEXTURE_SGA_Q"       , "position": [  8, 120] },
            { "uid": "TEXTURE_SGA_R"       , "position": [ 16, 120] },
            { "uid": "TEXTURE_SGA_S"       , "position": [ 24, 120] },
            { "uid": "TEXTURE_SGA_T"       , "position": [ 32, 120] },
            { "uid": "TEXTURE_SGA_U"       , "position": [ 40, 120] },
            { "uid": "TEXTURE_SGA_V"       , "position": [ 48, 120] },
            { "uid": "TEXTURE_SGA_W"       , "position": [ 56, 120] },
            { "uid": "TEXTURE_SGA_X"       , "position": [ 56, 120] },
            { "uid": "TEXTURE_SGA_Y"       , "position": [ 56, 120] },
            { "uid": "TEXTURE_SGA_Z"       , "position": [ 56, 120] }
        ],
        "destination": "assets/minecraft/textures/particle/particles.png",
        "canvas_size": [128, 128]
    }
```

If you are feeling fancy you can also use the "stamp" atlas to cut parts out of images and compile them. This is sueful for textures where the UV layout has changed but the model has not, so the sizes of the parts is consistent.

"copy" is the part of the image you want to use. "rotate" let's you do clock-wise rotations, ideally in increments of 90. "position" is as above. You can also "flip" the image "Horizonal" or "Vertical" (case sensitive) if you need to. The default "stamp" just assumed a "copy" of the entire image in the code.

Parts are stamped from the top down in the json list and the alpha values will "accumulate" so you can paste alpha images on top of alpha images.

Note: The positions are relative to the original images sizes as defined in the UID_mapping.json. So even if your images are 1024x1024 the mapping might be at a 64x64 scale, like in the example below for the bed.

```
    {
        "type": "stamp",
        "source": [
            { "uid": "TEXTURE_BED_RED", "copy": [6, 0, 22, 6], "rotate": 180, "position": [0, 7] },
            { "uid": "TEXTURE_BED_RED", "copy": [53, 21, 56, 24], "position": [0, 13] },
            { "uid": "TEXTURE_BED_RED", "copy": [50, 9, 53, 12], "position": [13, 13] }
        ],
        "destination": "assets/minecraft/textures/blocks/bed_head_end.png",
        "canvas_size": [16, 16]
    },
```

#### TGA Atlas

Technically "tga" are the "stamp" type atlas but the RGB is filled 100% white first. I will probably remove this in the future and just make a way to generate a solid colour image as a layer in the atlas. Anyway, so all of this you can technically use as part of the "stamp" atlas type if you wanted to.

    "use_for_alpha" uses the alpha of the texture only and replaces the alpha channel that exists if there is one.
    "alpha_add" layers the texture alpha values on top of the existing alpha values additively by the specified amount.

So the example below is how we generate the Bedrock leggings item texture from the java images. Also of note is that if you don't specify a position for the "stamp" it assumes the top corner.

Any "stamp" or "tga" type atlas will be saved as a TGA file if the desination path ends in .tga.

```
    {
        "type": "tga",
        "source": [
            { "uid": "TEXTURE_LEATHER_LEGGINGS" },
            { "uid": "TEXTURE_LEATHER_LEGGINGS_OVERLAY" },
            { "uid": "TEXTURE_LEATHER_LEGGINGS", "use_for_alpha": "True" },
            { "uid": "TEXTURE_LEATHER_LEGGINGS_OVERLAY", "alpha_add": 0.1 }
            
        ],
        "destination": "textures/items/leather_leggings.tga",
        "canvas_size": [16, 16]
    }
```
