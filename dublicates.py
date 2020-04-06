import widgets
import tkinter

class Application(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.wait_visibility()

        self.attributes("-fullscreen", True)
        self.title('Dublicate finder')

        self.menubar = tkinter.Menu(self)
        self.menubar.add_command(label = 'Settings', command = self._showSettings)
        self.menubar.add_command(label = 'Quit', command = self.destroy)

        self.config(menu = self.menubar)

        sframe = widgets.ScrollableFrame(self)
        sframe.pack(fill = tkinter.BOTH)

        self._settings = widgets.SettingFrame(sframe, confirmcommand = self._checkSettings, cancelcommand = self._hideSettings)
        self._frame = tkinter.Frame(sframe)
        self._settingsShown = False

        if self._settings.autostart:
            self._index()
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
            self._index()

    def _setFrame(self, func, *args, **kwargs):
        master = self._frame.master

        self._frame.destroy()
        self._frame = func(master, *args, **kwargs)

        if not self._settingsShown:
            self._frame.pack(fill = tkinter.BOTH)

        return self._frame

    def _index(self):
        self._index = lambda: None
        self._setFrame(widgets.IndexFrame, command = self._select)

    def _select(self):
        frame = self._setFrame(widgets.SelectFrame, command = self._sauceNao)

        self.bind('<Delete>',  lambda event: frame._deleteAll())
        self.bind('<Left>',    lambda event: frame.showNext())
        self.bind('<Right>',   lambda event: frame._onNext())

    def _sauceNao(self):
        self.unbind_all('<Delete>')
        self.unbind_all('<Left>')
        self.unbind_all('<Right>')

        self._setFrame(widgets.SauceNaoFrame)

if __name__ == '__main__':
    Application()