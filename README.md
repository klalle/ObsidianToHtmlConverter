# ObsidianToHtmlConverter
I made a python script for converting [obsidian](https://obsidian.md/) md-file to static (local) html (recursively adds all link/images)
I made this script for when I need to distribute something from my obsidian vault to someone that either have obsidian, or doesn't.

The script has 2 optional parameters:
1. Export to html or not [**Y**/N]
    - **N**: Exports the choosen md-file to a new vault and bring all the images and linked md-files with it (recursively!)
        - Easily opened as a new vault in obsidian and everything just works!
    - **Y**: Exactly like above, but also create html-files next to the md-files (with images and working links to other md.html-files in vault)
        - The script puts an index.html-file in the root of the exported vault that is a direct link to your exported file.md.html for easily access
2. Download external images to local vault [**Y**/N] (if export to html is chosen)
    - **Y**: downloads all the images
    - **N**: normal link to external image that downloads when viewed

Run this script from the root of obsidian vault

usage: 
```python3 exportMdFileToHtml.py <filename.md> <[y/n] [y/n]>```
- "<filename.md>" **no filepath needed** unless you have several files with same name

Only tesed on Linux and Windows!

