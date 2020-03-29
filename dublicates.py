# from tkinter import filedialog
# from tkinter import *

# def browse_button():
    # # Allow user to select a directory and store it in global var
    # # called folder_path
    # global folder_path
    # filename = filedialog.askdirectory()
    # folder_path.set(filename)
    # print(filename)


# root = Tk()
# folder_path = StringVar()
# lbl1 = Label(master=root,textvariable=folder_path)
# lbl1.grid(row=0, column=1)
# button2 = Button(text="Browse", command=browse_button)
# button2.grid(row=0, column=3)

# mainloop()

# exit()

import os
import re
import io
import sys
import json
import time
import base64
import pickle
import imghdr
import slugify
import asyncio
import filecmp
import tkinter
import tkinter.ttk
import tkinter.filedialog
import saucenao
import pysaucenao
import imagehash
import threading

import pathlib

import urllib.request
import urllib.parse

import PIL.Image
import PIL.ImageTk
import PIL.ImageFile
import PIL.ImageChops

import widgets

PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True # avoid image file is truncated

# logging.basicConfig(level = logging.DEBUG)

class Application(tkinter.Tk):
    def __init__(self, master = None):
        super().__init__(master)

        # self.loop = asyncio.get_event_loop()
        # self.attributes("-fullscreen", True)
        self.title('Dublicate finder')

        self._sframe = widgets.ScrollableFrame(self)
        self._sframe.pack()
        self._frame = None

        # tkinter.Button(self._sframe, text = 'Quit', command = self.destroy).grid(row = 1)

        self._frame = self.mainFrame(self._sframe)
        self._frame.grid(row = 0)

        # self._mainFrame()

    def _createNewFrame(self):
        if self._frame:
            self._frame.destroy()

        self._frame = tkinter.Frame(self._sframe)
        self._frame.grid(row = 0)

        return self._frame
        
        # self.frame = widgets.ScrollableFrame(self, self.winfo_screenwidth() / 2, 0)
        # self.frame.pack(expand = True, fill = tkinter.BOTH)
        # self.frame.grid(row = 0, column = 0, sticky = 'NESW')
        
        # self.frame = widgets.ScrollableFrame(self, self.winfo_screenwidth() / 2, 0)

        # return widgets.ScrollableFrame(self, self.winfo_screenwidth() / 2)

    class mainFrame(tkinter.Frame):
        dirFile = 'dirs.pkl'

        def __init__(self, master):
            super().__init__(master)
            
            self.grid_columnconfigure(1, minsize = 75)
            self.grid_columnconfigure(2, minsize = 75)

            self._load()

            print(str(self._dirs), str(self._cboxes), flush = True)
            
            tkinter.Label(self, text = 'Index').grid(row = 0, column = 1)
            tkinter.Label(self, text = 'SauceNao').grid(row = 0, column = 2)

            tkinter.Button(self, text = 'Add', command = lambda: self._add(tkinter.filedialog.askdirectory())).grid(row = 1, column = 0, sticky = 'e')
            tkinter.Button(self, text = 'Start', command = None).grid(row = 1, column = 1, columnspan = 2)

            print(sorted(self._dirs), flush = True)

            for dir in sorted(self._dirs):
                self._add(dir, *self._cboxes[dir], init = True)

        def _load(self):
            if pathlib.Path(self.dirFile).is_file():
                with open(self.dirFile, 'rb') as file:
                    (self._dirs, self._cboxes) = pickle.load(file)
            else:
                self._dirs = set()  # set for saving the dirs
                self._cboxes = dict() # and dict to associating the checkbox values

        def _store(self):
            with open(self.dirFile, 'wb') as file:
                pickle.dump((self._dirs, {key: [v.get() for v in value] for key, value in self._cboxes.items()}), file)

        def _add(self, dir: str, ivar: bool = False, svar: bool = False, init: bool = False):
            if init or not dir in self._dirs:
                icheckbox = tkinter.BooleanVar()
                icheckbox.set(ivar)
                scheckbox = tkinter.BooleanVar()
                scheckbox.set(svar)

                self._dirs.add(dir)
                self._cboxes[dir] = (icheckbox, scheckbox)

                (column, row) = self.grid_size()

                for w in self.grid_slaves(row = row - 1):
                    w.grid(row = row)

                # abutton.grid(row = row)
                
                row = row - 1

                label = tkinter.Label(self, text = dir)
                label.grid(row = row, column = 0, sticky = 'e')

                tkinter.Checkbutton(self, variable = icheckbox, command = self._store).grid(row = row, column = 1)
                tkinter.Checkbutton(self, variable = scheckbox, command = self._store).grid(row = row, column = 2)
                tkinter.Button(self, text = 'Delete', command = lambda: self._delete(label)).grid(row = row, column = 3)

                if not init:
                    self._store()

        def _delete(self, label: tkinter.Label):
            (columns, rows) = self.grid_size()

            dir = label['text']
            row = label.grid_info()['row']
            
            for s in self.grid_slaves(row = row):
                s.destroy()

            for r in range(row, rows):
                for s in self.grid_slaves(row = r):
                    s.grid(row = r - 1)

            self._dirs.remove(dir)
            self._cboxes.pop(dir)
            self._store()

    def _mainFrame(self):
        frame = self._createNewFrame()
        
        frame.grid_columnconfigure(1, minsize = 75)
        frame.grid_columnconfigure(2, minsize = 75)
        
        (dirs, cboxes) = self._dirs
        
        print(self._dirs, flush = True)
        print(type(dirs), type(cboxes), flush = True)
        
        tkinter.Label(frame, text = 'Index').grid(row = 0, column = 1)
        tkinter.Label(frame, text = 'SauceNao').grid(row = 0, column = 2)

        def add():
            filename = tkinter.filedialog.askdirectory()

            addRow(filename)
            
            # self._dirs.append((filename, ))

        abutton = tkinter.Button(frame, text = 'Add', command = add)
        abutton.grid(row = 1, column = 0, sticky = 'e')


        def addRow(dir: str, ivar: bool = False, svar: bool = False, init: bool = False):
            if init or not dir in dirs:
                icheckbox = tkinter.BooleanVar()
                icheckbox.set(ivar)
                scheckbox = tkinter.BooleanVar()
                scheckbox.set(svar)

                dirs.add(dir)
                cboxes[dir] = (icheckbox, scheckbox)

                # row = abutton.grid_info()['row']

                (column, row) = frame.grid_size()

                abutton.grid(row = row)
                
                row = row - 1

                tkinter.Label(frame, text = dir).grid(row = row, column = 0, sticky = 'e')
                tkinter.Checkbutton(frame, variable = icheckbox, command = self._storeDirs).grid(row = row, column = 1)
                tkinter.Checkbutton(frame, variable = scheckbox, command = self._storeDirs).grid(row = row, column = 2)
                tkinter.Button(frame, text = 'Delete', command = lambda: self._deleteDir(dir)).grid(row = row, column = 3)

                if not init:
                    self._storeDirs()

        for dir in sorted(dirs):
            addRow(dir, *cboxes[dir], init = True)

        print(frame.grid_slaves(row = 0), flush = True)
        print(frame.grid_size(), flush = True)
# from tkinter import filedialog
# from tkinter import *

# def browse_button():
    # # Allow user to select a directory and store it in global var
    # # called folder_path
    # global folder_path
    # filename = filedialog.askdirectory()
    # folder_path.set(filename)
    # print(filename)


# root = Tk()
# folder_path = StringVar()
# lbl1 = Label(master=root,textvariable=folder_path)
# lbl1.grid(row=0, column=1)
# button2 = Button(text="Browse", command=browse_button)
# button2.grid(row=0, column=3)


        # print(os.getcwd(), flush = True)

        # widgets.IndexFrame(frame, lambda: print('done', flush = True)).pack()

        # self.index(skip = False, fullScan = False)

    def saucenao(self):
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            path = os.path.abspath(sys.argv[1])

            for _, _, files in os.walk(path):
                break

            if len(files) == 0:
                self.nodubs()
            else:
                self.snao = pysaucenao.SauceNao()
                self.files = files
                self.saucenaoNext()
        else:
            self.nodubs()

    @staticmethod
    def createSubfolder(root, *args):
        for idx in range(len(args)):
            path = os.path.join(root, *args[:idx + 1])

            if not os.path.isdir(path):
                os.mkdir(path)

        return path

    def renameFile(self, src, dest):
        key = None

        for k, v in self.imageMap.items():
            if src in v:
                self.imageMap[k].remove(src)
                key = k
                break

        if os.path.exists(src):
            stat = os.stat(src)

            os.utime(src, ns = (time.time_ns(), stat.st_mtime_ns))
            os.rename(src, dest)

            if key:
                self.imageMap[key].add(dest)

        if key:
            self.store()

    def moveFileTo(self, file, data = None):
        dir = []

        if data:
            if type(data) is str:
                dir.append(data)
            else:
                name = None
            
                if 'material' in data:
                    name = data['material']
                elif 'source' in data:
                    name = data['source']
                elif 'title' in data:
                    name = data['title']

                if name:
                    name = slugify.slugify(name)

                    initial = name[0].upper()

                    if initial == name[0].lower():
                        dir.append('_')

                    dir.extend((initial, name[:64]))

                    if 'characters' in data:
                        dir.append(slugify.slugify(data['characters'][:64]))

        if len(dir) == 0:
            dir.append('_misc_')

        path = os.path.join(self.createSubfolder(os.path.abspath(os.path.join(os.path.dirname(file), '..')), *dir), os.path.basename(file))

        self.renameFile(file, path)

        return path

    def moveFileToTrash(self, file):
        dir = os.path.join(os.getcwd(), 'trash')

        os.makedirs(dir, exist_ok = True)
        
        path = os.path.join(dir, os.path.basename(file))

        if os.path.exists(path):
            root, ext = os.path.splitext(path)
            path = root + '-0' + ext
            idx = 1
            
            while os.path.exists(path):
                path = root + '-' + str(idx) + ext
                idx = idx + 1

        self.renameFile(file, path)

        return path

    @staticmethod
    async def fetchImage(label, thumbnail):
        img = PIL.ImageTk.PhotoImage(PIL.Image.open(io.BytesIO(urllib.request.urlopen(thumbnail).read())))

        label['image'] = img
        label.image = img
    
    removeHTML = re.compile(r'<[^>]+>')

    @classmethod
    def remove_tags(cls, text):
        return cls.removeHTML.sub('', str(text))
    
    def saucenaoNext(self):
        if len(self.files) == 0:
            self.nodubs()
        else:
            file = self.files.pop()
            path = os.path.join(os.path.abspath(sys.argv[1]), file)

            frame = self.createFrame()

            tkinter.Label(frame, text = 'Checking SauceNao for:\n"' + path + '"\n(' + str(len(self.files)) + ' remaining)').grid(row = 0)

            labelFrame = tkinter.LabelFrame(frame)
            labelFrame.grid(row = 1)

            img, _, _ = self.getImg(PIL.Image.open(path))

            label = tkinter.Label(labelFrame, image = img, borderwidth = 0)
            label.image = img
            label.pack()

            frame1 = tkinter.Frame(frame)
            frame1.grid(row = 3)

            tkinter.Button(frame1, text = 'Rescan', command = self.index).grid(row = 0, column = 0)
            tkinter.Button(frame1, text = 'Quit', command = self.destroy).grid(row = 0, column = 1)

            def thread():
                try:
                    results = self.loop.run_until_complete(self.snao.from_file(path))
                    
                    # with open('file.pkl', 'rb') as file:
                        # results = pickle.load(file)
                except pysaucenao.ShortLimitReachedException as e:
                    tkinter.Label(frame, text = self.remove_tags(e)).grid(row = 2)

                    self.files.append(file)
                except pysaucenao.DailyLimitReachedException as e:
                    tkinter.Label(frame, text = self.remove_tags(e)).grid(row = 2)
                    
                    self.files.append(file)

                    exit()
                except Exception as e:                
                    dir = self.moveFileTo(path, '_error_')

                    tkinter.Label(frame, text = self.remove_tags(e) + '\nMoved file to "' +  str(os.path.dirname(dir)) + '"').grid(row = 2)
                    
                    exit()
                else:
                    # with open('file.pkl', 'bw') as file:
                        # pickle.dump(results, file)

                    data = {}

                    for result in results:
                        for key, value in result.data.items():
                            if not key in data:
                                data[key] = []
                            
                            data[key].append(slugify.slugify(str(value)))

                    dir = self.moveFileTo(path, {key: '-'.join(sorted(list(set('-'.join(value).split('-'))))) for key, value in data.items()})
                    
                    tkinter.Label(frame, text = 'Moved file to "' +  str(os.path.dirname(dir)) + '"').grid(row = 2)

                    # tasks = []

                    # for idx, result in enumerate(results):
                        # frame3 = tkinter.LabelFrame(frame0, text = result.similarity)
                        # frame3.grid(row = 0, column = idx, padx = 5, pady = 5)

                        # thumbnail = result.thumbnail.replace(' ', '%20')
                        
                        # label = tkinter.Label(frame3)
                        # label.grid(row = 0, column = 0)

                        # tasks.append(self.fetchImage(label, thumbnail))

                        # frame4 = tkinter.Frame(frame3)
                        # frame4.grid(row = 1, column = 0)

                        # tkinter.Button(frame3, text = 'Match', command = self.moveFileTo(path, result.data)).grid(row = 2, column = 0)
                        
                        # for idx, d in enumerate(list(result.data.items())):
                            # tkinter.Label(frame4, text = str(d[0]) + ': ' + str(d[1]), wraplength = 300).grid(row = idx, column = 0)

                    # async def gather():
                        # await asyncio.gather(*tasks)

                    # self.loop.run_until_complete(gather())

                time.sleep(7.5)

                self.saucenaoNext()

            threading.Thread(target = thread, daemon = True).start()
    
    @staticmethod
    def getImg(im, box = 300):
        if im.width > im.height:
            size = (box, (box * im.height) // im.width)
        else:
            size = ((box * im.width) // im.height, box)
            
        img = im.resize(size).convert('RGB')

        return (PIL.ImageTk.PhotoImage(img), img, im)

    def nodubs(self):
        frame = self.createFrame()

        tkinter.Label(frame, text = 'No dublicates found!').grid(row = 0, column = 0, columnspan = 2)
        tkinter.Button(frame, text = 'Rescan', command = self.index).grid(row = 1, column = 0)
        tkinter.Button(frame, text = 'Quit', command = self.destroy).grid(row = 1, column = 1)

    def loaded(self):
        trash = os.path.abspath(os.path.join(os.getcwd(), 'trash'))
        self.dublicates = {key: sorted(list(value)) for key, value in [(key, [v for v in value if os.path.dirname(v) != trash]) for key, value in self.imageMap.items()] if len(value) > 1 and 'ignore' not in value}

        if len(self.dublicates) == 0:
            self.saucenao()
        else:
            self.next()

    def store(self):
        with open('imageshashes.pkl', 'wb') as file:
            pickle.dump(self.imageMap, file)

    def index(self, dir = '..', skip = False, fullScan = True):
        frame = self.createFrame()
        
        tkinter.Label(frame, text = 'Scanning for files...').grid()

        dirLabel = tkinter.Label(frame)
        dirLabel.grid()
        fileLabel = tkinter.Label(frame)
        fileLabel.grid()
        
        frame = tkinter.Frame(frame)
        frame.grid()

        pklExists = os.path.exists('imageshashes.pkl')

        if pklExists:
            if fullScan:
                tkinter.Button(frame, text = 'Quick scan', command = lambda: self.index(fullScan = False)).grid(row = 0, column = 0)
            else:
                tkinter.Button(frame, text = 'Full scan', command = self.index).grid(row = 0, column = 0)

        tkinter.Button(frame, text = 'Skip', command = lambda: self.index(skip = True)).grid(row = 0, column = 1)
        tkinter.Button(frame, text = 'Quit', command = self.destroy).grid(row = 0, column = 2)

        def thread(dir): # TODO: remove saucenao scan, add "new folder" scan to integrate, than move files to saucenao
            if pklExists:
                with open('imageshashes.pkl', 'rb') as file:
                    imageMap = pickle.load(file)

                if fullScan == False:
                    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
                        dir = sys.argv[1]
                    else:
                        dir = ''
            else:
                imageMap = {}

            if skip == False:
                try:
                    dirText = [None, ' (', None, ' remaining)']

                    for dir, dirs, files in os.walk(dir):
                        dir = os.path.abspath(dir)
                        length = len(files)
                        
                        dirText[0] = dir
                        dirText[2] = str(length)

                        dirLabel['text'] = ''.join(dirText)
                        fileLabel['text'] = ''

                        for file in files:
                            path = os.path.join(dir, file)

                            if imghdr.what(path):
                                try:
                                    im = PIL.Image.open(path)
                                except PIL.UnidentifiedImageError:
                                    pass
                                else:
                                    dirText[2] = str(length)

                                    dirLabel['text'] = ''.join(dirText)
                                    fileLabel['text'] = file

                                    hash = str(imagehash.phash(im))

                                    if hash in imageMap:
                                        if not path in imageMap[hash]:
                                            imageMap[hash].add(path)
                                            imageMap[hash].discard('ignore')
                                    else:
                                        imageMap[hash] = {path}

                            length = length - 1
                except tkinter.TclError:
                    exit() # old frame was destroyed by pressing Quick / Full Scan or Skip, so stop this thread

            self.imageMap = imageMap
            self.store()
            self.loaded()

        threading.Thread(target = thread, args = (dir, ), daemon = True).start()

    @staticmethod
    def openImage(file):
        return lambda: os.system('call "' + os.path.abspath(file) + '"')

    __colors = [
        'green',
        'red',
        'blue',
        'violet',
        'orange',
    ]

    @classmethod
    def colors(cls, idx):
        if idx >= len(cls.__colors):
            return 'black'
        
        return cls.__colors[idx]

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

    def preselectCheckbox(self, key, images, data):
        fimage = images[0][1][1]
        diff = [max([d for data in tuple(PIL.ImageChops.difference(fimage, image[1]).getdata()) for d in data]) for _, image, _ in images]
        maxdiff = max(diff)
        idxTrue = None
        
        if maxdiff < 32: # preselect best picture if difference is small
            maxsize = max(data['size'])

            victims = [idx for idx, size in enumerate(data['size']) if size == maxsize]

            if len(victims) != 1:
                sizes = [data['filesize'][idx] for idx in victims]
                maxsize = max(sizes)

                victims = [victims[idx] for idx, size in enumerate(sizes) if size == maxsize]

                if len(victims) != 1:
                    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
                        path = os.path.abspath(sys.argv[1])

                        newvictims = [idx for idx in victims if data['dir'][idx] != path]

                        if len(newvictims) != 0: # if 0 all are in search path so use old victims
                            victims = newvictims

            idxTrue = victims[0]

            # if maxdiff == 0: # could be dangerous for gifs which uses a black frame as start
                # frame = self.createFrame()

                # tkinter.Label(frame, text = 'Resolving 0 diff: "' + key + '" (' + str(len(self.dublicates)) + ' remaining)').grid(row = 0, column = 0)
                # tkinter.Button(frame, text = 'Quit', command = self.destroy).grid(row = 1, column = 0)

                # self.imageMap[key] = set((images.pop(idxTrue)[2], ))
                
                # for _, _, file in images:
                    # self.moveFileToTrash(file)

                # self.store()

                # threading.Thread(target = self.next, daemon = True).start()

                # return None, None

        return diff, idxTrue

    @staticmethod
    def onenter(idx, checkbox):
        def enter(event):
            main = checkbox[idx][2]
            image = main.image

            for _, _, button, label in checkbox:
                im = PIL.ImageChops.difference(image, button.image)
                img = PIL.ImageTk.PhotoImage(im)
                
                button['image'] = img
                button.newPhotoImage = img
                
                label['text'] = 'Difference: ' + str(max([d for data in tuple(im.getdata()) for d in data]))

            main['image'] = main.photoImage

        return enter

    @staticmethod
    def onleave(checkbox):
        def leave(event):
            for _, _, button, label in checkbox:
                button['image'] = button.photoImage

        return leave

    def next(self):
        if len(self.dublicates) == 0:
            self.loaded()
        else:
            (checkbox) = []
            (dkey, dublicate) = self.dublicates.popitem()

            dublicate = [file for file in dublicate if os.path.exists(file)]
            length = len(dublicate)
            
            if length <= 1:
                frame = self.createFrame()

                tkinter.Label(frame, text = 'Files moved or deleted: "' + dkey + '" (' + str(len(self.dublicates)) + ' remaining)').grid(row = 0, column = 0)
                tkinter.Button(frame, text = 'Quit', command = self.destroy).grid(row = 1, column = 0)

                if length == 0:
                    del self.imageMap[dkey]
                else:
                    self.imageMap[dkey] = set(dublicate)
                    
                self.store()

                threading.Thread(target = self.next, daemon = True).start()
            else:
                thumbnail = 300
            
                images = [(idx, self.getImg(PIL.Image.open(file), thumbnail), file) for idx, file in enumerate(dublicate)]
                data = {
                    'name':     [os.path.basename(file) for _, _, file in images],
                    'dir':      [os.path.dirname(file) for _, _, file in images],
                    'size':     [image[2].size for _, image, _ in images],
                    'filesize': [os.path.getsize(file) for _, _, file in images],
                }
                diff, idxTrue = self.preselectCheckbox(dkey, images, data)

                if diff:
                    position = {}

                    for key, value in data.items():
                        d = {}
                        # put data into groups
                        for idx, v in enumerate(value):
                            if v in d:
                                d[v].append(idx)
                            else:
                                d[v] = [idx]
                        
                        l = [None] * len(value)
                        # get values, sort by biggest group, create new dict with idx: ranking_position
                        for idx, value in enumerate(sorted([x[1] for x in sorted(d.items(), key = lambda x: max([x[0]]), reverse = True)], key = len, reverse = True)):
                            for v in value:
                                l[v] = idx

                        position[key] = l

                    frame = self.createFrame()

                    frame0 = tkinter.LabelFrame(frame, text = dkey + ' (' + str(len(self.dublicates)) + ' remaining)')
                    frame0.grid(row = 0, column = 0)
                    frame1 = tkinter.Frame(frame)
                    frame1.grid(row = 1, column = 0)
                    
                    tkinter.Button(frame1, text = 'Next', command = self.onnext(dkey, checkbox)).grid(row = 0, column = 0)
                    tkinter.Button(frame1, text = 'Rescan', command = self.index).grid(row = 0, column = 1)
                    tkinter.Button(frame1, text = 'Quit', command = self.destroy).grid(row = 0, column = 2)

                    for idx, image, file in images:
                        column = idx % 6
                    
                        if column == 0:
                            frame2 = tkinter.Frame(frame0)
                            frame2.grid(row = (idx // 6), column = 0)

                        var = tkinter.BooleanVar()
                        var.set(idxTrue == None or idxTrue == idx)
                        
                        label = tkinter.LabelFrame(frame2, text = 'Difference: ' + str(diff[idx]))
                        label.grid(row = 0, column = column, padx = 2.5, pady = 2.5)
                        label.rowconfigure(0, minsize = thumbnail + 5)
                        label.columnconfigure(0, minsize = thumbnail + 5)

                        button = tkinter.Button(label, image = image[0], command = self.openImage(file), borderwidth = 0)
                        button.photoImage = image[0]
                        button.image = image[1]
                        button.grid(row = 0, column = 0)
                        button.bind('<Enter>', self.onenter(idx, checkbox))
                        button.bind('<Leave>', self.onleave(checkbox))

                        tkinter.Checkbutton(frame2, text = os.path.basename(file).encode('utf-8'), variable = var, wraplength = thumbnail, fg = self.colors(position['name'][idx])).grid(row = 1, column = column)
                        tkinter.Label(frame2, text = 'Directory: ' + os.path.dirname(file), wraplength = thumbnail, fg = self.colors(position['dir'][idx])).grid(row = 2, column = column)
                        tkinter.Label(frame2, text = 'Size: ' + str(image[2].size), wraplength = thumbnail, fg = self.colors(position['size'][idx])).grid(row = 3, column = column)
                        tkinter.Label(frame2, text = 'Filesize: ' + str(os.path.getsize(file)), wraplength = thumbnail, fg = self.colors(position['filesize'][idx])).grid(row = 4, column = column)

                        checkbox.append((file, var, button, label))

if __name__ == '__main__':
    Application().mainloop()