import sys
import pathlib
import tkinter

sys.path.append(str(pathlib.Path(__file__).parent))

import Data
import Setting

sys.path.pop()

Data = Data.ImageMap(Data.Data('index'))

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
                Data.store()

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
                if Data.add(file):
                    self._fileLabel['text'] = file.name

        self._after = self.after_idle(self.process)

if __name__ == '__main__':
    root = tkinter.Tk()
    root.wait_visibility() # necessary otherwise the gui won't show up at all

    Frame(root, command = lambda: root.destroy()).pack(fill = tkinter.BOTH)
    
    root.mainloop()