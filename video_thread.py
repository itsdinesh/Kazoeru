import time
import threading
from greenlet import getcurrent as get_ident


# VideoEvent signal client when a new frame is available.
class VideoEvent(object):
    def __init__(self):
        self.events = {}

    # Invoked from the thread to wait for the next frame.
    def wait(self):
        ident = get_ident()
        if ident not in self.events:
            # Define a new client and add entry in the self.events dict
            # Each entry has two elements, a threading.Event() and a timestamp
            self.events[ident] = [threading.Event(), time.time()]
        return self.events[ident][0].wait()

    # Invoked by the thread when a new frame is available.
    def set(self):
        now = time.time()
        for ident, event in self.events.items():
            # If this client's event is not yet set, then set it.
            if not event[0].isSet():
                event[0].set()
                event[1] = now  # Update the last set timestamp to now

    # Invoked from the thread after a frame was processed.
    def clear(self):
        self.events[get_ident()][0].clear()


class VideoThread(object):
    thread = None  # Background thread that reads frames from video
    frame = None  # Current frame is stored here by background thread
    last_access = 0  # Time of last client access to the video
    event = VideoEvent()

    def __init__(self):
        # Start the background video thread if it isn't running yet.
        if VideoThread.thread is None:
            VideoThread.last_access = time.time()

            # Start background frame thread
            VideoThread.thread = threading.Thread(target=self._thread)
            VideoThread.thread.start()

            # Wait until frames are available
            while self.get_frame() is None:
                time.sleep(0)

    # Return the current frame of the video.
    @staticmethod
    def get_frame():
        VideoThread.last_access = time.time()

        # Wait for a signal from the video thread.
        VideoThread.event.wait()
        VideoThread.event.clear()
        return VideoThread.frame

    # Background Video Thread of the Web Application
    @classmethod
    def _thread(cls):
        frames_iterator = cls.frames()
        for frame in frames_iterator:
            VideoThread.frame = frame
            VideoThread.event.set()  # send signal to clients
        VideoThread.thread = None
