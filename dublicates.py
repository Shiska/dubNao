import gc
import tkinter

import widgets.Index
import widgets.SauceNao
import widgets.Select
import widgets.Scrollable
import widgets.Setting
import widgets.Trash

class Application(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.wait_visibility()

        # self.attributes('-fullscreen', True)
        self.state('zoomed')
        self.title('Dublicate finder')

        self.menubar = tkinter.Menu(self)
        # self.menubar.add_command(label = 'Index', command = self._clickedFrame(self._index))
        self.menubar.add_command(label = 'Select', command = self._clickedFrame(self._select))
        self.menubar.add_command(label = 'SauceNAO', command = self._clickedFrame(self._sauceNao))
        self.menubar.add_command(label = 'Trash', command = self._clickedFrame(self._trash))
        self.menubar.add_command(label = 'Settings', command = self._showSettings)
        # self.menubar.add_command(label = 'Quit', command = self.destroy)

        self.config(menu = self.menubar)

        sframe = widgets.Scrollable.Frame(self)
        sframe.pack(expand = True, fill = tkinter.BOTH)

        self._settingFrame = widgets.Setting.Frame(sframe, confirmcommand = self._checkSettings, cancelcommand = self._hideSettings)
        self._frame = tkinter.Frame(sframe)
        self._settingsShown = False
        self._onFrameDelete = None

        if widgets.Setting.Data.autostart:
            self._start()
        else:
            self._showSettings()

        self.mainloop()

    def _showSettings(self):
        if not self._settingsShown:
            self._frame.pack_forget()
            self._settingsShown = True
            self._settingFrame.pack(fill = tkinter.BOTH)

    def _checkSettings(self):
        if not widgets.Setting.Data.tempDir:
            tkinter.messagebox.showwarning('Warning', 'Temp directory not set!')
        elif not widgets.Setting.Data.destDir:
            tkinter.messagebox.showwarning('Warning', 'Dest directory not set!')
        else:
            self._hideSettings()
            return True

        return False

    def _hideSettings(self):
        if self._settingsShown:
            self._settingFrame.pack_forget()
            self._settingsShown = False
            self._frame.pack()
            self._start()

    def _start(self):
        self._start = lambda: None
        self._setFrame(widgets.SauceNao.Frame, command = self._index)

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

    def _sauceNao(self):
        self._setFrame(widgets.SauceNao.Frame, browse = self._index)

    def _index(self):
        self._setFrame(widgets.Index.Frame, command = self._select)

    def _select(self):
        self._setFrame(widgets.Select.Frame, command = self._trash)

    def _trash(self):
        self._setFrame(widgets.Trash.Frame)

if __name__ == '__main__':
    Application()