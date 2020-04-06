import sys
import pathlib
import tkinter

sys.path = list(set((*sys.path, str(pathlib.Path(__file__).parent))))

from MediaFrame import MediaFrame
from IndexFrame import IndexFrame
from SettingFrame import SettingFrame

class SauceNaoFrame(tkinter.Frame): #todo get frames after images were created, instead of getting the thumbnail twice!
    def __init__(self, master):
        super().__init__(master)

if __name__ == '__main__':
    root = tkinter.Tk()
    root.wait_visibility()

    SauceNaoFrame(root).pack(fill = tkinter.BOTH)

    root.mainloop()