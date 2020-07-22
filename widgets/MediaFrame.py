import os
import cv2
import tkinter
import pathlib
import platform
import PIL.Image
import subprocess
import PIL.ImageTk
import PIL.ImageDraw
import PIL.ImageFile
import PIL.ImageFont

PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True # avoid image file is truncated

def fdebug(func):
    def wrapper(self, *args, **kwargs):
        print(func.__name__, str(args), str(kwargs), flush = True)

        return func(self, *args, **kwargs)

    # return wrapper
    return func

class MediaFrame(tkinter.Frame):
    @fdebug
    def __init__(self, master, filename: str = None, thumbSize: tuple = (300, 300), autoplay: bool = True, loop: bool = True, onFrameChange = None):
        super().__init__(master)

        self.label = tkinter.Label(self)
        self.label.pack()

        self.framePos = tkinter.IntVar()
        self.scale = tkinter.Scale(self, orient = tkinter.HORIZONTAL, showvalue = False, variable = self.framePos, command = self._onScaleChanged)

        self._onFrameChange = onFrameChange
        self._video = cv2.VideoCapture()
        self._after = None        

        self.thumbSize = thumbSize
        self.autoplay = autoplay
        self.loop = loop

        self.bind = self.label.bind

        if filename:
            self.open(filename)

    @fdebug
    def open(self, filename: str):
        """ filename:
            - name of video file (eg. video.avi)
            - or image sequence (eg. img_%02d.jpg, which will read samples like img_00.jpg, img_01.jpg, img_02.jpg, ...)
            - or URL of video stream (eg. protocol://host:port/script_name?script_params|auth)
            - or GStreamer pipeline string in gst-launch tool format in case if GStreamer is used as backend Note that each video stream or IP camera feed has its own URL scheme. Please refer to the documentation of source stream to know the right URL.
        """
        self._delay = None
        self.scale.pack_forget()
        self._filename = filename

        if pathlib.Path(filename).exists():
            self._video.open(filename)

            isOpened = self._video.isOpened()

            if isOpened: # file was opened, check if first frame is readable
                isOpened = self._nextFrame()

            if not isOpened:
                self._setImage(PIL.Image.open(filename))
            else:
                frame_count = self._video.get(cv2.CAP_PROP_FRAME_COUNT)

                if frame_count > 1:
                    self._delay = int(1000 // self._video.get(cv2.CAP_PROP_FPS))

                    self.scale.config(to = frame_count - 1, length = self.label.winfo_reqwidth())
                    self.scale.pack()

                if self.autoplay:
                    self.play()
        else:
            text = 'File "' + filename + '" not found'
            font = PIL.ImageFont.load_default()
            width = font.getsize(text)

            img = PIL.Image.new('RGBA', (width[0] + 20, width[1] + 20))
             
            PIL.ImageDraw.Draw(img).text((10, 10), 'File "' + filename + '" not found', fill = 'black')

            self.thumbSize = None # avoid resizing
            self._setImage(img)

    @fdebug
    def _onScaleChanged(self, value: str):
        self._setFrame(int(value))

    @fdebug
    def _setFrame(self, index: int):
        self._video.set(cv2.CAP_PROP_POS_FRAMES, index)
        self._nextFrame()

    @fdebug
    def _nextFrame(self):
        ret, frame = self._video.read()

        if not ret and self.loop:
            self._video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self._video.read()

        if ret:
            self.framePos.set(self._video.get(cv2.CAP_PROP_POS_FRAMES) - 1)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            self._setImage(PIL.Image.fromarray(frame))

        return ret

    @fdebug
    def _setImage(self, image):
        image = self._image = image.convert('RGBA')
        thumbnail = self._thumbnail = image.copy()

        if self.thumbSize:
            thumbnail.thumbnail(self.thumbSize)

        if self._onFrameChange:
            self._setPhoto(self._onFrameChange(self, thumbnail) or thumbnail)
        else:
            self._setPhoto(thumbnail)

    @staticmethod
    def thumbnailScreensize(frame, image):
        image = image.copy()
        image.thumbnail((min(image.width, frame.winfo_screenwidth() * 95 // 100), min(image.height, frame.winfo_screenheight() * 85 // 100)))

        return image

    @fdebug
    def _setPhoto(self, photo):
        self.label['image'] = self.photo = PIL.ImageTk.PhotoImage(image = photo)

    @fdebug
    def __getitem__(self, index):
        return self.label[index]

    @fdebug
    def __setitem__(self, index, value):
        self.label[index] = value

    @fdebug
    def play(self):
        if self._delay and not self._after and self._video.isOpened():
            if self._video.get(cv2.CAP_PROP_POS_FRAMES) == self._video.get(cv2.CAP_PROP_FRAME_COUNT): # reset to start if video finished playing
                self._video.set(cv2.CAP_PROP_POS_FRAMES, 0)

            self._after = self.after(self._delay, self._update)

    @fdebug
    def _update(self):
        if self._video.isOpened():
            ret = self._nextFrame()

            if ret:
                self._after = self.after(self._delay, self._update)
            else: # no more frames
                self._after = None
            # the gui froze with 3 large gifs playing at the same time...
            # why does it prioritise to execute the next after instead of updating the idletasks
            self.update_idletasks()

    @fdebug
    def stop(self):
        if self._after:
            self.after_cancel(self._after)
            self._after = None

    @fdebug
    def toggle(self, *args):
        if self._after:
            self.stop()
        else:
            self.play()

    @fdebug
    def reset(self):
        self._setFrame(0)

    @fdebug
    def release(self):
        self.stop()
        self._video.release()

    @fdebug
    def destroy(self):
        self.release()

        return super().destroy()

    @fdebug
    def osOpen(self):
        if platform.system() == 'Darwin':
            subprocess.call(('open', self._filename))
        elif platform.system() == 'Windows':
            os.startfile(self._filename)
        else: # linux
            subprocess.call(('xdg-open', self._filename))

    @property
    @fdebug
    def isPlaying(self) -> bool:
        return self.isVideo and bool(self._after)

    @property
    @fdebug
    def isVideo(self) -> bool:
        return not self.isImage

    @property
    @fdebug
    def isImage(self) -> bool:
        return not self._delay

if __name__ == '__main__':
    from SelectFrame import SelectFrame

    root = tkinter.Tk()

    frame = MediaFrame(root, next(next(iter(SelectFrame.data()))[1]))
    frame.pack()

    frame.label.bind('<Button-1>', frame.toggle)
    
    root.mainloop()