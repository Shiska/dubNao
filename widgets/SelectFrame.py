import os
import pathlib
import tkinter
import platform
import subprocess
import hurry.filesize

import PIL.Image
import PIL.ImageTk
import PIL.ImageChops

from MediaFrame import MediaFrame

class SelectFrame(tkinter.Frame): #todo get frames after images were created, instead of getting the thumbnail twice!
    thumbnailSize = 300 # maybe: move all 'selected' files into a 'select' folder to speed up indexing
    maxImagesPerRow = 6

    colors = dict(enumerate([
        'green',
        'red',
        'blue',
        'violet',
        'orange',
    ]))

    def __init__(self, master, imageMap, items: dict, dest: str = None, command = None):
        super().__init__(master)

        self.command = command

        self._imageMap = imageMap
        self._items = dict(items)
        self._dest = pathlib.Path(dest).absolute() if dest else None

        frame = tkinter.Frame(self)
        frame.grid()

        tkinter.Button(frame, text = 'Next', command = self._onNext).grid(row = 0, column = 0)
        tkinter.Button(frame, text = 'Skip', command = self.showNext).grid(row = 0, column = 1)
        tkinter.Button(frame, text = 'Difference', command = self._onDiff).grid(row = 0, column = 2)
        tkinter.Button(frame, text = 'Delete', command = self._deleteAll).grid(row = 0, column = 3)

        self._vButtonsFrame = tkinter.Frame(self)
        self._vButtonsFrame.grid()

        tkinter.Button(self._vButtonsFrame, text = 'Start', command = self._startAll).grid(row = 0, column = 0)
        tkinter.Button(self._vButtonsFrame, text = 'Stop', command = self._stopAll).grid(row = 0, column = 1)
        tkinter.Button(self._vButtonsFrame, text = 'Reset', command = self._resetAll).grid(row = 0, column = 2)

        self._menu = tkinter.Menu(self, tearoff = 0)
        self._menu.add_command(label = 'Start', command = lambda: self._menu._mframe.play())
        self._menu.add_command(label = 'Stop', command = lambda: self._menu._mframe.stop())
        self._menu.add_command(label = 'Reset', command = lambda: self._menu._mframe.reset())

        keyFrame = tkinter.LabelFrame(self)
        keyFrame.grid()

        self._frame = tkinter.Frame(keyFrame)

        self.showNext()

    def _newFrame(self, text: str):
        self._inFrame = self._diffFrame = None

        master = self._frame.master

        master['text'] = text

        self._frame.destroy()
        self._frame = tkinter.Frame(master)
        self._frame.pack(expand = True, fill = tkinter.BOTH)

        return self._frame

    @staticmethod
    def openFile(filepath: str):
        if platform.system() == 'Darwin':
            subprocess.call(('open', filepath))
        elif platform.system() == 'Windows':
            os.startfile(filepath)
        else: # linux
            subprocess.call(('xdg-open', filepath))

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
        
        if max(data['difference']) < 32: # preselect best picture if highest difference is small
            maxsize = max(data['size'])
            victims = [idx for idx, size in enumerate(data['size']) if size == maxsize]

            if len(victims) > 1:
                sizes = [data['filesize'][idx] for idx in victims]
                maxsize = max(sizes)
                victims = [victims[idx] for idx, size in enumerate(sizes) if size == maxsize]

                if len(victims) > 1 and self._dest:
                    newvictims = [idx for idx in victims if data['file'][idx].parent == self._dest]

                    if len(newvictims): # if 0 all are in search path so use old victims
                        victims = newvictims

            selectIdx = victims[0]

        return selectIdx

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
            sortByLen = sorted([x[1] for x in sortByValue], key = len, reverse = True)
            ranking[key] = {i: pos for pos, indices in enumerate(sortByLen) for i in indices}

        return ranking

    @classmethod
    def _getColor(cls, idx: int):
        return cls.colors.get(idx, 'black')

    def iterImages(self):
        (columns, _) = self._frame.grid_size()

        for c in range(columns):
            mediaLabel = self._frame.grid_slaves(row = 2, column = c)[0]

            yield mediaLabel, mediaLabel.grid_slaves()[0]

    def _resizeImage(self, image):
        if image.width > image.height:
            return image.resize((self.thumbnailSize, self.thumbnailSize * image.height // image.width))

        return image.resize((self.thumbnailSize * image.width // image.height, self.thumbnailSize))

    def _setDiffImages(self, frame):
        thumbnail = self._resizeImage(frame._image)

        for mediaLabel, mediaFrame in self.iterImages():
            (diffImage, difference) = self.getDifference(thumbnail, self._resizeImage(mediaFrame._image))

            mediaFrame['image'] = mediaFrame.diff = PIL.ImageTk.PhotoImage(diffImage)
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

    def _onDiff(self):
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
                (diffImage, difference) = self.getDifference(self._diffFrame.thumbnail, thumbnail)

                mframe['image'] = mframe.diff = PIL.ImageTk.PhotoImage(diffImage)
                mframe.master['text'] = 'Difference: ' + str(difference)
        elif self._inFrame:
            image = self._inFrame._image.copy()
            image.thumbnail((image.width, self.winfo_screenheight() * 3 // 4))

            self._inFrame._setPhoto(image)

    def _onLeaveImage(self, event):
        def leave():
            if self._inFrame:
                self._inFrame._setPhoto(self._inFrame.thumbnail)
                self._inFrame = None

        # self.after_idle(leave)

    def _popup(self, mframe):
        def popup(event):
            self._menu._mframe = mframe
            self._menu.post(event.x_root, event.y_root)

        return popup

    def _startAll(self):
        for _, mediaFrame in self.iterImages():
            self.after_idle(mediaFrame.play)

    def _stopAll(self):
        for _, mediaFrame in self.iterImages():
            self.after_idle(mediaFrame.stop)

    def _resetAll(self):
        for _, mediaFrame in self.iterImages():
            self.after_idle(mediaFrame.reset)

    def _deleteAll(self):
        files = [mediaFrame._file for _, mediaFrame in self.iterImages()]

        self._newFrame('') # remove access from images

        all(map(self._imageMap.moveFileToTrash, files))

        self._imageMap.store()
        self.showNext()

    def _onNext(self):
        files = [(mediaFrame._var.get(), mediaFrame._file) for _, mediaFrame in self.iterImages()]

        self._newFrame('') # remove access from images

        for checkbox, file in files:
            if checkbox:
                if self._dest and str(file) in self._files: # move only files from the original items
                    self._imageMap.moveFileTo(file, self._dest)
            else:
                self._imageMap.moveFileToTrash(file)

        self._imageMap.store()
        self.showNext()

    def showNext(self):
        remaining = len(self._items)

        if remaining == 0:
            if self.command:
                self.command()
        else:
            (key, self._files) = self._items.popitem()

            isThereAnyVideo = False
            wrap = self.thumbnailSize * 3 // 4
            frame = self._newFrame(key + ' (' + str(remaining - 1) + ' remaining)')

            for idx, file in enumerate(map(pathlib.Path, self._imageMap[key])):
                lframe = tkinter.LabelFrame(frame)
                lframe.columnconfigure(0, minsize = self.thumbnailSize + 10)
                lframe.rowconfigure(0, minsize = self.thumbnailSize + 10)
                lframe.grid(row = 2, column = idx)

                mframe = MediaFrame(lframe, str(file), (self.thumbnailSize, self.thumbnailSize), onFrameChange = self._onFrameChange)
                mframe._var = tkinter.BooleanVar()
                mframe._column = idx
                mframe._file = file
                mframe.grid()

                def openFile(file):
                    def event(e):
                        self.openFile(file)

                    return event

                mframe.bind('<Button-1>', openFile(file))
                mframe.bind('<Enter>', self._onEnterImage(mframe))

                # mframe.bind('<Leave>', self._onLeaveImage)

                if mframe.isVideo:
                    mframe.bind('<Button-3>', self._popup(mframe))

                    isThereAnyVideo = True

            if isThereAnyVideo:
                self._vButtonsFrame.grid()
            else:
                self._vButtonsFrame.grid_remove()

            self._onDiff()
            self._onDiff()

            data = self.getFileData()
            ranking = self.groupData(data)
            selected = self._preselectCheckbox(data)

            for mediaFrame in data['frame']:
                idx = mediaFrame._column
                file = mediaFrame._file
                var = mediaFrame._var

                var.set(selected == None or selected == idx)

                tkinter.Checkbutton(frame, text = str(file.name), variable = var, fg = self._getColor(ranking['name'][idx])).grid(row = 0, column = idx)

                hframe = tkinter.Frame(frame)
                hframe.grid(row = 1, column = idx)

                tkinter.Label(hframe, text = 'Directory:').grid(row = 1, column = 0, sticky = 'e')
                tkinter.Label(hframe, text = 'Size:').grid(row = 2, column = 0, sticky = 'e')
                tkinter.Label(hframe, text = 'Filesize:').grid(row = 3, column = 0, sticky = 'e')

                tkinter.Label(hframe, text = str(file.parent), wraplength = wrap, fg = self._getColor(ranking['dir'][idx])).grid(row = 1, column = 1, sticky = 'w')
                tkinter.Label(hframe, text = '{} x {}'.format(*data['size'][idx]), wraplength = wrap, fg = self._getColor(ranking['size'][idx])).grid(row = 2, column = 1, sticky = 'w')
                tkinter.Label(hframe, text = str(data['filesize'][idx]), wraplength = wrap, fg = self._getColor(ranking['filesize'][idx])).grid(row = 3, column = 1, sticky = 'w')

            self._onEnterImage(data['frame'][[key for key, value in ranking['size'].items() if value == 0][0]])(None)

if __name__ == '__main__':
    from IndexFrame import ImageMap

    root = tkinter.Tk()
    root.wait_visibility()

    imageMap = ImageMap()

    from ScrollableFrame import ScrollableFrame
    
    frame = ScrollableFrame(root)
    frame.pack(expand = True, fill = tkinter.BOTH)

    SelectFrame(frame, imageMap, {k: v for k, v in imageMap}, 'dest', command = root.destroy).pack()

    root.mainloop()