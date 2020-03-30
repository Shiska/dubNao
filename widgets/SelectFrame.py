import os
import pathlib
import tkinter
import platform
import subprocess

import PIL.Image
import PIL.ImageTk
import PIL.ImageChops

from MediaFrame import MediaFrame

class SelectFrame(tkinter.Frame):
    thumbnailSize = 300
    maxImagesPerRow = 6

    colors = [
        'green',
        'red',
        'blue',
        'violet',
        'orange',
    ]

    def __init__(self, master, imageMap: dict, dest: str, *src: str, command = None):
        super().__init__(master)

        self.command = command

        src = list(map(pathlib.Path, src))

        self._items = {key: value for key, value in imageMap.items() for v in value if any(p in src for p in pathlib.Path(v).parents)}
        self._dest = pathlib.Path(dest)

        self._keyFrame = tkinter.LabelFrame(self)
        self._keyFrame.pack()

        self._frame = tkinter.Frame(self._keyFrame)
        
        tkinter.Button(self, text = 'Next', command = None).pack()

        self.showNext()

    def _newFrame(self, text: str):
        self._keyFrame['text'] = text

        self._frame.destroy()
        self._frame = tkinter.Frame(self._keyFrame)
        self._frame.pack()

        return self._frame

    @staticmethod
    def openFile(filepath: str):
        if platform.system() == 'Darwin':
            subprocess.call(('open', filepath))
        elif platform.system() == 'Windows':
            os.startfile(filepath)
        else: # linux
            subprocess.call(('xdg-open', filepath))

    # @staticmethod
    # def getThumbnail(file: str, size = None):
        # image = PIL.Image.open(file)

        # thumbnail = image.copy()
        # thumbnail.thumbnail(size if size or self.thumbnailSize)
            
        # # img = im.resize(size).convert('RGB')

        # return (PIL.ImageTk.PhotoImage(thumbnail), thumbnail, image, file)

    @staticmethod
    def getDifference(image1, image2) -> tuple:
        diffImage = PIL.ImageChops.difference(image1, image2)

        return (diffImage, max(diffImage.getdata()))

    @classmethod
    def getFileData(cls, files) -> dict:
        data = dict()

        data['file'] = list(map(pathlib.Path, files))
        data['image'] = list(map(PIL.Image.open, data['file']))
        data['thumbnail'] = [i.copy() for i in data['image']]

        size = (cls.thumbnailSize, cls.thumbnailSize)

        [t.thumbnail(size) for t in data['thumbnail']]

        data['photo'] = list(map(PIL.ImageTk.PhotoImage, data['thumbnail']))
        data['size'] = [i.size for i in data['image']]
        data['filesize'] = [f.stat().st_size for f in data['file']]

        firstThumbnail = data['thumbnail'][0]

        data['difference'] = [cls.getDifference(firstThumbnail, t)[1] for t in data['thumbnail']]
        
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

                if len(victims) > 1:
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
            enum = enumerate(value)
            groups = {v1: [idx for idx, v2 in enum if v1 == v2] for v1 in value}
            sortByValue = sorted(groups.items(), key = lambda x: x[0], reverse = True)
            sortByLen = sorted([x[1] for x in sortByValue], key = len, reverse = True)
            ranking[key] = {i: pos for pos, indices in enumerate(sortByLen) for i in indices}

        return ranking

    # def _addImages(self):
        # for idx, image, file in images:
            # column = idx % 6
        
            # if column == 0:
                # frame2 = tkinter.Frame(frame0)
                # frame2.grid(row = (idx // 6), column = 0)

            # var = tkinter.BooleanVar()
            # var.set(idxTrue == None or idxTrue == idx)
            
            # label = tkinter.LabelFrame(frame2, text = 'Difference: ' + str(diff[idx]))
            # label.grid(row = 0, column = column, padx = 2.5, pady = 2.5)
            # label.rowconfigure(0, minsize = thumbnail + 5)
            # label.columnconfigure(0, minsize = thumbnail + 5)

            # button = tkinter.Button(label, image = image[0], command = lambda: self.openFile(file), borderwidth = 0)
            # button.photoImage = image[0]
            # button.image = image[1]
            # button.grid(row = 0, column = 0)
            # button.bind('<Enter>', self.onenter(idx, checkbox))
            # button.bind('<Leave>', self.onleave(checkbox))

            # tkinter.Checkbutton(frame2, text = os.path.basename(file).encode('utf-8'), variable = var, wraplength = thumbnail, fg = self.colors(position['name'][idx])).grid(row = 1, column = column)
            # tkinter.Label(frame2, text = 'Directory: ' + os.path.dirname(file), wraplength = thumbnail, fg = self.colors(position['dir'][idx])).grid(row = 2, column = column)
            # tkinter.Label(frame2, text = 'Size: ' + str(image[2].size), wraplength = thumbnail, fg = self.colors(position['size'][idx])).grid(row = 3, column = column)
            # tkinter.Label(frame2, text = 'Filesize: ' + str(os.path.getsize(file)), wraplength = thumbnail, fg = self.colors(position['filesize'][idx])).grid(row = 4, column = column)

            # checkbox.append((file, var, button, label))

    @classmethod
    def _getColor(cls, idx: int):
        return dict(enumerate(cls.colors)).get(idx, 'black')

    @classmethod
    # def colors(cls, idx):
        # if idx >= len(cls.__colors):
            # return 'black'
        
        # return cls.__colors[idx]

    def onnext(self, key, checkbox):
        def next():
            s = set()
        
            for file, value, _, _ in checkbox:
                if value.get() == False:
                    self.moveFileToTrash(file)
                else:
                    s.add(file)

            if len(s) == 0:
                del self.imageMap[key]
            else:
                s.add('ignore')
                self.imageMap[key] = s

            self.store()
            self.next()

        return next

    def onenter(self, frame):
        def enter(event):
            for rframe in self._frame.grid_slaves():
                for cframe in rframe.grid_slaves():
                    imageLabel = cframe.grid_slaves(row = 0)[0]
                    imageFrame = imageLabel.grid_slaves()[0]

                    (diffImage, difference) = self.getDifference(frame.thumbnail, imageFrame.thumbnail)

                    imageFrame['image'] = imageFrame.diff = PIL.ImageTk.PhotoImage(diffImage)
                    imageLabel['text'] = 'Difference: ' + str(difference)

        return enter

    def onleave(self, event):
        for rframe in self._frame.grid_slaves():
            for cframe in rframe.grid_slaves():
                imageLabel = cframe.grid_slaves(row = 0)[0]
                imageFrame = imageLabel.grid_slaves()[0]

                imageFrame['image'] = imageFrame.photo

    def showNext(self):
        remaining = len(self._items)

        if remaining == 0:
            if self.command:
                self.command()
        else:
            (key, files) = self._items.popitem()

            frame = self._newFrame(key + ' (' + str(remaining - 1) + ' remaining)')

            files = [file for file in map(pathlib.Path, files) if file.is_file()]
            length = len(files)
            
            if length == 0:
                tkinter.Label(frame, text = 'Files moved or deleted').grid()

                self.after_idle(self.showNext)
            else:
                data = self.getFileData(files)

                ranking = self.groupData(data)
                selected = self._preselectCheckbox(data)

                for idx in range(length):
                    column = idx % self.maxImagesPerRow
                
                    if column == 0:
                        rframe = tkinter.Frame(frame)
                        rframe.grid(row = (idx // self.maxImagesPerRow), column = 0)

                    cframe = tkinter.Frame(rframe)
                    cframe.grid(row = 0, column = column, padx = 2.5, pady = 2.5)

                    var = tkinter.BooleanVar()
                    var.set(not selected or selected == idx)
                    
                    label = tkinter.LabelFrame(cframe, text = 'Difference: ' + str(data['difference'][idx]))
                    label.columnconfigure(0, minsize = self.thumbnailSize + 5)
                    label.rowconfigure(0, minsize = self.thumbnailSize + 5)
                    label.grid()

                    file = data['file'][idx]

                    mframe = MediaFrame(label, str(data['file'][idx]))

                    # mframe = tkinter.Button(label, image = data['photo'][idx], command = lambda: self.openFile(file), borderwidth = 0)
                    mframe.thumbnail = data['thumbnail'][idx]
                    mframe.photo = data['photo'][idx]
                    mframe.grid()
                    # mframe.bind('<Enter>', self.onenter(mframe))
                    # mframe.bind('<Leave>', self.onleave)

                    checkbox = tkinter.Checkbutton(cframe, text = str(file.name), variable = var, wraplength = self.thumbnailSize, fg = self._getColor(ranking['name'][idx]))
                    checkbox.var = var
                    checkbox.grid()

                    tkinter.Label(cframe, text = 'Directory: ' + str(file.parent), wraplength = self.thumbnailSize, fg = self._getColor(ranking['dir'][idx])).grid()
                    tkinter.Label(cframe, text = 'Size: ' + str(data['size'][idx]), wraplength = self.thumbnailSize, fg = self._getColor(ranking['size'][idx])).grid()
                    tkinter.Label(cframe, text = 'Filesize: ' + str(data['filesize'][idx]), wraplength = self.thumbnailSize, fg = self._getColor(ranking['filesize'][idx])).grid()

                    # checkbox.append((file, var, button, label))

if __name__ == '__main__':
    root = tkinter.Tk()
    root.wait_visibility()

    SelectFrame(root, {'hash': ['dance.gif']}, '.', '.').pack()
    
    root.mainloop()