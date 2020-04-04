import enum
import pickle
import pathlib
import tkinter
import tkinter.filedialog


class MainFrame(tkinter.Frame):
    dirFile = 'dirs.pkl'

    column = ('Dir', 'Index', 'Select', 'SauceNao', 'Dest', 'Ignore', 'Delete')
    column = type('Enum', (), dict((v, i) for i, v in enumerate(column)))

    def __init__(self, master, command = None):
        super().__init__(master)

        self.command = command
        
        self.grid_columnconfigure(self.column.Index, minsize = 50)
        self.grid_columnconfigure(self.column.Select, minsize = 50)
        self.grid_columnconfigure(self.column.SauceNao, minsize = 50)
        self.grid_columnconfigure(self.column.Dest, minsize = 50)

        label = tkinter.Label(self, text = 'Index')
        label.grid(row = 0, column = self.column.Index)
        label.ignore = True
        label = tkinter.Label(self, text = 'Select')
        label.grid(row = 0, column = self.column.Select)
        label.ignore = True
        label = tkinter.Label(self, text = 'SauceNao')
        label.grid(row = 0, column = self.column.SauceNao)
        label.ignore = True
        label = tkinter.Label(self, text = 'Dest')
        label.grid(row = 0, column = self.column.Dest)
        label.ignore = True
        label = tkinter.Label(self, text = 'Ignore')
        label.grid(row = 0, column = self.column.Ignore)
        label.ignore = True
        button = tkinter.Button(self, text = 'Add', command = lambda: self._add(tkinter.filedialog.askdirectory()))
        button.grid(row = 1, column = self.column.Dir, sticky = 'e')
        button.ignore = True
        button = tkinter.Button(self, text = 'Start', command = self._start)
        button.grid(row = 1, column = self.column.Index, columnspan = self.column.Delete - self.column.Index)
        button.ignore = True

        self._sauceNao = tkinter.StringVar()
        self._dest = tkinter.StringVar()

        if pathlib.Path(self.dirFile).is_file():
            with open(self.dirFile, 'rb') as file:
                (dirs, cboxes, sauceNao, dest) = pickle.load(file)

            self._sauceNao.set(sauceNao)
            self._dest.set(dest)

            for dir in sorted(dirs):
                self._add(dir, *cboxes[dir], init = True)

    def _update(self):
        (_, rows) = self.grid_size()

        sauceNao = self._sauceNao.get()
        dest = self._dest.get()

        for r in range(1, rows - 1):
            slaves = {s.grid_info()['column']: s for s in self.grid_slaves(row = r)}

            if slaves[self.column.Ignore].var.get():
                slaves[self.column.Index].config(state = tkinter.DISABLED)
                slaves[self.column.Index].deselect()
                slaves[self.column.Select].config(state = tkinter.DISABLED)
                slaves[self.column.Select].deselect()
                slaves[self.column.SauceNao].config(state = tkinter.DISABLED)
                slaves[self.column.SauceNao].deselect()
                slaves[self.column.Dest].config(state = tkinter.DISABLED)
                slaves[self.column.Dest].deselect()
            else:
                slaves[self.column.Index].config(state = tkinter.NORMAL)

                dir = slaves[self.column.Dir]['text']
                dSauceNao = (dir == sauceNao)
                dDest = (dir == dest)

                if dSauceNao or dDest:
                    slaves[self.column.Select].config(state = tkinter.DISABLED)
                    slaves[self.column.Select].deselect()
                else:
                    slaves[self.column.Select].config(state = tkinter.NORMAL)

                slaves[self.column.SauceNao].config(state = tkinter.DISABLED if dDest else tkinter.NORMAL)
                slaves[self.column.Dest].config(state = tkinter.DISABLED if dSauceNao else tkinter.NORMAL)

        self._store()

    def _store(self):
        (_, rows) = self.grid_size()

        dirs = set()
        cboxes = dict()

        for r in range(1, rows - 1):
            slaves = {s.grid_info()['column']: s for s in self.grid_slaves(row = r)}
            dir = slaves[self.column.Dir]['text']

            dirs.add(dir)
            cboxes[dir] = (slaves[self.column.Index].var.get(), slaves[self.column.Select].var.get(), slaves[self.column.Ignore].var.get())

        with open(self.dirFile, 'wb') as file:
            pickle.dump((dirs, cboxes, self._sauceNao.get(), self._dest.get()), file)

    def _add(self, dir: str, ivar: bool = False, svar: bool = False, gvar: bool = False, init: bool = False, row: int = None):
        if dir:
            if not init:
                dirs = [s['text'] for s in self.grid_slaves(column = self.column.Dir) if not getattr(s, 'ignore', False)]

                if dir in dirs:
                    return

                if not row:
                    dirs.append(dir)

                    row = sorted(dirs).index(dir) + 1 # plus header row

            icheckbox = tkinter.BooleanVar()
            icheckbox.set(ivar)
            scheckbox = tkinter.BooleanVar()
            scheckbox.set(svar)
            gcheckbox = tkinter.BooleanVar()
            gcheckbox.set(gvar)

            (_, rows) = self.grid_size()

            if not row:
                row = rows - 1

            for r in range(rows, row, -1):
                for w in self.grid_slaves(row = r - 1):
                    w.grid(row = r)

            dest = self._dest.get()
            sauceNao = self._sauceNao.get()

            label = tkinter.Label(self, text = dir)
            label.grid(row = row, column = self.column.Dir, sticky = 'e')

            checkbox = tkinter.Checkbutton(self, variable = icheckbox, command = self._update)
            checkbox.grid(row = row, column = self.column.Index)
            checkbox.var = icheckbox

            if gvar:
                checkbox.config(state = tkinter.DISABLED)

            checkbox = tkinter.Checkbutton(self, variable = scheckbox, command = self._update)
            checkbox.grid(row = row, column = self.column.Select)
            checkbox.var = scheckbox

            if gvar or dir in (dest, sauceNao):
                checkbox.config(state = tkinter.DISABLED)

            radio = tkinter.Radiobutton(self, variable = self._sauceNao, value = dir, command = self._update)
            radio.grid(row = row, column = self.column.SauceNao)

            if gvar or dir == dest:
                radio.config(state = tkinter.DISABLED)

            radio = tkinter.Radiobutton(self, variable = self._dest, value = dir, command = self._update)
            radio.grid(row = row, column = self.column.Dest)

            if gvar or dir == sauceNao:
                radio.config(state = tkinter.DISABLED)

            checkbox = tkinter.Checkbutton(self, variable = gcheckbox, command = self._update)
            checkbox.grid(row = row, column = self.column.Ignore)
            checkbox.var = gcheckbox

            tkinter.Button(self, text = 'Delete', command = lambda: self._delete(label)).grid(row = row, column = self.column.Delete)

            if not init:
                self._store()

    def _delete(self, label: tkinter.Label):
        (_, rows) = self.grid_size()

        dir = label['text']
        row = label.grid_info()['row']
        
        for s in self.grid_slaves(row = row):
            s.destroy()

        for r in range(row, rows):
            for s in self.grid_slaves(row = r):
                s.grid(row = r - 1)

        self._store()

    @staticmethod
    def _getRootFolders(folders: set):
        folders = list(map(pathlib.Path, folders))

        for f in folders:
            folders = [x for x in folders if f not in list(x.parents)]

        return set(folders)

    def _start(self):
        (_, rows) = self.grid_size()

        index = set() # all active root folders
        select = set() # all select folders
        ignore = set() # all ignored folders

        for r in range(1, rows - 1):
            slaves = {s.grid_info()['column']: s for s in self.grid_slaves(row = r)}
            dir = slaves[self.column.Dir]['text']

            if slaves[self.column.Index].var.get():
                index.add(dir)

            if slaves[self.column.Select].var.get():
                select.add(dir)

            if slaves[self.column.Ignore].var.get():
                ignore.add(dir)

        index = self._getRootFolders(index)
        select = self._getRootFolders(select)
        ignore = self._getRootFolders(ignore)

        if self.command:
            self.command(index, select, ignore, self._sauceNao.get(), self._dest.get())

if __name__ == '__main__':
    root = tkinter.Tk()

    MainFrame(root).pack(expand = True, fill = tkinter.BOTH)

    root.mainloop()