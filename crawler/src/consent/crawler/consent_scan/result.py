from ooutil.crawler.log import Log


class FramesLog(Log):
    def __init__(self, main_frame_url):
        super().__init__()
        self.frames = []
        self.main_frame_url = main_frame_url
