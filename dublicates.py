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
import saucenao
import pysaucenao
import imagehash
import threading

import urllib.request
import urllib.parse

import PIL.Image
import PIL.ImageTk
import PIL.ImageFile
import PIL.ImageChops

PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True # avoid image file is truncated

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
    def __init__(self, master, x, y): # hierarchy: master -> frame -> vscrollbar, hscrollbar, canvas -> self
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

        self.bind('<Configure>', lambda event: canvas.config(scrollregion = canvas.bbox('all')))

        vscrollbar.config(command = canvas.yview)
        hscrollbar.config(command = canvas.xview)

        canvas.create_window(x, y, anchor = tkinter.N, window = self)

        self.__destroy = self.destroy

        def destroy():
            return self.__destroy(), frame.destroy()

        self.grid = frame.grid
        self.pack = frame.pack
        self.place = frame.place
        self.destroy = destroy

class Application(tkinter.Tk):
    def __init__(self, master = None):
        super().__init__(master)

        self.frame = None
        self.loop = asyncio.get_event_loop()
        self.attributes("-fullscreen", True)
        self.title('Dublicate finder')

        self.index(skip = False, fullScan = False)

    def createFrame(self):
        if self.frame:
            self.frame.destroy()

        self.frame = ScrollableFrame(self, self.winfo_screenwidth() / 2, 0)
        self.frame.pack(expand = True, fill = tkinter.BOTH)

        return self.frame

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