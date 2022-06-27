import os
import zipfile
from contextlib import AbstractContextManager
from datetime import datetime
from typing import Iterable

from echostats._abc import BaseConsumer
from echostats.models import ConsumerEvent


class RecorderConsumer(BaseConsumer):
    def __init__(self, path: str):
        self.path = path
        self.zfile = zipfile.ZipFile(self.path, mode="w")
        self.fp = self.zfile.open(os.path.basename(self.path), mode="w")

    def get_context_managers(self) -> Iterable[AbstractContextManager]:
        return [self.zfile, self.fp]

    def consume(self, event: ConsumerEvent) -> None:
        dt = datetime.now().isoformat(sep=" ", timespec="milliseconds").encode()
        line = dt + b"\t" + event.stream_event.data + b"\n"
        self.fp.write(line)
