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

class Frame(tkinter.Frame):
    def __init__(self, master): # hierarchy: master -> oframe -> vscrollbar, hscrollbar, canvas -> iframe -> self
        oframe = tkinter.Frame(master)
        oframe.grid_rowconfigure(0, weight = 1)
        oframe.grid_columnconfigure(0, weight = 1)

        canvas = tkinter.Canvas(oframe, width = 1, height = 1)
        canvas.grid(row = 0, column = 0, sticky = 'NESW')

        vscrollbar = AutoScrollbar(oframe, command = canvas.yview)
        vscrollbar.grid(row = 0, column = 1, sticky = 'NS')
        hscrollbar = AutoScrollbar(oframe, command = canvas.xview, orient = tkinter.HORIZONTAL)
        hscrollbar.grid(row = 1, column = 0, sticky = 'EW')

        canvas.config(yscrollcommand = vscrollbar.set, xscrollcommand = hscrollbar.set)
        # additional inner frame so the scrollbars are always at the border of the window
        iframe = tkinter.Frame(canvas)

        super().__init__(iframe)

        self.pack(fill = tkinter.BOTH)

        window = canvas.create_window(0, 0, anchor = tkinter.NW, window = iframe)

        def configure(event): # if outer frame size changes
            # expand inner frame to canvas but never smaller then content
            canvas.itemconfig(window, width = max(self.winfo_reqwidth(), event.width), height = max(self.winfo_reqheight(), event.height))

        canvas.bind('<Configure>', configure)

        def configure(event): # if content size changes
            # set canvas size and scrollregion to content size
            width = self.winfo_reqwidth()
            height = self.winfo_reqheight()

            canvas.config(width = width, height = height, scrollregion = (0, 0, width, height))
            # increase inner frame if content size is bigger than canvas
            canvas.itemconfig(window, width = max(width, oframe.winfo_width()), height = max(height, oframe.winfo_height()))

        self.bind('<Configure>', configure)
        # set class pack managers to outer frame managers
        self.grid = oframe.grid
        self.pack = oframe.pack
        self.place = oframe.place
        # fix destroy
        destroy = self.destroy # destroy itself first otherwise this will result in an infinite loop because oframe.destroy would call self.destroy
        self.destroy = lambda: (destroy(), oframe.destroy())

if __name__ == '__main__':
    import widgets.Media as Media
    import widgets.Select as Select

    root = tkinter.Tk()

    frame = Frame(root)
    frame.pack(fill = tkinter.BOTH)

    Media.Frame(frame, next(next(iter(Select.Data))[1]), thumbSize = None).pack()
    
    root.mainloop()