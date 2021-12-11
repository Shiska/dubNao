import re
import io
import asyncio
import pathlib
import slugify
import tkinter
import traceback
import threading
import pysaucenao
import collections
import urllib.request
import PIL.Image, PIL.ImageTk

import widgets.Data as Data
import widgets.Media as Media
import widgets.Trash as Trash
import widgets.Setting as Setting

Data = Data.ImageMap(Data.Data('sauceNao'))

class Frame(tkinter.Frame):
    def __init__(self, master, command = None, browse = None):
        super().__init__(master)

        self.command = command or self._browse
        self.browse = browse

        self._snao = pysaucenao.SauceNao(api_key = Setting.Data.apiKey)

        self._tempDir = pathlib.Path(Setting.Data.tempDir).resolve()
        self._destDir = pathlib.Path(Setting.Data.destDir).resolve()
        self._event_loop = asyncio.new_event_loop()

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

        self._dict = Data._dict
        self._getGenerator()

        item = next(self._itemsGenerator, None)

        if item:
            self._items = [item]
        else:
            self._items = []

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
        # 2. remove duplicated items (set)
        # 3. filter empty strings
        # 4. sort list so different orders result in the same output
        # 5. joint result by spaces '-'
        data = {key: '-'.join(sorted(filter(None, set('-'.join(value).split('-'))))) for key, value in data.items()}
        
        dirs = []
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

        with Data as data:
            return data.moveFileTo(file, dest)

    def _sauceNao(self, file, success, failure, delay = 7500): # 30 seconds / 4 = wait 7.5 seconds inbetween checks
        self._messageLabel['text'] = 'Checking...'

        try: # impossible to integrate into the mainloop because all asyncio functions are blocking!!!!!!
            results = self._event_loop.run_until_complete(self._snao.from_file(file))
        except pysaucenao.ShortLimitReachedException as e: # 4 checks in 30 seconds
            self._messageLabel['text'] = 'Short limit reached, waiting...'

            func = lambda: self._sauceNao(file, success, failure)
        except pysaucenao.DailyLimitReachedException as e:
            self._messageLabel['text'] = 'Daily limit reached!'

            func = failure
        except pysaucenao.FileSizeLimitException as e:
            self._messageLabel['text'] = 'File to big\nMoved file to "' +  str(self._moveFileTo(file, '_error_\_tobig_').parent) + '"'

            func = success
        except pysaucenao.InvalidOrWrongApiKeyException as e:
            self._messageLabel['text'] = 'Invalid or wrong API Key'

            func = failure
        except pysaucenao.ImageSizeException as e:
            self._messageLabel['text'] = 'File to small\nMoved file to "' +  str(self._moveFileTo(file, '_error_\_tosmall_').parent) + '"'

            func = success
        except pysaucenao.InvalidImageException as e:
            self._messageLabel['text'] = 'Invalid image\nMoved file to "' +  str(self._moveFileTo(file, '_error_\_invalid_').parent) + '"'

            func = success
        except pysaucenao.TooManyFailedRequestsException as e:
            self._messageLabel['text'] = 'To many failed requests'

            func = failure
        except pysaucenao.BannedException as e:
            self._messageLabel['text'] = 'Account banned!'

            func = failure
        except pysaucenao.UnknownStatusCodeException as e:
            self._messageLabel['text'] = self.removeHTML(e)

            func = failure
        except Exception as e:
            self._messageLabel['text'] = traceback.format_exc() + '\nMoved file to "' +  str(self._moveFileTo(file, '_error_').parent) + '"'

            func = success
        else:
            self._messageLabel['text'] = 'Moved file to "' +  str(self._moveFileTo(file, self._getDestFolder(results)).parent) + '"'

            func = success

        self.after(delay, func)

    def _checkAll(self):
        self._buttonsFrame.pack_forget()
        self._messageLabel.pack()

        items = (v for hash, value in Data for v in map(pathlib.Path, value) if v.parent == self._tempDir)

        self.unbind('<Left>')
        self.unbind('<Down>')
        self.unbind('<Up>')
        self.unbind('<Right>')

        def nextItem():
            if len(self._items):
                file = self._items.pop()
            else:
                file = next(self._itemsGenerator, None)

            if not file: # no files found
                return self.after_idle(self.command)

            self._imageFrame['text'] = file.name
            self._mediaFrame.open(str(file))

            threading.Thread(target = self._sauceNao, args = (file, nextItem, self.command), daemon = True).start()

        nextItem()

    def _showIndex(self, index):
        self._index = index
        self._messageLabel.pack_forget()

        length = len(self._items)

        if index < length:
            file = self._items[index]
            index += 1

            if index == length: # add next item from generator if we are near the end
                value = next(self._itemsGenerator, None)

                if value:
                    self._items.append(value)
                    length += 1

            self._previousButton['state'] = tkinter.DISABLED if index == 1 else tkinter.NORMAL
            self._nextButton['state'] = tkinter.DISABLED if index == length else tkinter.NORMAL

            self._imageFrame['text'] = file.name + ' (' + str(index) + ')'
            self._mediaFrame.open(str(file))

            self.update_idletasks()
        else:
            if self.browse:
                self.after_idle(self.browse)
            else:
                for oframe in self.pack_slaves():
                    for s in oframe.pack_slaves():
                        s.destroy()

                tkinter.Label(oframe, text = 'Empty').pack()

    def _next(self, event = None):
        if self._nextButton['state'] != tkinter.DISABLED:
            self._showIndex(self._index + 1)

    def _previous(self, event = None):
        if self._previousButton['state'] != tkinter.DISABLED:
            self._showIndex(self._index - 1)

    def _checkSuccess(self):
        def proceed():
            index = self._index

            self._items.pop(index)
            self._checkFailure()

            if len(self._items) == index:
                self._showIndex(index - 1)
            else:
                self._showIndex(index)

        self.after(5000, proceed)

    def _checkFailure(self):
        self._previousButton['state'] = self._previousButton.state
        self._nextButton['state'] = self._nextButton.state
        self._checkButton['state'] = self._deleteButton['state'] = self._checkAllButton['state'] = tkinter.NORMAL

    def _check(self, event = None):
        if self._checkButton['state'] != tkinter.DISABLED:
            self._messageLabel.pack()

            self._previousButton.state = self._previousButton['state']
            self._nextButton.state = self._nextButton['state']

            self._previousButton['state'] = self._nextButton['state'] = self._checkButton['state'] = self._deleteButton['state'] = self._checkAllButton['state'] = tkinter.DISABLED

            threading.Thread(target = self._sauceNao, args = (self._mediaFrame._filename, self._checkSuccess, self._checkFailure, 0), daemon = True).start()

    def _getGenerator(self):
        self._itemsGenerator = (v for hash, value in reversed(Data._dict.items()) for v in map(pathlib.Path, value) if v.exists() and v.parent == self._tempDir)

    def _delete(self, event = None):
        if self._deleteButton['state'] != tkinter.DISABLED:
            index = self._index
            file = str(self._items.pop(index))

            with Trash.Data as trashData:
                Data.remove(file)
                trashData.add(file)
                # recreate generator because dict has changed
                self._getGenerator()

                if len(self._items) == index:
                    self._showIndex(index - 1)
                else:
                    self._showIndex(index)

            Data.store()

    def _browse(self):
        self.focus_set()

        self.bind('<Left>',     self._previous)
        self.bind('<Down>',     self._delete)
        self.bind('<Up>',       self._check)
        self.bind('<Right>',    self._next)

        self._imageFrame.pack_forget()
        self._buttonsFrame.pack(expand = True, fill = tkinter.X)
        self._imageFrame.pack()

        self._showIndex(0)

if __name__ == '__main__':
    root = tkinter.Tk()
    root.wait_visibility()
    root.state('zoomed')

    Frame(root, browse = lambda: root.after_idle(root.destroy)).pack(fill = tkinter.BOTH)

    root.mainloop()