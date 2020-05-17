import pathlib
import tkinter

if '.' in __name__:
    from .MediaFrame import MediaFrame
    from .IndexFrame import IndexFrame
    from .SettingFrame import SettingFrame
else:
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
        tkinter.Button(iframe, text = 'Delete All', command = self.clear).pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)

        frame = self._imageFrame = tkinter.LabelFrame(oframe)
        frame.pack()

        tkinter.Label(frame, text = 'Size:').grid(row = 0, column = 0, sticky = 'e')
        tkinter.Label(frame, text = 'Filesize:').grid(row = 1, column = 0, sticky = 'e')

        self._sizeLabel = tkinter.Label(frame)
        self._sizeLabel.grid(row = 0, column = 1, sticky = 'w')
        self._fileSizeLabel = tkinter.Label(frame)
        self._fileSizeLabel.grid(row = 1, column = 1, sticky = 'w')

        mediaFrame = self._mediaFrame = MediaFrame(frame, onFrameChange = self._onFrameChange)
        mediaFrame.bind('<Button-1>', lambda e: mediaFrame.osOpen())
        mediaFrame.grid(row = 2, column = 0, columnspan = 2, sticky = 'ew')

        self._showIndex()

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

    def _showIndex(self, index = 0):
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

            self._sizeLabel['text'] = '{} x {}'.format(*self._mediaFrame._image.size)
            self._fileSizeLabel['text'] = file.stat().st_size

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

    def clear(self, event = None):
        for oframe in self.pack_slaves():
            for s in oframe.pack_slaves():
                s.destroy()

        frame = tkinter.Frame(oframe)
        frame.grid_columnconfigure(1, weight = 1)
        frame.pack()

        tkinter.Label(frame, text = 'Deleting file:').grid(row = 0, column = 0, sticky = 'e')

        fileLabel = tkinter.Label(frame)
        fileLabel.grid(row = 0, column = 1, sticky = 'w')

        fileLabel.bind('<Configure>', lambda event: frame.grid_columnconfigure(1, minsize = event.width)) # increase minsize so it doesn't resize constantly

        def step():
            if len(self._items):
                file = self._items.pop()

                fileLabel['text'] = file.name

                self._imageMap.delete(file)

                file.unlink()

                self.after_idle(step)
            else:
                self._empty()

        step()

if __name__ == '__main__':
    root = tkinter.Tk()
    root.wait_visibility()

    TrashFrame(root).pack(fill = tkinter.BOTH)

    root.mainloop()