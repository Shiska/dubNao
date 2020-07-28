import sys
import pickle
import imghdr
import pathlib
import tkinter
import imagehash
import PIL.Image
import collections

sys.path.append(str(pathlib.Path(__file__).parent))

import Setting

sys.path.pop()

class ImageMap():
    def __init__(self, filename: str = 'imageshashes.pkl'):
        self._filename = filename
        self._modified = False

        if pathlib.Path(filename).is_file():
            with open(filename, 'rb') as file:
                self._data = pickle.load(file)
        else:
            self._data = collections.defaultdict(set)

    def store(self):
        if self._modified:
            self._modified = False

            with open(self._filename, 'wb') as file:
                pickle.dump(self._data, file)

    def clear(self):
        self._modified = True
        self._data.clear()

    def __len__(self):
        return len(self._data)

    def add(self, filename: str) -> str:
        hash = self.getHash(filename)

        if hash:
            hash = self._data[hash]
            hash.add(str(filename))

            self._modified = True

        return hash

    def getHash(self, filename: str) -> str:
        file = pathlib.Path(filename)

        # if imghdr.what(file):
        try:
            with PIL.Image.open(file) as image:
                return str(imagehash.phash(image.convert('RGBA')))
        except PIL.UnidentifiedImageError:
            pass

    def remove(self, filename: str = None, hash: str = None):
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

                    self._modified = True
        elif hash:
            if self._data.pop(hash, None):
                self._modified = True

    def _iter_(self):
        remove = []

        for hash, value in self._data.items():
            files = [v for v in map(pathlib.Path, value) if v.exists()]

            if len(files):
                remove.extend(((v, hash) for v in value.difference(map(str, files))))

                yield hash, files
            else:
                remove.extend(((v, hash) for v in value))

        for v, hash in remove:
            self.remove(v, hash)

        self.store()

    def __iter__(self):
        for hash, value in self._iter_():
            yield hash, map(str, value)

    def __getitem__(self, key):
        return self._data[key]

    def renameFile(self, src, dest):
        src = pathlib.Path(src)

        if src.exists():
            hash = self.getHash(src)

            if hash:
                s = self._data[hash]
                
                s.remove(str(src))
                s.add(str(dest))

                self._modified = True

                src.touch() # update last modification date
                src.replace(dest)

    def moveFileTo(self, src: str, dest: str, overwrite: bool = False):
        src = pathlib.Path(src)
        dest = pathlib.Path(dest)
        dest.mkdir(parents = True, exist_ok = True)
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

    def pop(self):
        self._modified = True

        return self._data.popitem()

def Data():
    return ImageMap('index.pkl')

class Frame(tkinter.Frame):
    def __init__(self, master, command = None):
        super().__init__(master)

        self._command = command

        oframe = tkinter.Frame(self)
        oframe.pack()

        frame = tkinter.LabelFrame(oframe, text = 'Scanning for files')
        frame.grid_columnconfigure(1, weight = 1)
        frame.grid(sticky = 'ew')

        tkinter.Label(frame, text = 'Directory:').grid(row = 0, column = 0, sticky = 'e')
        tkinter.Label(frame, text = 'File:').grid(row = 1, column = 0, sticky = 'e')

        self._data = Data()
        self._dirLabel = tkinter.Label(frame)
        self._dirLabel.grid(row = 0, column = 1, sticky = 'w')
        self._fileLabel = tkinter.Label(frame)
        self._fileLabel.grid(row = 1, column = 1, sticky = 'w')

        frame = tkinter.Frame(oframe)
        frame.grid(sticky = 'ew')

        self._scanButton = tkinter.Button(frame)
        self._scanButton.pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)

        tkinter.Button(frame, text = 'Skip', command = self.skip).pack(expand = True, fill = tkinter.X, side = tkinter.RIGHT)

        frame.bind('<Configure>', lambda event: oframe.grid_columnconfigure(0, minsize = event.width)) # increase minsize so it doesn't resize constantly

        self.after_idle(self.quickscan)

    def fullscan(self):
        self._scanButton.config(text = 'Quickscan', command = self.quickscan)

        self._dirs = Setting.Data.getRootFolders([Setting.Data.tempDir, Setting.Data.destDir, *iter(Setting.Data.indexDirs), *iter(Setting.Data.selectDirs)])
        self._ignore = set(Setting.Data.ignoreDirs)
        self._files = iter(())

        self._after = self.after_idle(self.process)

    def quickscan(self):
        self._scanButton.config(text = 'Fullscan', command = self.fullscan)

        self._dirs = set(Setting.Data.indexDirs)
        self._ignore = set(Setting.Data.ignoreDirs)
        self._files = iter(())

        self._after = self.after_idle(self.process)

    def skip(self):
        if self._after:
            self.after_cancel(self._after)

        if self._command:
            self._command()

    def process(self):
        self._after = None

        file = next(self._files, None)

        if not file:
            if len(self._dirs) == 0:
                self._data.store()

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
                if self._data.add(file):
                    self._fileLabel['text'] = file.name

        self._after = self.after_idle(self.process)

if __name__ == '__main__':
    root = tkinter.Tk()
    root.wait_visibility() # necessary otherwise the gui won't show up at all

    Frame(root, command = lambda: root.destroy()).pack(fill = tkinter.BOTH)
    
    root.mainloop()