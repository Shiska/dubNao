import pickle
import imghdr
import pathlib
import tkinter
import imagehash
import PIL.Image
import collections

import time

class ImageMap():
    def __init__(self, filename: str = 'imageshashes.pkl'):
        self._filename = filename

        if pathlib.Path(filename).is_file():
            with open(filename, 'rb') as file:
                self._data = pickle.load(file)
        else:
            self._data = collections.defaultdict(set)

    def store(self):
        with open(self._filename, 'wb') as file:
            pickle.dump(self._data, file)

    def add(self, filename: str) -> str:
        hash = self.getHash(filename)

        if hash:
            self._data[hash].add(filename)

        return hash

    def getHash(self, filename: str) -> str:
        file = pathlib.Path(filename)

        if imghdr.what(file):
            try:
                image = PIL.Image.open(file)
            except PIL.UnidentifiedImageError:
                pass
            else:
                return str(imagehash.phash(image.convert('RGBA')))

    def delete(self, filename: str = None, hash: str = None):
        if hash:
            hash = self._data.pop(hash, None)

        if filename:
            hash = self.getHash(filename)

            if hash:
                hset = self._data[hash]
                
                if filename in hset:
                    if len(hset) == 1:
                        del self._data[hash]
                    else:
                        hset.remove(filename)

        return hash

    def __iter__(self):
        for key, value in self._data.items():
            yield key, value

    def renameFile(self, src, dest):
        src = pathlib.Path(src)

        if src.exists():
            hash = self.getHash(src)

            if hash:
                s = self._data[hash]
                s.remove(src)
                s.add(dest)

                src.touch() # update last modification date
                src.rename(dest)

    def moveFileToTrash(self, file):
        file = pathlib.Path(file)

        path = pathlib.Path.cwd().joinpath('trash')
        path.mkdir(exist_ok = True)
        path = path.joinpath(file.name)

        if path.exists():
            name = [path.stem, '-', '0', path.suffix]
            idx = 1

            path = path.parent.joinpath(''.join(name))
            
            while path.exists():
                name[2] = str(idx)
                idx = idx + 1

                path = path.parent.joinpath(''.join(name))

        self.renameFile(file, path)

        return path


class IndexFrame(tkinter.Frame):
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

        self._imageMap = ImageMap()
        self._after = self.after_idle(self.process)

        self.bind('<Configure>', lambda event: self.grid_columnconfigure(0, minsize = event.width)) # increase minsize so it doesn't resize constantly

    def skip(self):
        if self._after:
            self.after_cancel(self._after)

        if self._command:
            self._command(self._imageMap)

    def process(self):
        self._after = None

        file = next(self._files, None)

        if not file:
            if len(self._dirs) == 0:
                self._imageMap.store()

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
                if self._imageMap.add(file):
                    self._fileLabel['text'] = file.name

        self._after = self.after_idle(self.process)

if __name__ == '__main__':
    root = tkinter.Tk()
    root.wait_visibility() # necessary otherwise the gui won't show up at all

    IndexFrame(root, str(pathlib.Path(__file__).absolute().parent), command = lambda imageMap: root.destroy()).pack()
    
    root.mainloop()