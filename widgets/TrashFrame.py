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

        self._items = sorted((v for _, value in imageMap.trash() for v in map(pathlib.Path, value)), key = lambda v: v.stat().st_mtime, reverse = True)
        self._sauceNaoDir = pathlib.Path(SettingFrame.sauceNaoDir).resolve()
        self._imageMap = imageMap
        self.focus_set()

        self.bind('<Left>',     self.previous)
        self.bind('<Up>',       self.restore)
        self.bind('<Down>',     self.delete)
        self.bind('<Right>',    self.next)

        oframe = tkinter.LabelFrame(self, text = 'Trash')
        oframe.pack()

        iframe = tkinter.Frame(oframe)
        iframe.pack(expand = True, fill = tkinter.X)

        self._previousButton = tkinter.Button(iframe, text = 'Previous (Left)', command = self.previous)
        self._previousButton.pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)

        self._nextButton = tkinter.Button(iframe, text = 'Next (Right)', command = self.next)
        self._nextButton.pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)

        tkinter.Button(iframe, text = 'Restore (Up)', command = self.restore).pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)
        tkinter.Button(iframe, text = 'Delete (Down)', command = self.delete).pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)

        frame = self._imageFrame = tkinter.LabelFrame(oframe)
        frame.pack()

        mediaFrame = self._mediaFrame = MediaFrame(frame, onFrameChange = self._onFrameChange)
        mediaFrame.bind('<Button-1>', lambda e: mediaFrame.osOpen())
        mediaFrame.pack()

        self._showIndex(0)

    def _onFrameChange(self, mframe, thumbnail):
        image = mframe._image.copy()
        image.thumbnail((image.width, self.winfo_screenheight() * 3 // 4))

        mframe._setPhoto(image)

    def _empty(self):
        if self.command:
            self.command()
        else:
            for oframe in self.pack_slaves():
                for s in oframe.pack_slaves():
                    s.destroy()

            tkinter.Label(oframe, text = 'Empty').pack()

    def _showIndex(self, index):
        length = len(self._items)

        if length == 0:
            self._empty()
        else:
            self._index = index
            file = self._items[index]
            index = index + 1

            self._previousButton['state'] = tkinter.DISABLED if index == 1 else tkinter.NORMAL
            self._nextButton['state'] = tkinter.DISABLED if index == length else tkinter.NORMAL
            self._imageFrame['text'] = file.name + ' (' + str(index) + '/' + str(length) + ')'
            self._mediaFrame.open(str(file))

    def previous(self, event = None):
        if self._index != 0:
            self._showIndex(self._index - 1)

    def next(self, event = None):
        index = self._index + 1

        if index != len(self._items):
            self._showIndex(index)

    def _popCurrentItem(self):
        index = self._index
        file = self._items.pop(index)
        length = len(self._items)

        if length == index:
            self._showIndex(index - 1)
        else:
            self._showIndex(index)

        return file

    def restore(self, event = None):
        self._imageMap.moveFileTo(self._popCurrentItem(), self._sauceNaoDir)

    def delete(self, event = None):
        file = self._popCurrentItem()

        self._imageMap.delete(file)
        file.unlink()

if __name__ == '__main__':
    root = tkinter.Tk()
    root.wait_visibility()

    TrashFrame(root).pack(fill = tkinter.BOTH)

    root.mainloop()