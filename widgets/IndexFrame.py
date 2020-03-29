import pickle
import imghdr
import pathlib
import tkinter
import imagehash
import PIL.Image

import time

class IndexFrame(tkinter.Frame):
    pklFile = 'imageshashes.pkl'

    def __init__(self, master, command, *paths: str):
        super().__init__(master)

        self._dirs = list(paths)
        self._command = command
        self._files = iter(())

        tkinter.Label(self, text = 'Scanning for files...').pack()

        self._dirLabel = tkinter.Label(self)
        self._dirLabel.pack()
        self._fileLabel = tkinter.Label(self)
        self._fileLabel.pack()

        tkinter.Button(self, text = 'Skip', command = self.skip).pack()

        if pathlib.Path(self.pklFile).is_file():
            with open(self.pklFile, 'rb') as file:
                self._imageMap = pickle.load(file)
        else:
            self._imageMap = {}

        master.wait_visibility() # necessary otherwise the gui won't show up at all

        self._after = self.after_idle(self.process) # wait before starting but after wait_visibility!

    def skip(self):
        if self._after:
            self.after_cancel(self._after)

        return self._command()

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

    IndexFrame(root, root.destroy, str(pathlib.Path(__file__).absolute().parent)).pack()
    
    root.mainloop()