from collections import defaultdict

from ooutil.crawler.log import Log


class ConsentScannerLog(Log):
    def __init__(self):
        super().__init__()
        self.scan_result = defaultdict(list)
