import sys
import pickle
import pathlib
import tkinter

sys.path.append(str(pathlib.Path(__file__).parent))

import Media
import SauceNao

sys.path.pop()

class Data():
    def __init__(self, filename: str = 'trash.pkl'):
        self._filename = filename

        if pathlib.Path(filename).is_file():
            with open(filename, 'rb') as file:
                self._data = pickle.load(file)
        else:
            self._data = list()

    def store(self):
        with open(self._filename, 'wb') as file:
            pickle.dump(self._data, file)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def add(self, filename: str):
        filename = str(filename)

        if filename not in self._data:
            self._data.append(filename)

    def remove(self, filename: str):
        return self._data.remove(str(filename))

    def pop(self):
        return self._data.pop()

class Frame(tkinter.Frame):
    def __init__(self, master, command = None):
        super().__init__(master)

        self.command = command

        self._data = Data()
        self._sauceNaoData = SauceNao.Data()
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
        length = len(self._data)

        if length == 0:
            self._empty()
        else:
            self._index = index

            index = index + 1
            file = pathlib.Path(self._data[-index])

            if file.exists():
                self._previousButton['state'] = tkinter.DISABLED if index == 1 else tkinter.NORMAL
                self._nextButton['state'] = tkinter.DISABLED if index == length else tkinter.NORMAL
                self._imageFrame['text'] = file.name + ' (' + str(index) + '/' + str(length) + ')'
                self._mediaFrame.open(str(file))

                self._sizeLabel['text'] = '{} x {}'.format(*self._mediaFrame._image.size)
                self._fileSizeLabel['text'] = file.stat().st_size

                self.update_idletasks()

    def previous(self, event = None):
        if self._index != 0:
            self._showIndex(self._index - 1)

    def next(self, event = None):
        if self._nextButton['state'] != tkinter.DISABLED:
            self._showIndex(self._index + 1)

    def _popCurrentItem(self):
        index = self._index
        file = self._mediaFrame._filename

        self._data.remove(file)

        if len(self._data) == index:
            self._showIndex(index - 1)
        else:
            self._showIndex(index)

        self._data.store()

        return file

    def restore(self, event = None):
        self._sauceNaoData.add(self._popCurrentItem())
        self._sauceNaoData.store()

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
            if len(self._data):
                file = pathlib.Path(self._data.pop())

                fileLabel['text'] = file.name

                file.unlink()

                self.after_idle(step)
            else:
                self._data.store()
                self._empty()

        step()

if __name__ == '__main__':
    root = tkinter.Tk()
    root.wait_visibility()

    Frame(root).pack(fill = tkinter.BOTH)

    root.mainloop()