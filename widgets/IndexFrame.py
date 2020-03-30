import pickle
import imghdr
import pathlib
import tkinter
import imagehash
import PIL.Image

import time

class IndexFrame(tkinter.Frame):
    pklFile = 'imageshashes.pkl'

    def __init__(self, master, *paths: str, command = None):
        super().__init__(master)

        self._dirs = list(paths)
        self._command = command
        self._files = iter(())

        tkinter.Label(self, text = 'Scanning for files...').grid()

        self._dirLabel = tkinter.Label(self)
        self._dirLabel.grid()
        self._fileLabel = tkinter.Label(self)
        self._fileLabel.grid()

        tkinter.Button(self, text = 'Skip', command = self.skip).grid()

        if pathlib.Path(self.pklFile).is_file():
            with open(self.pklFile, 'rb') as file:
                self._imageMap = pickle.load(file)
        else:
            self._imageMap = {}

        self._after = self.after_idle(self.process)

        self.bind('<Configure>', lambda event: self.grid_columnconfigure(0, minsize = event.width)) # increase minsize so it doesn't resize constantly

    def skip(self):
        if self._after:
            self.after_cancel(self._after)

        if self._command:
            self._command(self._imageMap)

    def store(self):
        with open(self.pklFile, 'wb') as file:
            pickle.dump(self._imageMap, file)

    def process(self):
        self._after = None

        file = next(self._files, None)

        if not file:
            if len(self._dirs) == 0:
                self.store()

                return self.skip()

            dir = self._dirs.pop()

            print(str(dir).encode('utf-8'), flush = True)

            self._files = pathlib.Path(dir).iterdir()

            self._dirLabel['text'] = dir
            self._fileLabel['text'] = ''
        else:
            if file.is_dir():
                self._dirs.append(file)
            else:
                if imghdr.what(file):
                    try:
                        im = PIL.Image.open(file)
                    except PIL.UnidentifiedImageError:
                        pass
                    else:
                        self._fileLabel['text'] = file.name

                        file = str(file)
                        hash = str(imagehash.phash(im.convert('RGBA')))

                        if hash in self._imageMap:
                            if not file in self._imageMap[hash]:
                                self._imageMap[hash].add(file)
                                self._imageMap[hash].discard('ignore')
                        else:
                            self._imageMap[hash] = {file}

        self._after = self.after_idle(self.process)

if __name__ == '__main__':
    root = tkinter.Tk()
    root.wait_visibility() # necessary otherwise the gui won't show up at all

    IndexFrame(root, str(pathlib.Path(__file__).absolute().parent), command = lambda imageMap: root.destroy()).pack()
    
    root.mainloop()