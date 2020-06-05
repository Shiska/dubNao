# dubNao
Python GUI (tkinter) for sorting images with SauceNAO ([pysaucenao](https://github.com/FujiMakoto/pysaucenao)).

## Requirements
* python3

*make.bat* will try to setup an virtual environment with the following packages (you do not need to intall them by yourself):
* pillow
* ImageHash
* pysaucenao
* opencv-python
* python-slugify

### Windows N- and KN
Requires Media Feature Pack found in Settings / Optional Feature or in DISM /Online.

### Linux
Check opencv-python documentation, pypi: "almost any GNU/Linux distribution".

## Settings frame
### Directories
The first three directories: *SauceNAO*, *Select* and *Trash* are to temporary storing the image files and are default set to subdirectories of the python directory.
The last directory *Dest* will contain the sorted images based on the results of SauceNAO.
### Search
Here you can add directories which will be indexed and / or moved to the *Select* directory.  
Additionally you can select subdirectories which can be ignored by the indexer.
### Misc
* *autostart*: Start directly into the SauceNAO frame.  
*  *check for dublicates*: Displays dublicates additionally to new files.  
* *Autoselect*: X seconds before a perfect match (0 difference in all present images) will be skipped.

## SauceNAO frame
Looks up the images in the *SauceNAO* directory and moves them to *Dest*, images need to indexed!
Moving files directly into the *SauceNAO* directry isn't recommended, you would need to reindex the whole directory each time.

## Index frame
Search all given directories (checkbox *Index*) without (checkbox *Ignore*) for image files.

## Select frame
Moves all indexed files from given directories (checkbox *Select*) without (checkbox *Ignore*) to the *Select* directory.  
Afterwards it displays the files grouped by the hash, the buttons have the following functions:
* *Next*: Moves selected files to *SauceNAO* directory, moves unselected to *Trash* directory.
* *Difference*: Shows the highest color difference for each image, move the mouse over another image to set it as comparison target (by default the leftmost image).
* *Delete*: Moves all file to *Trash* directory no matter if selected or not.

## Trash frame

* *Left*, *Right*: Moves to previous / next image in trash.
* *Restore*: Moves file to *SauceNAO* directory.
* *Delete*: Permanently deletes file from disk.
* *Delete All*: Clears the *Trash* directory.
