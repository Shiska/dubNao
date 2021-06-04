import pickle
import imghdr
import pathlib
import imagehash
import collections

import PIL.Image

class Data():
    """
        >>> Data('key').data["key"] = None
        >>> Data('key', default = list).data["key"] = None
        >>> Data('key', filename = 'unknown.file').data["key"] = None
    """
    _data = dict() # shares file data, to avoid reading from the file multiple times
    _dump = dict() # shares file dump, to avoid writing to the file multiple times

    def __init__(self, key: str, default = dict, filename: str = 'data.pkl'):
        self._filename = filename

        try:
            data = self._data[filename]
        except KeyError:
            data = dict()

            if pathlib.Path(filename).is_file():
                with open(filename, 'rb') as file:
                    dump = file.read()

                data = pickle.loads(dump)
            else:
                dump = pickle.dumps(data)

            self._data[filename] = data
            self._dump[filename] = dump

        self._file = data

        try:
            self._data = data[key]
        except KeyError:
            self._data = data[key] = default()

    def store(self):
        dump = pickle.dumps(self._file)

        if dump != self._dump[self._filename]:
            with open(self._filename, 'wb') as file:
                file.write(dump)

            self._dump[self._filename] = dump

    @property
    def data(self):
        return self._data

class ImageMap():
    def __init__(self, data):
        """ >>> _ = ImageMap(Data('')) """

        self._data = data
        self._dict = data.data

    def clear(self):
        """ >>> ImageMap(Data('')).clear() """

        self._dict.clear()

    def store(self):
        self._data.store()

    def __len__(self):
        """
            >>> len(ImageMap(Data('')))
            0
        """
        return len(self._dict)

    def add(self, filename: str) -> str:
        """
            >>> if True:
            ...     map = ImageMap(Data(''))
            ...     file = pathlib.Path('widgets', 'image.png').absolute()
            ...     hash = map.add(file)
            ...     str(file) == next(iter(map.pop()[1]))
            True
        """
        hash = self.getHash(filename)

        if hash:
            self._dict.setdefault(hash, set()).add(str(filename))

        return hash

    def getHash(self, filename: str) -> str:
        file = pathlib.Path(filename)

        # if imghdr.what(file):
        if file.exists():
            try:
                with PIL.Image.open(file) as image:
                    return str(imagehash.phash(image.convert('RGBA')))
            except PIL.UnidentifiedImageError:
                pass

    def remove(self, filename: str = None, hash: str = None, removeKey: bool = True):
        """
            >>> if True:
            ...     map = ImageMap(Data(''))
            ...     file = pathlib.Path('widgets', 'image.png').absolute()
            ...     hash = map.add(file)
            ...     len(map) == 1
            ...     map.remove(file, hash)
            ...     len(map) == 0
            True
            True
        """
        if filename:
            if not hash:
                hash = self.getHash(filename)

            if hash:
                hset = self._dict[hash]
                filename = str(filename)
                
                if filename in hset:
                    if removeKey and len(hset) == 1:
                        del self._dict[hash]
                    else:
                        hset.remove(filename)
        elif hash:
            self._dict.pop(hash, None)

    def _iter_(self):
        remove = []

        for hash, value in self._dict.items():
            files = [v for v in map(pathlib.Path, value) if v.exists()]

            if len(files):
                remove.extend(((v, hash) for v in value.difference(map(str, files))))

                yield hash, files
            else:
                if len(value):
                    remove.extend(((v, hash) for v in value))
                else:
                    remove.append((None, hash))

        for v, hash in remove:
            self.remove(v, hash)

    def __iter__(self):
        """ >>> next(iter(ImageMap(Data(''))), None) """

        for hash, value in self._iter_():
            yield hash, map(str, value)

    def __reversed__(self):
        pass

    def __getitem__(self, key):
        """
            >>> if True:
            ...     map = ImageMap(Data(''))
            ...     map._dict['key'] = 'hi'
            ...     map['key']
            ...     del map._dict['key']
            'hi'
        """

        return [v for v in self._dict[key] if pathlib.Path(v).exists()]

    def __contains__(self, key):
        return (key in self._dict) and (len(self[key]) != 0)

    def renameFile(self, src, dest):
        src = pathlib.Path(src)

        if src.exists():
            hash = self.getHash(src)

            if hash:
                s = self._dict[hash]
                
                s.remove(str(src))
                s.add(str(dest))

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
        return self._dict.popitem()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.store()

    def __len__(self):
        return len(self._dict)

if __name__ == '__main__':
    import doctest

    doctest.testmod()