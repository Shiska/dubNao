import sys
import pathlib
import tkinter

sys.path = list(set((*sys.path, str(pathlib.Path(__file__).parent))))

from MediaFrame import MediaFrame
from IndexFrame import IndexFrame
from SettingFrame import SettingFrame

class TrashFrame(tkinter.Frame):
    def __init__(self, master, command = None):
        super().__init__(master)

        self.command = command

        imageMap = IndexFrame.imageMap

        self._items = sorted(((v, key) for key, value in imageMap.trash() for v in value), key = lambda i: pathlib.Path(i[0]).stat().st_mtime)
        self._sauceNaoDir = pathlib.Path(SettingFrame.sauceNaoDir).resolve()
        self._imageMap = imageMap

        oframe = tkinter.LabelFrame(self, text = 'Trash')
        oframe.pack()

        iframe = tkinter.Frame(oframe)
        iframe.pack(expand = True, fill = tkinter.X)

        tkinter.Button(iframe, text = 'Next', command = self._next).pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)
        tkinter.Button(iframe, text = 'Restore', command = self._restore).pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)
        tkinter.Button(iframe, text = 'Delete', command = self._delete).pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)

        frame = self._imageFrame = tkinter.LabelFrame(oframe)
        frame.pack()

        mediaFrame = self._mediaFrame = MediaFrame(frame, onFrameChange = self._onFrameChange)
        mediaFrame.pack()

        self._next()

    def _onFrameChange(self, mframe, thumbnail):
        image = mframe._image.copy()
        image.thumbnail((image.width, self.winfo_screenheight() * 3 // 4))

        mframe._setPhoto(image)

    def _next(self):
        if len(self._items):
            (file, key) = self._items.pop()

            self._file = pathlib.Path(file)

            self._imageFrame['text'] = self._file.name + ' (' + str(len(self._items)) + ' remaining)'
            self._mediaFrame.open(file)
            self._mediaFrame.bind('<Button-1>', lambda e: self._mediaFrame.osOpen())

        elif self.command:
            self.command()

    def _restore(self):
        self._mediaFrame.release()
        self._imageMap.moveFileTo(self._file, self._sauceNaoDir)
        self._next()

    def _delete(self):
        self._mediaFrame.release()
        self._imageMap.delete(self._file)
        self._file.unlink()
        self._next()

if __name__ == '__main__':
    root = tkinter.Tk()
    root.wait_visibility()

    TrashFrame(root, command = lambda: root.after_idle(root.destroy)).pack(fill = tkinter.BOTH)

    root.mainloop()