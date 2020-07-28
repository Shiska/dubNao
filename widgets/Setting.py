import enum
import pickle
import pathlib
import tkinter
import tkinter.filedialog

class Data():
    file = 'settings.pkl'

    def __init__(self):
        return self.init()

    @classmethod
    def init(cls):
        cls.init = lambda *args: None

        cls._duplicates = tkinter.BooleanVar()
        cls._autostart = tkinter.BooleanVar()
        cls._autoselect = tkinter.IntVar()
        cls._temp = tkinter.StringVar()
        cls._dest = tkinter.StringVar()

        if pathlib.Path(cls.file).is_file():
            return cls.load()

        cwd = pathlib.Path.cwd()

        cls._directories = dict()
        cls._temp._dir = cwd.joinpath('tmp')
        cls._dest._dir = cwd.joinpath('dest')

        pathlib.Path.mkdir(cls._temp._dir, exist_ok = True)
        pathlib.Path.mkdir(cls._dest._dir, exist_ok = True)

        cls._temp._dir = str(cls._temp._dir)
        cls._dest._dir = str(cls._dest._dir)

        return cls.store()

    @classmethod
    def load(cls):
        with open(cls.file, 'rb') as file:
            (cls._directories, cls._temp._dir, cls._dest._dir, autostart, duplicates, autoselect) = pickle.load(file)

        cls._duplicates.set(duplicates)
        cls._autoselect.set(autoselect)
        cls._autostart.set(autostart)

    @classmethod
    def store(cls):
        with open(cls.file, 'wb') as file:
            pickle.dump((cls._directories, cls.tempDir, cls.destDir, cls.autostart, cls.duplicates, cls.autoselect), file)

    class classproperty(property):
        def __get__(self, instance, owner):
            return super().__get__(owner, owner.init())

    @classproperty
    def duplicates(cls):
        return cls._duplicates.get()
    @classproperty
    def autostart(cls):
        return cls._autostart.get()
    @classproperty
    def autoselect(cls):
        return cls._autoselect.get()
    @classproperty
    def tempDir(cls):
        return cls._temp._dir
    @classproperty
    def destDir(cls):
        return cls._dest._dir
    @classproperty
    def indexDirs(cls):
        return cls.getRootFolders({dir for dir, cboxes in cls._directories.items() if cboxes[0]})
    @classproperty
    def selectDirs(cls):
        return cls.getRootFolders({dir for dir, cboxes in cls._directories.items() if cboxes[1]})
    @classproperty
    def ignoreDirs(cls):
        return cls.getRootFolders({dir for dir, cboxes in cls._directories.items() if cboxes[2]})

    @staticmethod
    def getRootFolders(folders: set):
        folders = [pathlib.Path(f).resolve() for f in folders]

        for f in folders:
            folders = [x for x in folders if f not in list(x.parents)]

        return set(folders)

class Frame(tkinter.LabelFrame):
    column = ('Dir', 'Index', 'Select', 'Ignore', 'Delete')
    column = type('Enum', (), dict((v, i) for i, v in enumerate(column)))

    def __init__(self, master, confirmcommand = None, cancelcommand = None):
        super().__init__(master, text = 'Settings')

        self.confirmcommand = confirmcommand
        self.cancelcommand = cancelcommand

        Data.init()

        Data._temp.trace('w', lambda *args: self._setDir(Data._temp, Data._temp.get()))
        Data._dest.trace('w', lambda *args: self._setDir(Data._dest, Data._dest.get()))

        frame = tkinter.LabelFrame(self, text = 'Directories')
        frame.grid_columnconfigure(1, weight = 1)
        frame.pack(fill = tkinter.X)

        tkinter.Label(frame, text = 'Tmp: ').grid(row = 2, column = 0, sticky = 'e')
        tkinter.Label(frame, text = 'Dest: ').grid(row = 3, column = 0, sticky = 'e')

        tkinter.Entry(frame, textvariable = Data._temp).grid(row = 2, column = 1, sticky = 'ew')
        tkinter.Entry(frame, textvariable = Data._dest).grid(row = 3, column = 1, sticky = 'ew')

        tkinter.Button(frame, text = '...', command = lambda: self._askDirectory(Data._temp)).grid(row = 2, column = 2, padx = 2.5, sticky = 'w')
        tkinter.Button(frame, text = '...', command = lambda: self._askDirectory(Data._dest)).grid(row = 3, column = 2, padx = 2.5, sticky = 'w')

        frame = self._folderFrame = tkinter.LabelFrame(self, text = 'Search')
        frame.pack(fill = tkinter.X)
        frame.grid_columnconfigure(self.column.Dir, weight = 1)
        frame.grid_columnconfigure(self.column.Index, minsize = 50)
        frame.grid_columnconfigure(self.column.Select, minsize = 50)
        frame.grid_columnconfigure(self.column.Ignore, minsize = 50)
        frame.grid_columnconfigure(self.column.Delete, weight = 1)

        tkinter.Button(frame, text = 'Add', command = lambda: self._add(tkinter.filedialog.askdirectory())).grid(row = 0, column = self.column.Dir, sticky = 'e')
        tkinter.Label(frame, text = 'Index').grid(row = 0, column = self.column.Index)
        tkinter.Label(frame, text = 'Select').grid(row = 0, column = self.column.Select)
        tkinter.Label(frame, text = 'Ignore').grid(row = 0, column = self.column.Ignore)

        frame = tkinter.LabelFrame(self, text = 'Misc')
        frame.grid_columnconfigure(0, weight = 1)
        frame.grid_columnconfigure(3, weight = 1)
        frame.pack(fill = tkinter.X)

        tkinter.Checkbutton(frame, text = 'Autostart', variable = Data._autostart).grid(column = 1, columnspan = 2)
        tkinter.Checkbutton(frame, text = 'Check for duplicates', variable = Data._duplicates).grid(column = 1, columnspan = 2)
        tkinter.Label(frame, text = 'Autoselect (seconds): ').grid(row = 2, column = 1, sticky = 'e')
        tkinter.Spinbox(frame, from_ = 0, to_ = 99, width = 2, textvariable = Data._autoselect).grid(row = 2, column = 2, sticky = 'w')

        frame = tkinter.Frame(self)
        frame.pack(fill = tkinter.X)

        tkinter.Button(frame, text = 'Confirm', command = self._confirm).pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)
        tkinter.Button(frame, text = 'Cancel', command = self._cancel).pack(expand = True, fill = tkinter.X, side = tkinter.RIGHT)

    def _confirm(self):
        if self.confirmcommand:
            if not self.confirmcommand():
                return

        Data.store()

    def _cancel(self):
        if self.cancelcommand:
            self.cancelcommand()

        Data.load()

    def _setDir(self, variable, dir):
        path = pathlib.Path(dir)

        if path.is_dir():
            variable._dir = str(path.resolve()) if dir else dir

    def _askDirectory(self, variable):
        dir = tkinter.filedialog.askdirectory(mustexist = True, initialdir = variable._dir)

        if dir:
            variable.set(pathlib.Path(dir))

    def _update(self, label: tkinter.Label):
        slaves = {s.grid_info()['column']: s for s in self._folderFrame.grid_slaves(row = label.grid_info()['row'])}

        if slaves[self.column.Ignore].var.get():
            slaves[self.column.Index].config(state = tkinter.DISABLED)
            slaves[self.column.Index].deselect()
            slaves[self.column.Select].config(state = tkinter.DISABLED)
            slaves[self.column.Select].deselect()
        else:
            slaves[self.column.Index].config(state = tkinter.NORMAL)
            slaves[self.column.Select].config(state = tkinter.NORMAL)

        Data._directories[label['text']] = (slaves[self.column.Index].var.get(), slaves[self.column.Select].var.get(), slaves[self.column.Ignore].var.get())

    def _add(self, dir: str, vars: tuple = (False, False, False), row: int = None):
        if dir:
            dir = pathlib.Path(dir)
            dirs = [pathlib.Path(s['text']) for s in self._folderFrame.grid_slaves(column = self.column.Dir) if isinstance(s, tkinter.Label)]

            if dir in dirs:
                return

            if not row:
                dirs.append(dir)

                row = sorted(dirs).index(dir) + 1 # plus header row

            (ivar, svar, gvar) = vars

            icheckbox = tkinter.BooleanVar()
            icheckbox.set(ivar)
            scheckbox = tkinter.BooleanVar()
            scheckbox.set(svar)
            gcheckbox = tkinter.BooleanVar()
            gcheckbox.set(gvar)

            (_, rows) = self._folderFrame.grid_size()

            if not row:
                row = rows

            for r in range(rows, row, -1):
                for w in self._folderFrame.grid_slaves(row = r - 1):
                    w.grid(row = r)

            label = tkinter.Label(self._folderFrame, text = dir)
            label.grid(row = row, column = self.column.Dir, sticky = 'e')

            update = lambda: self._update(label)

            checkbox = tkinter.Checkbutton(self._folderFrame, variable = icheckbox, command = update)
            checkbox.grid(row = row, column = self.column.Index)
            checkbox.var = icheckbox
            checkbox = tkinter.Checkbutton(self._folderFrame, variable = scheckbox, command = update)
            checkbox.grid(row = row, column = self.column.Select)
            checkbox.var = scheckbox
            checkbox = tkinter.Checkbutton(self._folderFrame, variable = gcheckbox, command = update)
            checkbox.grid(row = row, column = self.column.Ignore)
            checkbox.var = gcheckbox

            update()

            tkinter.Button(self._folderFrame, text = 'Delete', command = lambda: self._delete(label)).grid(row = row, column = self.column.Delete, sticky = 'w')

    def _delete(self, label: tkinter.Label):
        (_, rows) = self._folderFrame.grid_size()
        grid_slaves = self._folderFrame.grid_slaves

        row = label.grid_info()['row']
        del Data._directories[label['text']]

        for s in grid_slaves(row = row):
            s.destroy()

        for r in range(row, rows):
            for s in grid_slaves(row = r):
                s.grid(row = r - 1)

    def _resetFrame(self):
        (_, rows) = self._folderFrame.grid_size()
        grid_slaves = self._folderFrame.grid_slaves

        for r in range(1, rows):
            for s in grid_slaves(row = r):
                s.destroy()

        for dir, cboxes in Data._directories.items():
            self._add(dir, cboxes)

        Data._temp.set(Data._temp._dir)
        Data._dest.set(Data._dest._dir)

    def pack(self, *args, **kwargs):
        self._resetFrame()

        return super().pack(*args, **kwargs)

    def grid(self, *args, **kwargs):
        self._resetFrame()

        return super().grid(*args, **kwargs)

    def place(self, *args, **kwargs):
        self._resetFrame()

        return super().place(*args, **kwargs)

if __name__ == '__main__':
    root = tkinter.Tk()

    print(Data.duplicates, flush = True)
    print(Data.autostart, flush = True)
    print(Data.autoselect, flush = True)
    print(Data.tempDir, flush = True)
    print(Data.destDir, flush = True)
    print(Data.indexDirs, flush = True)
    print(Data.selectDirs, flush = True)
    print(Data.ignoreDirs, flush = True)

    def confirm():
        root.after_idle(root.destroy)
        return True

    Frame(root, confirmcommand = confirm, cancelcommand = root.destroy).pack(fill = tkinter.BOTH)

    root.mainloop()