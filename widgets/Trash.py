import pathlib
import tkinter

import widgets.Data as Data
import widgets.Media as Media
import widgets.SauceNao as SauceNao

class Trash():
    def __init__(self, data):
        self._data = data
        self._list = data.data

    def __len__(self):
        return len(self._list)

    def __getitem__(self, key):
        return self._list[key]

    def store(self):
        self._data.store()

    def add(self, filename: str):
        filename = str(filename)

        if filename not in self._list:
            self._list.append(filename)

    def remove(self, filename: str):
        return self._list.remove(str(filename))

    def pop(self):
        return self._list.pop()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.store()

Data = Trash(Data.Data('trash', list))

class Frame(tkinter.Frame):
    def __init__(self, master, command = None):
        super().__init__(master)

        self.command = command

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

        mediaFrame = self._mediaFrame = Media.Frame(frame, onFrameChange = lambda mframe, thumbnail: Media.Frame.thumbnailScreensize(self, mframe._image))
        mediaFrame.bind('<Button-1>', lambda e: mediaFrame.osOpen())
        mediaFrame.grid(row = 2, column = 0, columnspan = 2, sticky = 'ew')

        self._showIndex()

    def _empty(self):
        if self.command:
            self.command()
        else:
            for oframe in self.pack_slaves():
                for s in oframe.pack_slaves():
                    s.destroy()

            tkinter.Label(oframe, text = 'Empty').pack()

    def _showIndex(self, index = 0):
        length = len(Data)

        if length == 0:
            self._empty()
        else:
            self._index = index

            index = index + 1
            file = pathlib.Path(Data[-index])

            if file.exists():
                self._previousButton['state'] = tkinter.DISABLED if index == 1 else tkinter.NORMAL
                self._nextButton['state'] = tkinter.DISABLED if index == length else tkinter.NORMAL
                self._imageFrame['text'] = file.name + ' (' + str(index) + '/' + str(length) + ')'
                self._mediaFrame.open(str(file))

                self._sizeLabel['text'] = '{} x {}'.format(*self._mediaFrame._image.size)
                self._fileSizeLabel['text'] = file.stat().st_size

                self.update_idletasks()
            else:
                with Data as data:
                    data.pop(-index)

                self._showIndex(index - 1)

    def previous(self, event = None):
        if self._index != 0:
            self._showIndex(self._index - 1)

    def next(self, event = None):
        if self._nextButton['state'] != tkinter.DISABLED:
            self._showIndex(self._index + 1)

    def _popCurrentItem(self):
        index = self._index
        file = self._mediaFrame._filename

        with Data as data:
            data.remove(file)

            if len(data) == index:
                self._showIndex(index - 1)
            else:
                self._showIndex(index)

        return file

    def restore(self, event = None):
        with SauceNao.Data as data:
            data.add(self._popCurrentItem())

    def delete(self, event = None):
        pathlib.Path(self._popCurrentItem()).unlink()

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
            if len(Data):
                file = pathlib.Path(Data.pop())

                fileLabel['text'] = file.name

                file.unlink()

                self.after_idle(step)
            else:
                Data.store()

                self._empty()

        step()

if __name__ == '__main__':
    root = tkinter.Tk()
    root.wait_visibility()

    Frame(root).pack(fill = tkinter.BOTH)

    root.mainloop()