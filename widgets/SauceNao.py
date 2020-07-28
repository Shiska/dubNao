import re
import io
import sys
import asyncio
import pathlib
import slugify
import tkinter
import threading
import pysaucenao
import collections
import urllib.request
import PIL.Image, PIL.ImageTk

sys.path.append(str(pathlib.Path(__file__).parent))

import Index
import Media
import Trash
import Setting

sys.path.pop()

def Data():
    return Index.ImageMap('sauceNao.pkl')

class Frame(tkinter.Frame):
    def __init__(self, master, command = None, browse = False):
        super().__init__(master)

        self.command = command or self._browse

        self._snao = pysaucenao.SauceNao()
        self._tempDir = pathlib.Path(Setting.Data.tempDir).resolve()
        self._destDir = pathlib.Path(Setting.Data.destDir).resolve()
        self._event_loop = asyncio.get_event_loop()
        self._data = Data()

        oframe = tkinter.LabelFrame(self, text = 'SauceNAO')
        oframe.pack()

        frame = self._buttonsFrame = tkinter.Frame(oframe)

        self._previousButton = tkinter.Button(frame, text = 'Previous (Left)', command = self._previous)
        self._previousButton.pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)

        self._nextButton = tkinter.Button(frame, text = 'Next (Right)', command = self._next)
        self._nextButton.pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)

        self._checkButton = tkinter.Button(frame, text = 'Check (Up)', command = self._check)
        self._checkButton.pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)

        self._deleteButton = tkinter.Button(frame, text = 'Delete (Down)', command = self._delete)
        self._deleteButton.pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)

        self._checkAllButton = tkinter.Button(frame, text = 'Check all', command = self._checkAll)
        self._checkAllButton.pack(expand = True, fill = tkinter.X, side = tkinter.LEFT)

        self._imageFrame = tkinter.LabelFrame(oframe)
        self._imageFrame.pack()

        mediaFrame = self._mediaFrame = Media.Frame(self._imageFrame, onFrameChange = lambda mframe, thumbnail: Media.Frame.thumbnailScreensize(self, mframe._image))
        mediaFrame.pack()

        self._messageLabel = tkinter.Label(oframe)
        self._messageLabel.pack()

        if browse:
            self._browse()
        else:
            self._checkAll()

    @staticmethod
    async def fetchImage(obj, url):
        obj['image'] = obj.image = PIL.ImageTk.PhotoImage(PIL.Image.open(io.BytesIO(urllib.request.urlopen(url.replace(' ', '%20')).read())))
    
    _removeHTML = re.compile(r'<[^>]+>')

    @classmethod
    def removeHTML(cls, text):
        return cls._removeHTML.sub('', str(text))

    def _getDestFolder(self, results):
        data = collections.defaultdict(list)

        for result in results:
            for key, value in result.data.items():
                data[key].append(slugify.slugify(str(value)))
        # 1. split all values by spaces, now '-' after slugify (join + split)
        # 2. remove dublicated items (set)
        # 3. filter empty strings
        # 4. sort list so different orders result in the same output
        # 5. joint result by spaces '-'
        data = {key: '-'.join(sorted(filter(None, set('-'.join(value).split('-'))))) for key, value in data.items()}
        
        dirs = []
        name = None

        name = list(filter(None, (data.get('material'), data.get('source'), data.get('title'))))

        if len(name):
            name = name[0]
            initial = name[0].upper()

            if initial == name[0].lower():
                dirs.append('_')

            dirs.extend((initial, name[:64]))

            if 'characters' in data:
                dirs.append(data['characters'][:64])

        if len(dirs) == 0:
            dirs.append('_misc_')

        return pathlib.PurePath(*dirs)

    def _moveFileTo(self, file, dir):
        dest = self._destDir.joinpath(dir)

        self._mediaFrame.release()

        dest = self._data.moveFileTo(file, dest)

        self._data.store()

        return dest

    def _sauceNao(self, file, success, failure, delay = 7500): # 30 seconds / 4 = wait 7.5 seconds inbetween checks
        self._messageLabel['text'] = 'Checking...'

        try:
            results = self._event_loop.run_until_complete(self._snao.from_file(file)) # impossible to integrate into mainloop because this shit forces you to use a second event loops
        except pysaucenao.ShortLimitReachedException as e: # 4 checks in 30 seconds
            self._messageLabel['text'] = self.removeHTML(e)

            func = lambda: self._sauceNao(file, success, failure)
        except pysaucenao.DailyLimitReachedException as e:
            self._messageLabel['text'] = self.removeHTML(e)

            func = failure
        except Exception as e:
            self._messageLabel['text'] = self.removeHTML(e) + '\nMoved file to "' +  str(self._moveFileTo(file, '_error_').parent) + '"'

            func = failure
        else:
            self._messageLabel['text'] = 'Moved file to "' +  str(self._moveFileTo(file, self._getDestFolder(results)).parent) + '"'

            func = success

        self.after(delay, func)

    def _checkAll(self):
        self._buttonsFrame.pack_forget()
        self._messageLabel.pack()

        items = (v for hash, value in self._data for v in map(pathlib.Path, value) if v.parent == self._tempDir)

        self.unbind('<Left>')
        self.unbind('<Down>')
        self.unbind('<Up>')
        self.unbind('<Right>')

        def nextItem():
            file = next(items, None)

            if not file: # no files found
                return self.after_idle(self.command)

            self._imageFrame['text'] = file.name
            self._mediaFrame.open(str(file))

            threading.Thread(target = self._sauceNao, args = (file, nextItem, self.command), daemon = True).start()

        nextItem()

    def _showIndex(self, index):
        self._index = index
        self._messageLabel.pack_forget()

        file = self._items[index]
        length = len(self._items)
        index = index + 1

        self._previousButton['state'] = tkinter.DISABLED if index == 1 else tkinter.NORMAL
        self._nextButton['state'] = tkinter.DISABLED if index == length else tkinter.NORMAL

        self._imageFrame['text'] = file.name + ' (' + str(index) + '/' + str(length) + ')'
        self._mediaFrame.open(str(file))

        self.update_idletasks()

    def _next(self, event = None):
        if self._nextButton['state'] != tkinter.DISABLED:
            if self._success:
                self._success = False
                self._showIndex(self._index)
            else:
                self._showIndex(self._index + 1)

    def _previous(self, event = None):
        if self._previousButton['state'] != tkinter.DISABLED:
            self._showIndex(self._index - 1)
            self._success = False

    def _checkSuccess(self):
        self._items.pop(self._index)
        self._success = True
        self._checkFailure()

    def _checkFailure(self):
        self._previousButton['state'] = self._previousButton.state
        self._nextButton['state'] = self._nextButton.state
        self._checkButton['state'] = tkinter.NORMAL
        self._deleteButton['state'] = tkinter.NORMAL

    def _check(self, event = None):
        if self._checkButton['state'] != tkinter.DISABLED:
            self._messageLabel.pack()

            self._previousButton.state = self._previousButton['state']
            self._nextButton.state = self._nextButton['state']

            self._previousButton['state'] = tkinter.DISABLED
            self._nextButton['state'] = tkinter.DISABLED
            self._checkButton['state'] = tkinter.DISABLED
            self._deleteButton['state'] = tkinter.DISABLED

            threading.Thread(target = self._sauceNao, args = (self._mediaFrame._filename, self._checkSuccess, self._checkFailure, 0), daemon = True).start()

    def _delete(self, event = None):
        if self._deleteButton['state'] != tkinter.DISABLED:
            index = self._index
            file = str(self._items.pop(index))

            self._data.remove(file)
            self._trashData.add(file)

            if len(self._items) == index:
                self._showIndex(index - 1)
            else:
                self._showIndex(index)

            self._trashData.store()
            self._data.store()

    def _browse(self):
        self._items = ([v for hash, value in self._data for v in map(pathlib.Path, value) if v.parent == self._tempDir])[::-1]

        self.focus_set()

        self.bind('<Left>',     self._previous)
        self.bind('<Down>',     self._delete)
        self.bind('<Up>',       self._check)
        self.bind('<Right>',    self._next)

        self._imageFrame.pack_forget()
        self._buttonsFrame.pack(expand = True, fill = tkinter.X)
        self._imageFrame.pack()

        self._trashData = Trash.Data()
        self._success = False
        self._showIndex(0)

if __name__ == '__main__':
    root = tkinter.Tk()
    root.wait_visibility()
    root.state('zoomed')

    Frame(root, command = lambda: root.after_idle(root.destroy), browse = True).pack(fill = tkinter.BOTH)

    root.mainloop()