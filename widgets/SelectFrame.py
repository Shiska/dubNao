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
    thumbnailSize = 300
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
        self._diffFrame = False

        self._imageMap = imageMap
        self._items = dict(items)
        self._dest = pathlib.Path(dest).absolute() if dest else None

        keyFrame = tkinter.LabelFrame(self)
        keyFrame.pack(expand = True, fill = tkinter.Y)

        self._frame = tkinter.Frame(keyFrame)

        frame = tkinter.Frame(self)
        frame.pack()
        
        tkinter.Button(frame, text = 'Next', command = self._onNext).grid(row = 0, column = 0)
        tkinter.Button(frame, text = 'Skip', command = self.showNext).grid(row = 0, column = 1)

        self._vButtonsFrame = tkinter.Frame(frame)
        self._vButtonsFrame.grid(row = 0, column = 2)

        tkinter.Button(self._vButtonsFrame, text = 'Start', command = self._startAll).grid(row = 0, column = 0)
        tkinter.Button(self._vButtonsFrame, text = 'Stop', command = self._stopAll).grid(row = 0, column = 1)
        tkinter.Button(self._vButtonsFrame, text = 'Reset', command = self._resetAll).grid(row = 0, column = 2)

        self._menu = tkinter.Menu(self, tearoff = 0)
        self._menu.add_command(label = 'Start', command = lambda: self._menu._mframe.play())
        self._menu.add_command(label = 'Stop', command = lambda: self._menu._mframe.stop())
        self._menu.add_command(label = 'Reset', command = lambda: self._menu._mframe.reset())

        tkinter.Button(frame, text = 'Difference', command = self._onDiff).grid(row = 0, column = 3)
        tkinter.Button(frame, text = 'Delete', command = self._deleteAll).grid(row = 0, column = 4)

        self.showNext()

    def _newFrame(self, text: str):
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

    @classmethod
    def getFileData(cls, files) -> dict:
        data = dict()

        data['file'] = list(map(pathlib.Path, files))
        data['image'] = list(map(PIL.Image.open, data['file']))
        data['thumbnail'] = [i.convert('RGB') for i in data['image']]

        size = (cls.thumbnailSize, cls.thumbnailSize)

        [t.thumbnail(size) for t in data['thumbnail']]

        data['size'] = [i.size for i in data['image']]
        data['filesize'] = [f.stat().st_size for f in data['file']]

        if len(data['thumbnail']):
            firstThumbnail = data['thumbnail'][0]

            data['difference'] = [cls.getDifference(firstThumbnail, t)[1] for t in data['thumbnail']]
        else:
            data['difference'] = []
        
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
        for rframe in self._frame.grid_slaves():
            for cframe in rframe.grid_slaves():
                mediaLabel = cframe.grid_slaves(row = 0)[0]

                yield mediaLabel, mediaLabel.grid_slaves()[0]

    def _setDiffImages(self, frame):
        thumbnail = frame.thumbnail

        for mediaLabel, mediaFrame in self.iterImages():
            (diffImage, difference) = self.getDifference(thumbnail, mediaFrame.thumbnail)

            mediaFrame['image'] = mediaFrame.diff = PIL.ImageTk.PhotoImage(diffImage)
            mediaLabel['text'] = 'Difference: ' + str(difference)

    def _onEnterImage(self, frame):
        def enter(event):
            if self._diffFrame:
                self._diffFrame = frame
                self._setDiffImages(frame)

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
            data = self.getFileData(self._imageMap[key])
            ranking = self.groupData(data)
            selected = self._preselectCheckbox(data)
            frame = self._newFrame(key + ' (' + str(remaining - 1) + ' remaining)')

            for idx, file in enumerate(data['file']):
                column = idx % self.maxImagesPerRow
            
                if column == 0:
                    rframe = tkinter.LabelFrame(frame, text = 'hi')
                    rframe.grid(row = (idx // self.maxImagesPerRow), column = 0, sticky = 'nesw')

                cframe = tkinter.Frame(rframe)
                cframe.grid(row = 0, column = column, padx = 1, pady = 1)

                var = tkinter.BooleanVar()
                var.set(selected == None or selected == idx)
                
                lframe = tkinter.LabelFrame(cframe, text = 'Difference: ' + str(data['difference'][idx]))
                lframe.columnconfigure(0, minsize = self.thumbnailSize + 10)
                lframe.rowconfigure(0, minsize = self.thumbnailSize + 10)
                lframe.grid()

                mframe = MediaFrame(lframe, str(file), (self.thumbnailSize, self.thumbnailSize), onFrameChange = self._onFrameChange)
                mframe._file = file
                mframe._var = var
                mframe.grid()

                def openFile(file):
                    def event(e):
                        self.openFile(file)

                    return event

                mframe.bind('<Button-1>', openFile(file))
                mframe.bind('<Enter>', self._onEnterImage(mframe))

                if mframe.isVideo:
                    mframe.bind('<Button-3>', self._popup(mframe))

                    isThereAnyVideo = True

                hframe = tkinter.Frame(cframe)
                hframe.grid()

                wrap = self.thumbnailSize * 3 // 4

                tkinter.Checkbutton(hframe, text = str(file.name), variable = var, wraplength = wrap, fg = self._getColor(ranking['name'][idx])).grid(row = 0, column = 1, sticky = 'w')

                tkinter.Label(hframe, text = 'Directory:').grid(row = 1, column = 0, sticky = 'e')
                tkinter.Label(hframe, text = 'Size:').grid(row = 2, column = 0, sticky = 'e')
                tkinter.Label(hframe, text = 'Filesize:').grid(row = 3, column = 0, sticky = 'e')

                tkinter.Label(hframe, text = str(file.parent), wraplength = wrap, fg = self._getColor(ranking['dir'][idx])).grid(row = 1, column = 1, sticky = 'w')
                tkinter.Label(hframe, text = '{} x {}'.format(*data['size'][idx]), wraplength = wrap, fg = self._getColor(ranking['size'][idx])).grid(row = 2, column = 1, sticky = 'w')
                tkinter.Label(hframe, text = hurry.filesize.size(data['filesize'][idx]), wraplength = wrap, fg = self._getColor(ranking['filesize'][idx])).grid(row = 3, column = 1, sticky = 'w')

            if isThereAnyVideo:
                self._vButtonsFrame.grid()
            else:
                self._vButtonsFrame.grid_remove()

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