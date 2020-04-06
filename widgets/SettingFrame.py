import enum
import pickle
import pathlib
import tkinter
import tkinter.filedialog

class TextLabel(tkinter.Text):
    def __init__ (self, master, text = ''):
        super().__init__(master, height = 1, borderwidth = 0, width = len(text), wrap = 'none')

        self.insert(1.0, text)
        self.configure(state = 'disabled')

class SettingFrame(tkinter.LabelFrame):
    dirFile = 'settings.pkl'

    column = ('Dir', 'Index', 'Select', 'Ignore', 'Delete')
    column = type('Enum', (), dict((v, i) for i, v in enumerate(column)))

    def __init__(self, master, confirmcommand = None, cancelcommand = None):
        super().__init__(master, text = 'Settings')

        self.confirmcommand = confirmcommand
        self.cancelcommand = cancelcommand

        self._init()

        self._sauceNao.trace('w', lambda *args: self._setDir(self._sauceNao, self._sauceNao.get()))
        self._select.trace('w', lambda *args: self._setDir(self._select, self._select.get()))
        self._trash.trace('w', lambda *args: self._setDir(self._trash, self._trash.get()))
        self._dest.trace('w', lambda *args: self._setDir(self._dest, self._dest.get()))

        frame = tkinter.LabelFrame(self, text = 'Directories')
        frame.grid_columnconfigure(1, weight = 1)
        frame.pack(fill = tkinter.X)

        tkinter.Label(frame, text = 'SauceNao: ').grid(row = 0, column = 0, sticky = 'e')
        tkinter.Label(frame, text = 'Select: ').grid(row = 1, column = 0, sticky = 'e')
        tkinter.Label(frame, text = 'Trash: ').grid(row = 2, column = 0, sticky = 'e')
        tkinter.Label(frame, text = 'Dest: ').grid(row = 3, column = 0, sticky = 'e')

        tkinter.Entry(frame, textvariable = self._sauceNao).grid(row = 0, column = 1, sticky = 'ew')
        tkinter.Entry(frame, textvariable = self._select).grid(row = 1, column = 1, sticky = 'ew')
        tkinter.Entry(frame, textvariable = self._trash).grid(row = 2, column = 1, sticky = 'ew')
        tkinter.Entry(frame, textvariable = self._dest).grid(row = 3, column = 1, sticky = 'ew')

        tkinter.Button(frame, text = '...', command = lambda: self._askDirectory(self._sauceNao)).grid(row = 0, column = 2, padx = 2.5, sticky = 'w')
        tkinter.Button(frame, text = '...', command = lambda: self._askDirectory(self._select)).grid(row = 1, column = 2, padx = 2.5, sticky = 'w')
        tkinter.Button(frame, text = '...', command = lambda: self._askDirectory(self._trash)).grid(row = 2, column = 2, padx = 2.5, sticky = 'w')
        tkinter.Button(frame, text = '...', command = lambda: self._askDirectory(self._dest)).grid(row = 3, column = 2, padx = 2.5, sticky = 'w')

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
        frame.pack(fill = tkinter.X)

        tkinter.Checkbutton(frame, text = 'Autostart', variable = self._autostart).pack()
        tkinter.Checkbutton(frame, text = 'Check for duplicates', variable = self._duplicates).pack()

        frame = tkinter.Frame(self)
        frame.pack(fill = tkinter.X)

        tkinter.Button(frame, text = 'Confirm', command = self._confirm).pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)
        tkinter.Button(frame, text = 'Cancel', command = self._cancel).pack(expand = True, fill = tkinter.X, side = tkinter.RIGHT)

    @classmethod
    def _load(cls):
        with open(cls.dirFile, 'rb') as file:
            data = pickle.load(file)

        (cls._directories, cls._sauceNao._dir, cls._select._dir, cls._trash._dir, cls._dest._dir, autostart, duplicates) = data

        cls._duplicates.set(duplicates)
        cls._autostart.set(autostart)

    @classmethod
    def _store(cls):
        with open(cls.dirFile, 'wb') as file:
            pickle.dump((cls._directories, cls.sauceNaoDir, cls.selectDir, cls.trashDir, cls.destDir, cls.autostart, cls.duplicates), file)

    @classmethod
    def _init(cls):
        cls._init = lambda *args: None

        cls._duplicates = tkinter.BooleanVar()
        cls._autostart = tkinter.BooleanVar()
        cls._sauceNao = tkinter.StringVar()
        cls._select = tkinter.StringVar()
        cls._trash = tkinter.StringVar()
        cls._dest = tkinter.StringVar()

        if pathlib.Path(cls.dirFile).is_file():
            cls._load()
        else:
            cwd = pathlib.Path.cwd()

            cls._directories = dict()
            cls._sauceNao._dir = cwd.joinpath('sauceNao')
            cls._select._dir = cwd.joinpath('select')
            cls._trash._dir = cwd.joinpath('trash')
            cls._dest._dir = cwd.joinpath('dest')

            pathlib.Path.mkdir(cls._sauceNao._dir, exist_ok = True)
            pathlib.Path.mkdir(cls._select._dir, exist_ok = True)
            pathlib.Path.mkdir(cls._trash._dir, exist_ok = True)
            pathlib.Path.mkdir(cls._dest._dir, exist_ok = True)

            cls._sauceNao._dir = str(cls._sauceNao._dir)
            cls._select._dir = str(cls._select._dir)
            cls._trash._dir = str(cls._trash._dir)
            cls._dest._dir = str(cls._dest._dir)

            cls._store()

    def _confirm(self):
        if self.confirmcommand:
            if not self.confirmcommand():
                return

        self._store()

    def _cancel(self):
        if self.cancelcommand:
            self.cancelcommand()

        self._load()

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

        self._directories[label['text']] = (slaves[self.column.Index].var.get(), slaves[self.column.Select].var.get(), slaves[self.column.Ignore].var.get())

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
        del self._directories[label['text']]

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

        for dir, cboxes in self._directories.items():
            self._add(dir, cboxes)

        self._sauceNao.set(self._sauceNao._dir)
        self._select.set(self._select._dir)
        self._trash.set(self._trash._dir)
        self._dest.set(self._dest._dir)

    def pack(self, *args, **kwargs):
        self._resetFrame()

        return super().pack(*args, **kwargs)

    def grid(self, *args, **kwargs):
        self._resetFrame()

        return super().grid(*args, **kwargs)

    def place(self, *args, **kwargs):
        self._resetFrame()

        return super().place(*args, **kwargs)

    class classproperty(classmethod):
        def __get__(self, instance, owner = None):
            owner._init()

            return super().__get__(instance, owner)()

    @classproperty
    def duplicates(cls):
        return cls._duplicates.get()
    @classproperty
    def autostart(cls):
        return cls._autostart.get()
    @classproperty
    def sauceNaoDir(cls):
        return cls._sauceNao._dir
    @classproperty
    def selectDir(cls):
        return cls._select._dir
    @classproperty
    def trashDir(cls):
        return cls._trash._dir
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

if __name__ == '__main__':
    root = tkinter.Tk()

    print(SettingFrame.sauceNaoDir, flush = True)
    print(SettingFrame.selectDir, flush = True)
    print(SettingFrame.trashDir, flush = True)
    print(SettingFrame.destDir, flush = True)
    print(SettingFrame.indexDirs, flush = True)
    print(SettingFrame.selectDirs, flush = True)
    print(SettingFrame.ignoreDirs, flush = True)

    def confirm():
        root.after_idle(root.destroy)
        return True

    SettingFrame(root, confirmcommand = confirm, cancelcommand = root.destroy).pack(fill = tkinter.BOTH)

    root.mainloop()