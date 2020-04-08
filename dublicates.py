import widgets
import tkinter

class Application(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.wait_visibility()

        self.attributes('-fullscreen', True)
        self.title('Dublicate finder')

        self.menubar = tkinter.Menu(self)
        self.menubar.add_command(label = 'Indexing', command = self._clickedFrame(self._index))
        self.menubar.add_command(label = 'Selection', command = self._clickedFrame(self._select))
        self.menubar.add_command(label = 'SauceNAO', command = self._clickedFrame(self._sauceNao))
        self.menubar.add_command(label = 'Trash', command = self._clickedFrame(self._trash))
        self.menubar.add_command(label = 'Settings', command = self._showSettings)
        self.menubar.add_command(label = 'Quit', command = self.destroy)

        self.config(menu = self.menubar)

        sframe = widgets.ScrollableFrame(self)
        sframe.pack(expand = True, fill = tkinter.BOTH)

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
        self._sauceNao()

    def _clickedFrame(self, frame):
        def clicked():
            self._hideSettings()
            frame()

        return clicked

    def _setFrame(self, func, *args, **kwargs):
        master = self._frame.master

        self._frame.destroy()
        self._frame = func(master, *args, **kwargs)
        self._frame.pack(expand = True, fill = tkinter.BOTH)

        if self._settingsShown:
            self._frame.pack_forget()

        return self._frame

    def _sauceNao(self):
        self._setFrame(widgets.SauceNaoFrame, command = self._index)

    def _index(self):
        self._setFrame(widgets.IndexFrame, command = self._select)

    def _select(self):
        self._setFrame(widgets.SelectFrame, command = self._trash)

    def _trash(self):
        self._setFrame(widgets.TrashFrame)

if __name__ == '__main__':
    Application()