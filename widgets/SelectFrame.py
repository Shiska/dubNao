import pathlib
import tkinter
import collections

import PIL.ImageTk
import PIL.ImageChops

if '.' in __name__:
    from .MediaFrame import MediaFrame
    from .IndexFrame import IndexFrame
    from .SettingFrame import SettingFrame
else:
    from MediaFrame import MediaFrame
    from IndexFrame import IndexFrame
    from SettingFrame import SettingFrame

class SelectFrame(tkinter.Frame):
    thumbnailSize = 300
    maxImagesPerRow = 6

    colors = dict(enumerate([
        'green',
        'red',
        'blue',
        'violet',
        'orange',
    ]))

    def __init__(self, master, command = None):
        super().__init__(master)

        self.command = command

        self._after = None
        self._imageMap =  IndexFrame.imageMap
        self._destDir = pathlib.Path(SettingFrame.destDir)
        self._selectDir = pathlib.Path(SettingFrame.selectDir)
        self._sauceNaoDir = pathlib.Path(SettingFrame.sauceNaoDir)

        self.focus_set()
        self.after_idle(self._initMove)

    def _initMove(self): # copied from indexFrame
        selectDirs = set(map(pathlib.Path, SettingFrame.selectDirs))

        self._items = [(key, v) for key, value in self._imageMap for v in map(pathlib.Path, value) if any(p in selectDirs for p in v.parents)]

        oframe = tkinter.Frame(self)
        oframe.pack()

        frame = tkinter.LabelFrame(oframe, text = 'Moving files')
        frame.grid_columnconfigure(1, weight = 1)
        frame.grid(sticky = 'ew')

        tkinter.Label(frame, text = 'Key:').grid(row = 0, column = 0, sticky = 'e')
        tkinter.Label(frame, text = 'File:').grid(row = 1, column = 0, sticky = 'e')

        keyLabel = tkinter.Label(frame)
        keyLabel.grid(row = 0, column = 1, sticky = 'w')
        fileLabel = tkinter.Label(frame)
        fileLabel.grid(row = 1, column = 1, sticky = 'w')

        frame.bind('<Configure>', lambda event: oframe.grid_columnconfigure(0, minsize = event.width)) # increase minsize so it doesn't resize constantly

        ignoreDirs = (self._sauceNaoDir, self._selectDir, pathlib.Path(SettingFrame.trashDir), self._destDir)

        def moveFiles():
            if len(self._items):
                (key, file) = self._items.pop()

                keyLabel['text'] = key
                fileLabel['text'] = ''

                parents = file.parents

                if all(p not in ignoreDirs for p in parents):
                    with PIL.Image.open(file) as image:
                        pass # just open and close it again, data stays in image object

                    if image.width > 200 or image.height > 200:
                        fileLabel['text'] = str(file)

                        self._imageMap.moveFileTo(file, self._selectDir)
                    else: # delete small files
                        self._imageMap.delete(file, key)

                        file.unlink()

                self.after_idle(moveFiles)
            else:
                oframe.destroy()

                self._imageMap.store()
                self._initSelect()

        self.after_idle(moveFiles)

    def _initSelect(self):
        # todo check imageMap for deleted files
        if SettingFrame.duplicates:
            self._items = ((key, value) for key, value in self._imageMap if len(value) > 1 or self._selectDir in pathlib.Path(value[0]).parents)
        else:
            self._items = ((key, v) for key, value in self._imageMap for v in ({v for v in value if self._selectDir in pathlib.Path(v).parents}, ) if len(v))

        oframe = tkinter.LabelFrame(self, text = 'Selection')
        oframe.pack()

        self.bind('<Left>',     self.reset)
        self.bind('<Up>',       self.difference)
        self.bind('<Down>',     self.delete)
        self.bind('<Right>',    self.next)
        self.bind('<space>',    self.toggle)

        frame = tkinter.Frame(oframe)
        frame.pack(expand = True, fill = tkinter.X)

        self._nextButton = tkinter.Button(frame, command = self.next)
        self._nextButton._text = self._nextButton['text'] = 'Next (Right)'
        self._nextButton.pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)

        tkinter.Button(frame, text = 'Difference (Up)', command = self.difference).pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)
        tkinter.Button(frame, text = 'Delete (Down)', command = self.delete).pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)
        tkinter.Button(frame, text = 'Uncheck All', command = self.uncheck).pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)

        self._vButtonsFrame = tkinter.Frame(oframe)
        self._vButtonsFrame.pack(expand = True, fill = tkinter.X)

        tkinter.Button(self._vButtonsFrame, text = 'Start (Space)', command = self.start).pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)
        tkinter.Button(self._vButtonsFrame, text = 'Stop (Space)', command = self.stop).pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)
        tkinter.Button(self._vButtonsFrame, text = 'Reset (Left)', command = self.reset).pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)

        self._menu = tkinter.Menu(self, tearoff = 0)
        self._menu.add_command(label = 'Start', command = lambda: self._menu._mframe.play())
        self._menu.add_command(label = 'Stop', command = lambda: self._menu._mframe.stop())
        self._menu.add_command(label = 'Reset', command = lambda: self._menu._mframe.reset())

        keyFrame = tkinter.LabelFrame(oframe)
        keyFrame.pack()

        self._frame = tkinter.Frame(keyFrame)

        self.skip()

    def _newFrame(self, text: str = ''):
        self._inFrame = self._diffFrame = None

        master = self._frame.master

        master['text'] = text

        self._frame.destroy()
        self._frame = tkinter.Frame(master)

        self._stopAutoselect()

        return self._frame

    @staticmethod
    def getDifference(image1, image2) -> tuple:
        diffImage = PIL.ImageChops.difference(image1, image2)

        return (diffImage, max(d for data in diffImage.getdata() for d in data))

    def getFileData(self) -> dict:
        data = dict()

        data['frame'] = frames = [mediaFrame for _, mediaFrame in self.iterImages()]
        data['file'] = [f._file for f in frames]
        data['size'] = [f._image.size for f in frames]
        data['filesize'] = [f.stat().st_size for f in data['file']]
        data['difference'] = [f._difference for f in frames]

        return data

    def _preselectCheckbox(self, data):
        selectIdx = None
        maxdiff = max(data['difference'])

        if maxdiff < 32: # preselect best picture if highest difference is small
            maxsize = max(data['size'])
            victims = [idx for idx, size in enumerate(data['size']) if size == maxsize]

            if len(victims) > 1:
                sizes = [data['filesize'][idx] for idx in victims]
                maxsize = max(sizes)
                victims = [victims[idx] for idx, size in enumerate(sizes) if size == maxsize]

                if len(victims) > 1:
                    newvictims = [idx for idx in victims if data['file'][idx].parent != self._selectDir]

                    if len(newvictims):
                        victims = newvictims

                        if maxdiff == 0:
                            self._autoselect(SettingFrame.autoselect)

            selectIdx = victims[0]

        return selectIdx

    def _autoselect(self, seconds):
        if seconds == 0:
            self._stopAutoselect()
            self.after_idle(self.next)
        else:
            self._nextButton['text'] = 'Autoselect in ' + str(seconds) + ' seconds (Right)'
            self._after = self.after(1000, lambda: self._autoselect(seconds - 1))

    def _stopAutoselect(self):
        if self._after:
            self._nextButton['text'] = self._nextButton._text
            self.after_cancel(self._after)
            self._after = None
            return True

        return False

    @staticmethod
    def groupData(data):
        ranking = {}

        items = dict()

        items['name'] = [f.name for f in data['file']]
        items['dir'] = [f.parent for f in data['file']]
        items['size'] = data['size']
        items['filesize'] = data['filesize']

        for key, value in items.items():
            enum = list(enumerate(value))
            groups = {v1: [idx for idx, v2 in enum if v1 == v2] for v1 in value}
            sortByValue = sorted(groups.items(), key = lambda x: x[0], reverse = True)
            # sortByLen = sorted([x[1] for x in sortByValue], key = len, reverse = True)
            ranking[key] = {i: pos for pos, indices in enumerate(sortByValue) for i in indices[1]}

        return ranking

    @classmethod
    def _getColor(cls, idx: int):
        return cls.colors.get(idx, 'black')

    def iterImages(self):
        for mediaLabel in self._frame.grid_slaves():
            if isinstance(mediaLabel, tkinter.LabelFrame):
                yield mediaLabel, mediaLabel.grid_slaves()[0]

    def _resizeImage(self, image):
        if image.width > image.height:
            return image.resize((self.thumbnailSize, self.thumbnailSize * image.height // image.width))

        return image.resize((self.thumbnailSize * image.width // image.height, self.thumbnailSize))

    def _setDiffImages(self, frame):
        thumbnail = self._resizeImage(frame._image)

        for mediaLabel, mediaFrame in self.iterImages():
            (diffImage, difference) = self.getDifference(thumbnail, self._resizeImage(mediaFrame._image))

            mediaFrame['image'] = mediaFrame.diff = PIL.ImageTk.PhotoImage(diffImage.convert('RGB'))
            mediaLabel['text'] = 'Difference: ' + str(difference)
            mediaFrame._difference = difference

    def _onEnterImage(self, frame):
        def enter(event):
            if self._diffFrame:
                self._diffFrame = frame
                self._setDiffImages(frame)
            else:
                if self._inFrame:
                    self._inFrame._setPhoto(self._inFrame._thumbnail)

                self._inFrame = frame

                image = frame._image.copy()
                image.thumbnail((image.width, self.winfo_screenheight() * 3 // 4))

                frame._setPhoto(image)

        return enter

    def difference(self, event = None):
        if self._diffFrame:
            self._diffFrame = None

            for _, mediaFrame in self.iterImages():
                mediaFrame['image'] = mediaFrame.photo
        else:
            self._diffFrame = next(self.iterImages())[1]
            self._setDiffImages(self._diffFrame)

    def _onFrameChange(self, mframe, thumbnail):
        if self._diffFrame:
            if self._diffFrame == mframe:
                self._setDiffImages(mframe)
            else:
                (diffImage, difference) = self.getDifference(self._diffFrame._thumbnail, thumbnail)

                mframe['image'] = mframe.diff = PIL.ImageTk.PhotoImage(diffImage)
                mframe.master['text'] = 'Difference: ' + str(difference)
        elif self._inFrame == mframe:
            image = self._inFrame._image.copy()
            image.thumbnail((image.width, self.winfo_screenheight() * 3 // 4))

            self._inFrame._setPhoto(image)

    def _popup(self, mframe):
        def popup(event):
            self._menu._mframe = mframe
            self._menu.post(event.x_root, event.y_root)

        return popup

    def start(self, event = None):
        self._videosPlaying = True

        for _, mediaFrame in self.iterImages():
            self.after_idle(mediaFrame.play)

    def stop(self, event = None):
        self._videosPlaying = False

        for _, mediaFrame in self.iterImages():
            self.after_idle(mediaFrame.stop)

    def toggle(self, event = None):
        if self._videosPlaying:
            self.stop()
        else:
            self.start()

    def reset(self, event = None):
        for _, mediaFrame in self.iterImages():
            self.after_idle(mediaFrame.reset)

    def delete(self, event = None):
        for _, mediaFrame in self.iterImages():
            mediaFrame.release()

            self._imageMap.moveFileToTrash(mediaFrame._file)

        self._imageMap.store()
        self.skip()

    def uncheck(self, event = None):
        for _, mediaFrame in self.iterImages():
            mediaFrame._var.set(False);

    def next(self, event = None):
        if self._after:
            self._stopAutoselect()
        else:
            for _, mediaFrame in self.iterImages():
                mediaFrame.release()
                file = mediaFrame._file

                if mediaFrame._var.get():
                    if str(file) in self._files: # move only files from the original items
                        self._imageMap.moveFileTo(file, self._sauceNaoDir)
                else:
                    self._imageMap.moveFileToTrash(file)

            self._imageMap.store()
            self.skip()

    def skip(self, event = None):
        (key, self._files) = next(self._items, (None, None))

        if key:
            isThereAnyVideo = False
            frame = self._newFrame(key)
            wrap = self.thumbnailSize * 3 // 4

            for idx, file in enumerate(map(pathlib.Path, self._imageMap[key])):
                lframe = tkinter.LabelFrame(frame)
                lframe.columnconfigure(0, minsize = self.thumbnailSize + 10)
                lframe.rowconfigure(0, minsize = self.thumbnailSize + 10)
                lframe.grid()

                mframe = MediaFrame(lframe, str(file), (self.thumbnailSize, self.thumbnailSize), onFrameChange = self._onFrameChange)
                mframe._var = tkinter.BooleanVar()
                mframe._file = file
                mframe.grid()

                def openFile(frame):
                    def event(e):
                        frame.osOpen()

                    return event

                mframe.bind('<Button-1>', openFile(mframe))
                mframe.bind('<Enter>', self._onEnterImage(mframe))

                if mframe.isVideo:
                    mframe.bind('<Button-3>', self._popup(mframe))

                    isThereAnyVideo = True

            self._videosPlaying = True

            if isThereAnyVideo:
                self._vButtonsFrame.pack()
            else:
                self._vButtonsFrame.pack_forget()
            # to calculate difference value and hide it again
            self.difference()
            self.difference()

            data = self.getFileData()
            ranking = self.groupData(data)
            selected = self._preselectCheckbox(data)

            rows = collections.defaultdict(int)
            length = len(data['frame'])
            step = 128 // length
            # sort columns by size
            columns = {item[0]: idx for idx, item in enumerate(sorted(ranking['size'].items(), key = lambda i: i[1]))}

            for idx, mediaFrame in enumerate(data['frame']):
                column = columns[idx]

                file = mediaFrame._file
                var = mediaFrame._var

                var.set(selected == None or selected == idx)

                rank = ranking['name'][idx]
                tkinter.Checkbutton(frame, text = '{} ({})'.format(file.name, rank), variable = var, fg = '#{:02X}{:02X}00'.format(rank * step, 128 - rank * step)).grid(row = 0, column = column)

                hframe = tkinter.Frame(frame)
                hframe.grid(row = 1, column = column)

                tkinter.Label(hframe, text = 'Directory:').grid(row = 1, column = 0, sticky = 'e')
                tkinter.Label(hframe, text = 'Size:').grid(row = 2, column = 0, sticky = 'e')
                tkinter.Label(hframe, text = 'Filesize:').grid(row = 3, column = 0, sticky = 'e')

                rank = ranking['dir'][idx]
                tkinter.Label(hframe, text = '{} ({})'.format(file.parent, rank), wraplength = wrap, fg = '#{:02X}{:02X}00'.format(rank * step, 128 - rank * step)).grid(row = 1, column = 1, sticky = 'w')
                rank = ranking['size'][idx]
                tkinter.Label(hframe, text = '{} x {} ({})'.format(*data['size'][idx], rank), wraplength = wrap, fg = '#{:02X}{:02X}00'.format(rank * step, 128 - rank * step)).grid(row = 2, column = 1, sticky = 'w')
                rank = ranking['filesize'][idx]
                tkinter.Label(hframe, text = '{} ({})'.format(data['filesize'][idx], rank), wraplength = wrap, fg = '#{:02X}{:02X}00'.format(rank * step, 128 - rank * step)).grid(row = 3, column = 1, sticky = 'w')

                mediaFrame.master.grid(row = 2, column = column)

            self._onEnterImage(data['frame'][[idx for idx, column in columns.items() if column == 0][0]])(None)

            frame.pack(fill = tkinter.BOTH)
        else:
            if self.command:
                self.command()

if __name__ == '__main__':
    from ScrollableFrame import ScrollableFrame

    root = tkinter.Tk()
    root.state('zoomed')
    root.wait_visibility()

    frame = ScrollableFrame(root)
    frame.pack(expand = True, fill = tkinter.BOTH)

    SelectFrame(frame, command = lambda: root.after_idle(root.destroy)).pack(expand = True, fill = tkinter.BOTH)

    root.mainloop()