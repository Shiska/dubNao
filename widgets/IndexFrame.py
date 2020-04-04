import pickle
import imghdr
import pathlib
import tkinter
import imagehash
import PIL.Image
import collections

import time

class ImageMap():
    trashDir = pathlib.Path.cwd().joinpath('trash')

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
            hash = self._data[hash]
            hash.add(str(filename))
            hash.discard('__checked__')

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
        if filename:
            if not hash:
                hash = self.getHash(filename)

            if hash:
                hset = self._data[hash]
                filename = str(filename)
                
                if filename in hset:
                    if len(hset) == 1:
                        del self._data[hash]
                    else:
                        hset.remove(filename)
        elif hash:
            hash = self._data.pop(hash, None)

    def __iter__(self):
        for hash, value in list(self._data.items()):
            if '__checked__' not in value:
                files = []

                for v in map(pathlib.Path, list(value)):
                    if not v.exists():
                        self.delete(filename = v, hash = hash)
                        self.store()
                    elif v.parent != self.trashDir:
                        files.append(str(v))

                if len(files):
                    yield hash, files

    def __getitem__(self,key):
        return self._data[key]

    def renameFile(self, src, dest):
        src = pathlib.Path(src)

        if src.exists():
            hash = self.getHash(src)

            if hash:
                s = self._data[hash]
                
                s.remove(str(src))
                s.add(str(dest))
                s.add('__checked__')

                src.touch() # update last modification date
                src.replace(dest)

    def moveFileTo(self, src: str, dest: str, overwrite: bool = True):
        src = pathlib.Path(src)
        dest = pathlib.Path(dest)
        dest.mkdir(exist_ok = True)
        dest = dest.joinpath(src.name)

        if not overwrite and dest.exists():
            name = [dest.stem, '-', '0', dest.suffix]
            idx = 1

            dest = dest.parent.joinpath(''.join(name))
            
            while dest.exists():
                name[2] = str(idx)
                idx = idx + 1

                dest = dest.parent.joinpath(''.join(name))

        self.renameFile(src, dest)

        return dest

    def moveFileToTrash(self, filename: str):
        return self.moveFileTo(filename, self.trashDir, overwrite = False)

class IndexFrame(tkinter.Frame):
    def __init__(self, master, dirs: set, ignoreDirs: set = set(), command = None):
        super().__init__(master)

        self._dirs = set(dirs)
        self._ignore = set(ignoreDirs)
        self._command = command
        self._files = iter(())

        frame = tkinter.LabelFrame(self, text = 'Scanning for files')
        frame.grid_columnconfigure(1, weight = 1)
        frame.grid(sticky = 'NESW')

        tkinter.Label(frame, text = 'Directory:').grid(row = 0, column = 0, sticky = 'e')
        tkinter.Label(frame, text = 'File:').grid(row = 1, column = 0, sticky = 'e')

        self._dirLabel = tkinter.Label(frame)
        self._dirLabel.grid(row = 0, column = 1, sticky = 'w')
        self._fileLabel = tkinter.Label(frame)
        self._fileLabel.grid(row = 1, column = 1, sticky = 'w')

        tkinter.Button(self, text = 'Skip', command = self.skip).grid()

        self._imageMap = ImageMap()
        self._after = self.after_idle(self.process)

        # self.bind('<Configure>', lambda event: self.grid_columnconfigure(0, minsize = event.width)) # increase minsize so it doesn't resize constantly

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

            if not dir in self._ignore:
                self._files = pathlib.Path(dir).iterdir()

                self._dirLabel['text'] = dir
                self._fileLabel['text'] = ''
        else:
            if file.is_dir():
                self._dirs.add(file)
            else:
                if self._imageMap.add(file):
                    self._fileLabel['text'] = file.name

        self._after = self.after_idle(self.process)

if __name__ == '__main__':
    root = tkinter.Tk()
    root.wait_visibility() # necessary otherwise the gui won't show up at all

    IndexFrame(root, [str(pathlib.Path(__file__).absolute().parent)], command = lambda imageMap: root.destroy()).pack()
    
    root.mainloop()