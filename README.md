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
* The directory *Temp* stores the image files waiting to be processed.
* The directory *Dest* will contain the sorted images based on the results of SauceNAO.
### Search
Here you can add directories which will be indexed and / or moved to the *Temp* directory.  
Additionally you can select subdirectories which can be ignored by the indexer.
### Misc
* *autostart*: Start directly into the SauceNAO frame.  
* *check for dublicates*: Displays dublicates additionally to new files.  
* *Autoselect*: X seconds before a perfect match (0 difference in all present images) will be skipped.

## SauceNAO frame
Looks up the selected images in the *Temp* directory and moves them to *Dest*.

## Index frame
Search all given directories (checkbox *Index*) without (checkbox *Ignore*) for image files.

## Select frame
Moves all indexed files from given directories (checkbox *Select*) without (checkbox *Ignore*) to the *Temp* directory.  
Afterwards it displays the files grouped by the hash, the buttons have the following functions:
* *Next*: Marks selected files as *SauceNAO*, marks unselected as *Trash*.
* *Difference*: Shows the highest color difference for each image, move the mouse over another image to set it as comparison target (by default the leftmost image).
* *Delete*: Marks all files as *Trash* no matter if selected or not.

## Trash frame

* *Left*, *Right*: Moves to previous / next image in trash.
* *Restore*: Marks file as *SauceNAO*.
* *Delete*: Permanently deletes file from disk.
* *Delete All*: Deletes all *Trash* files.