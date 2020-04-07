import cv2
import tkinter
import PIL.Image
import PIL.ImageTk
import PIL.ImageFile

PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True # avoid image file is truncated

class MediaFrame(tkinter.Frame):
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

    def open(self, filename: str):
        """ filename:
            - name of video file (eg. video.avi)
            - or image sequence (eg. img_%02d.jpg, which will read samples like img_00.jpg, img_01.jpg, img_02.jpg, ...)
            - or URL of video stream (eg. protocol://host:port/script_name?script_params|auth)
            - or GStreamer pipeline string in gst-launch tool format in case if GStreamer is used as backend Note that each video stream or IP camera feed has its own URL scheme. Please refer to the documentation of source stream to know the right URL.
        """
        self._delay = None
        self.scale.pack_forget()
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

    def _onScaleChanged(self, value: str):
        self._setFrame(int(value))

    def _setFrame(self, index: int):
        self._video.set(cv2.CAP_PROP_POS_FRAMES, index)
        self._nextFrame()

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

    def _setImage(self, image):
        image = self._image = image.convert('RGB')

        thumbnail = self._thumbnail = image.copy()
        thumbnail.thumbnail(self.thumbSize)

        self._setPhoto(thumbnail)

        if self._onFrameChange:
            self._onFrameChange(self, thumbnail)

    def _setPhoto(self, photo):
        self['image'] = self.photo = PIL.ImageTk.PhotoImage(image = photo)

    def __getitem__(self, index):
        return self.label[index]

    def __setitem__(self, index, value):
        self.label[index] = value

    def play(self):
        if self._delay and not self._after and self._video.isOpened():
            if self._video.get(cv2.CAP_PROP_POS_FRAMES) == self._video.get(cv2.CAP_PROP_FRAME_COUNT): # reset to start if video finished playing
                self._video.set(cv2.CAP_PROP_POS_FRAMES, 0)

            self._after = self.after(self._delay, self._update)

    def _update(self):
        if self._video.isOpened():
            ret = self._nextFrame()

            if ret:
                self._after = self.after(self._delay, self._update)
            else: # no more frames
                self._after = None

    def stop(self):
        if self._after:
            self.after_cancel(self._after)
            self._after = None

    def toggle(self, *args):
        if self._after:
            self.stop()
        else:
            self.play()

    def reset(self):
        self._setFrame(0)

    def release(self):
        self.stop()
        self._video.release()

    def destroy(self):
        self.release()

        return super().destroy()

    @property
    def isPlaying(self) -> bool:
        return self.isVideo and bool(self._after)

    @property
    def isVideo(self) -> bool:
        return not self.isImage

    @property
    def isImage(self) -> bool:
        return not self._delay

if __name__ == "__main__":
    from IndexFrame import ImageMap

    root = tkinter.Tk()
    
    # help(root)
    
    # exit()

    frame = MediaFrame(root, str(ImageMap()._data.popitem()[1].pop()))
    frame.pack()

    frame.label.bind('<Button-1>', frame.toggle)
    
    root.mainloop()