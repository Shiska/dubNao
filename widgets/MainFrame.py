import pickle
import pathlib
import tkinter
import tkinter.filedialog

class MainFrame(tkinter.Frame):
    dirFile = 'dirs.pkl'

    columnDir = 0
    columnIndex = 1
    columnSelect = 2
    columnSauceNao = 3
    columnDest = 4
    columnDelete = 5

    def __init__(self, master, command = None):
        super().__init__(master)

        self.command = command

        self.grid_columnconfigure(self.columnIndex, minsize = 50)
        self.grid_columnconfigure(self.columnSelect, minsize = 50)
        self.grid_columnconfigure(self.columnSauceNao, minsize = 50)
        self.grid_columnconfigure(self.columnDest, minsize = 50)

        label = tkinter.Label(self, text = 'Index')
        label.grid(row = 0, column = self.columnIndex)
        label.ignore = True
        label = tkinter.Label(self, text = 'Select')
        label.grid(row = 0, column = self.columnSelect)
        label.ignore = True
        label = tkinter.Label(self, text = 'SauceNao')
        label.grid(row = 0, column = self.columnSauceNao)
        label.ignore = True
        label = tkinter.Label(self, text = 'Dest')
        label.grid(row = 0, column = self.columnDest)
        label.ignore = True
        button = tkinter.Button(self, text = 'Add', command = lambda: self._add(tkinter.filedialog.askdirectory()))
        button.grid(row = 1, column = self.columnDir, sticky = 'e')
        button.ignore = True
        button = tkinter.Button(self, text = 'Start', command = self._start)
        button.grid(row = 1, column = self.columnIndex, columnspan = self.columnDelete - self.columnIndex)
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

            dir = slaves[self.columnDir]['text']

            dSauceNao = (dir == sauceNao)
            dDest = (dir == dest)

            if dSauceNao or dDest:
                slaves[self.columnSelect].config(state = tkinter.DISABLED)
                slaves[self.columnSelect].deselect()
            else:
                slaves[self.columnSelect].config(state = tkinter.NORMAL)

            slaves[self.columnSauceNao].config(state = tkinter.DISABLED if dDest else tkinter.NORMAL)
            slaves[self.columnDest].config(state = tkinter.DISABLED if dSauceNao else tkinter.NORMAL)

        self._store()

    def _store(self):
        (_, rows) = self.grid_size()

        dirs = set()
        cboxes = dict()

        for r in range(1, rows - 1):
            slaves = {s.grid_info()['column']: s for s in self.grid_slaves(row = r)}
            dir = slaves[self.columnDir]['text']

            dirs.add(dir)
            cboxes[dir] = (slaves[self.columnIndex].var.get(), slaves[self.columnSelect].var.get())

        with open(self.dirFile, 'wb') as file:
            pickle.dump((dirs, cboxes, self._sauceNao.get(), self._dest.get()), file)

    def _add(self, dir: str, ivar: bool = False, svar: bool = False, init: bool = False):
        if not init:
            dirs = [s['text'] for s in self.grid_slaves(column = self.columnDir) if not getattr(s, 'ignore', False)]

            if dir in dirs:
                return

        icheckbox = tkinter.BooleanVar()
        icheckbox.set(ivar)
        scheckbox = tkinter.BooleanVar()
        scheckbox.set(svar)

        (_, row) = self.grid_size()

        for w in self.grid_slaves(row = row - 1):
            w.grid(row = row)
        
        row = row - 1
        dest = self._dest.get()
        sauceNao = self._sauceNao.get()

        label = tkinter.Label(self, text = dir)
        label.grid(row = row, column = self.columnDir, sticky = 'e')

        checkbox = tkinter.Checkbutton(self, variable = icheckbox, command = self._update)
        checkbox.grid(row = row, column = self.columnIndex)
        checkbox.var = icheckbox

        checkbox = tkinter.Checkbutton(self, variable = scheckbox, command = self._update)
        checkbox.grid(row = row, column = self.columnSelect)
        checkbox.var = scheckbox

        if dir in (dest, sauceNao):
            checkbox.config(state = tkinter.DISABLED)

        radio = tkinter.Radiobutton(self, variable = self._sauceNao, value = dir, command = self._update)
        radio.grid(row = row, column = self.columnSauceNao)

        if dir == dest:
            radio.config(state = tkinter.DISABLED)

        radio = tkinter.Radiobutton(self, variable = self._dest, value = dir, command = self._update)
        radio.grid(row = row, column = self.columnDest)

        if dir == sauceNao:
            radio.config(state = tkinter.DISABLED)

        tkinter.Button(self, text = 'Delete', command = lambda: self._delete(label)).grid(row = row, column = self.columnDelete)

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
    def _getRootFolders(folders: list):
        folders = list(map(pathlib.Path, folders))

        for f in folders:
            folders = [x for x in folders if f not in list(x.parents)]

        return folders

    def _start(self):
        (_, rows) = self.grid_size()

        index = [] # all active root folders
        select = [] # all select folders

        special = (self._sauceNao.get(), self._dest.get())

        for r in range(1, rows - 1):
            slaves = {s.grid_info()['column']: s for s in self.grid_slaves(row = r)}
            dir = slaves[self.columnDir]['text']

            if slaves[self.columnIndex].var.get():
                index.append(dir)

            if slaves[self.columnSelect].var.get():
                select.append(dir)

        index = self._getRootFolders(index)
        select = self._getRootFolders(select)

        if self.command:
            self.command(index, select, *special)

if __name__ == '__main__':
    root = tkinter.Tk()

    MainFrame(root).pack()

    root.mainloop()