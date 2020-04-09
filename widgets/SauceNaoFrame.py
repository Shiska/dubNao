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

sys.path = list(set((*sys.path, str(pathlib.Path(__file__).parent))))

from MediaFrame import MediaFrame
from IndexFrame import IndexFrame
from SettingFrame import SettingFrame

class SauceNaoFrame(tkinter.Frame):
    def __init__(self, master, command = None):
        super().__init__(master)

        self.command = command

        self._snao = pysaucenao.SauceNao()
        self._sauceNaoDir = pathlib.Path(SettingFrame.sauceNaoDir)
        self._destDir = pathlib.Path(SettingFrame.destDir).resolve()
        self._event_loop = asyncio.get_event_loop()
        self._imageMap = IndexFrame.imageMap
        self._items = iter(())

        oframe = tkinter.LabelFrame(self, text = 'SauceNAO')
        oframe.pack()

        frame = self._imageFrame = tkinter.LabelFrame(oframe)
        frame.pack()

        mediaFrame = self._mediaFrame = MediaFrame(frame, onFrameChange = self._onFrameChange)
        mediaFrame.pack()

        label = self._messageLabel = tkinter.Label(oframe)
        label.pack()

        self._next()

    @staticmethod
    async def fetchImage(obj, url):
        obj['image'] = obj.image = PIL.ImageTk.PhotoImage(PIL.Image.open(io.BytesIO(urllib.request.urlopen(url.replace(' ', '%20')).read())))
    
    _removeHTML = re.compile(r'<[^>]+>')

    @classmethod
    def removeHTML(cls, text):
        return cls._removeHTML.sub('', str(text))

    def _onFrameChange(self, mframe, thumbnail):
        image = mframe._image.copy()
        image.thumbnail((image.width, self.winfo_screenheight() * 3 // 4))

        mframe._setPhoto(image)

    def _getDestFolder(self, results):
        data = collections.defaultdict(list)

        for result in results:
            for key, value in result.data.items():
                data[key].append(slugify.slugify(str(value)))

        data = {key: '-'.join(sorted(list(set('-'.join(value).split('-'))))) for key, value in data.items()}
        
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

        return self._imageMap.moveFileTo(file, dest)

    def _check(self, file):
        self._messageLabel['text'] = 'Checking...'

        try:
            results = self._event_loop.run_until_complete(self._snao.from_file(file)) # impossible to integrate into mainloop because this shit forces you to use a second event loops
        except pysaucenao.ShortLimitReachedException as e:
            self._messageLabel['text'] = self.removeHTML(e)

            func = self._next
        except pysaucenao.DailyLimitReachedException as e:
            self._messageLabel['text'] = self.removeHTML(e)

            func = self._executeCommand
        except Exception as e:
            self._messageLabel['text'] = self.removeHTML(e) + '\nMoved file to "' +  str(self._moveFileTo(file, '_error_').parent) + '"'

            func = self._executeCommand
        else:
            self._messageLabel['text'] = 'Moved file to "' +  str(self._moveFileTo(file, self._getDestFolder(results)).parent) + '"'

            func = self._next

        self.after(7500, func)

    def _next(self):
        file = next(self._items, None)

        if not file:
            self._items = (v for key, value in self._imageMap for v in value if self._sauceNaoDir in pathlib.Path(v).parents)

            file = next(self._items, None)

            if not file: # no more files found
                return self.after_idle(self._executeCommand)

        self._imageFrame['text'] = pathlib.Path(file).name
        self._mediaFrame.open(file)

        threading.Thread(target = self._check, args = (file, ), daemon = True).start()

    def _executeCommand(self):
        if self.command:
            self.command()

if __name__ == '__main__':
    root = tkinter.Tk()
    root.wait_visibility()

    SauceNaoFrame(root, command = lambda: root.after_idle(root.destroy)).pack(fill = tkinter.BOTH)

    root.mainloop()