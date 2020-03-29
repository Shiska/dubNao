import tkinter

class AutoScrollbar(tkinter.Scrollbar):
    # a scrollbar that hides itself if it's not needed.
    # only works if you use the grid geometry manager.
    def set(self, lo, hi):
        try:
            retn = super().set(lo, hi)
        except tkinter.TclError:
            pass
        else:
            if float(lo) <= 0.0 and float(hi) >= 1.0:
                self.grid_remove()
            else:
                self.grid()

            return retn

    def pack(self, **kw):
        raise tkinter.TclError('cannot use pack with this widget')

    def place(self, **kw):
        raise tkinter.TclError('cannot use place with this widget')

class ScrollableFrame(tkinter.Frame):
    def __init__(self, master): # hierarchy: master -> frame -> vscrollbar, hscrollbar, canvas -> self
        frame = tkinter.Frame(master)
        frame.grid_rowconfigure(0, weight = 1)
        frame.grid_columnconfigure(0, weight = 1)

        vscrollbar = AutoScrollbar(frame)
        vscrollbar.grid(row = 0, column = 1, sticky = 'NS')
        hscrollbar = AutoScrollbar(frame, orient = tkinter.HORIZONTAL)
        hscrollbar.grid(row = 1, column = 0, sticky = 'EW')

        canvas = tkinter.Canvas(frame, yscrollcommand = vscrollbar.set, xscrollcommand = hscrollbar.set)
        canvas.grid(row = 0, column = 0, sticky = 'NESW')

        super().__init__(canvas)

        self.bind('<Configure>', lambda event: canvas.config(width = event.width, height = event.height, scrollregion = canvas.bbox('all')))

        vscrollbar.config(command = canvas.yview)
        hscrollbar.config(command = canvas.xview)

        canvas.create_window(0, 0, anchor = tkinter.N, window = self)

        self.grid = frame.grid
        self.pack = frame.pack
        self.place = frame.place

        destroy = self.destroy # destroy itself first otherwise this will result in an infinite loop because frame.destroy would call self.destroy
        self.destroy = lambda: (destroy(), frame.destroy())

if __name__ == "__main__":
    import MediaFrame

    root = tkinter.Tk()

    frame = ScrollableFrame(root)
    frame.pack()

    MediaFrame.MediaFrame(frame, 'dance.gif').pack()
    
    root.mainloop()