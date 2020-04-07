import widgets
import tkinter

class Application(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.wait_visibility()

        self.attributes("-fullscreen", True)
        self.title('Dublicate finder')

        self.menubar = tkinter.Menu(self)
        self.menubar.add_command(label = 'Indexing', command = self._index)
        self.menubar.add_command(label = 'Selection', command = self._select)
        self.menubar.add_command(label = 'SauceNAO', command = self._sauceNao)
        self.menubar.add_command(label = 'Trash', command = self._trash)
        self.menubar.add_command(label = 'Settings', command = self._showSettings)
        self.menubar.add_command(label = 'Quit', command = self.destroy)

        self.config(menu = self.menubar)

        sframe = widgets.ScrollableFrame(self)
        sframe.pack(fill = tkinter.BOTH)

        self._settings = widgets.SettingFrame(sframe, confirmcommand = self._checkSettings, cancelcommand = self._hideSettings)
        self._frame = tkinter.Frame(sframe)

        self._settingsShown = False
        self._onFrameDelete = None

        if self._settings.autostart:
            self._start()
        else:
            self._showSettings()

        self.mainloop()

    def _showSettings(self):
        if not self._settingsShown:
            self._frame.pack_forget()
            self._settingsShown = True
            self._settings.pack(fill = tkinter.BOTH)

    def _checkSettings(self):
        if not self._settings.sauceNaoDir:
            tkinter.messagebox.showwarning('Warning', 'SauceNao directory not set!')
        elif not self._settings.selectDir:
            tkinter.messagebox.showwarning('Warning', 'Select directory not set!')
        elif not self._settings.trashDir:
            tkinter.messagebox.showwarning('Warning', 'Trash directory not set!')
        elif not self._settings.destDir:
            tkinter.messagebox.showwarning('Warning', 'Dest directory not set!')
        else:
            self._hideSettings()
            return True

        return False

    def _hideSettings(self):
        if self._settingsShown:
            self._settings.pack_forget()
            self._settingsShown = False
            self._frame.pack()
            self._start()

    def _start(self):
        self._start = lambda: None
        self._index()

    def _setFrame(self, func, *args, **kwargs): # enter, exit callbacks and select / saucenao in menu
        master = self._frame.master

        if self._onFrameDelete:
            self._onFrameDelete()
            self._onFrameDelete = None

        self._frame.destroy()
        self._frame = func(master, *args, **kwargs)

        if not self._settingsShown:
            self._frame.pack(fill = tkinter.BOTH)

        return self._frame

    def _index(self):
        self._setFrame(widgets.IndexFrame, command = self._select)

    def _select(self):
        frame = self._setFrame(widgets.SelectFrame, command = self._sauceNao)

        self.bind('<Delete>',  lambda event: frame._deleteAll())
        self.bind('<Left>',    lambda event: frame.showNext())
        self.bind('<Right>',   lambda event: frame._onNext())

        def unbind():
            self.unbind_all('<Delete>')
            self.unbind_all('<Left>')
            self.unbind_all('<Right>')

        self._onFrameDelete = unbind

    def _sauceNao(self):
        self._setFrame(widgets.SauceNaoFrame, command = self._done)

    def _done(self):
        frame = self._setFrame(tkinter.Frame)

        tkinter.Label(frame, 'Done').pack()

    def _trash(self):
        self._setFrame(widgets.TrashFrame, command = self._select)

if __name__ == '__main__':
    Application()