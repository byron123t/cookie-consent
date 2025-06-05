"""Utils for enqueuing tasks."""

from consent.util.redis import REDIS_URL
from ooutil.distproc import task_enqueuer


class TaskEnqueuer:
    @classmethod
    def get_queue(cls):
        return task_enqueuer.TaskEnqueuer.get_default_queue(REDIS_URL)
