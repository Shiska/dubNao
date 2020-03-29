import cv2
import tkinter
import PIL.Image
import PIL.ImageTk

class MediaFrame(tkinter.Frame):
    def __init__(self, master, filename: str, size: tuple = (300, 300), autoplay: bool = True, loop: bool = True):
        super().__init__(master)

        self.label = tkinter.Label(self)
        self.label.bind('<Button-1>', self._toggle)
        self.label.pack()

        self.framePos = tkinter.IntVar()

        self.scale = tkinter.Scale(self, orient = tkinter.HORIZONTAL, showvalue = False, variable = self.framePos, command = self._onScaleChanged)

        self._video = cv2.VideoCapture()
        self._after = None        

        self.autoplay = autoplay
        self.loop = loop
        self.size = size
        self.open(filename)

    def open(self, filename: str):
        """ filename:
            - name of video file (eg. video.avi)
            - or image sequence (eg. img_%02d.jpg, which will read samples like img_00.jpg, img_01.jpg, img_02.jpg, ...)
            - or URL of video stream (eg. protocol://host:port/script_name?script_params|auth)
            - or GStreamer pipeline string in gst-launch tool format in case if GStreamer is used as backend Note that each video stream or IP camera feed has its own URL scheme. Please refer to the documentation of source stream to know the right URL.
        """
        self._video.open(filename)

        if not self._video.isOpened():
            raise ValueError('Unable to open file', filename)

        self._setFrame(0)

        frame_count = self._video.get(cv2.CAP_PROP_FRAME_COUNT)

        if frame_count == 1: # image
            self._delay = None

            self.scale.pack_forget()
        else:
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

            image = PIL.Image.fromarray(frame)
            image.thumbnail(self.size)

            self.label['image'] = self._image = PIL.ImageTk.PhotoImage(image = image)

        return ret

    def play(self):
        if self._video.isOpened() and self._delay and not self._after:
            if self._video.get(cv2.CAP_PROP_POS_FRAMES) == self._video.get(cv2.CAP_PROP_FRAME_COUNT): # reset to start if video finished playing
                self._video.set(cv2.CAP_PROP_POS_FRAMES, 0)

            self._after = self.after(self._delay, self._update)

    def _update(self):
        if self.video.isOpened():
            ret = self._nextFrame()

            if ret:
                self._after = self.after(self._delay, self._update)
            else: # no more frames
                self._after = None

    def stop(self):
        if self._after:
            self.after_cancel(self._after)
            self._after = None

    def _toggle(self, *args):
        if self._after:
            self.stop()
        else:
            self.play()

    @property
    def video(self):
        return self._video

    @property
    def isPlaying(self) -> bool:
        return (self._after != None)

    def destroy(self):
        self.stop()

        return super().destroy()

if __name__ == "__main__":
    root = tkinter.Tk()

    MediaFrame(root, 'dance.gif').pack()
    
    root.mainloop()