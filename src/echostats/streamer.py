import json
import time
import zipfile
from abc import ABC
from abc import abstractmethod
from pprint import pprint
from typing import Generator

import pydantic
import requests
from echostats.models import EchoEvent


class BaseStreamer(ABC):
    @abstractmethod
    def consume(self) -> Generator[EchoEvent, None, None]:
        ...


class OnlineStreamer(BaseStreamer):
    def __init__(self, ip: str, rate: float = 10):
        self.ip = ip
        self.count = 0
        self.rate = rate

    def consume(self) -> Generator[EchoEvent, None, None]:
        while True:
            time.sleep(1 / self.rate)
            result_request = requests.get(f"http://{self.ip}:6721/session")
            if result_request.status_code == 404:
                print("skipped")
                continue

            print(f"{result_request.status_code=}")
            yield EchoEvent.parse_raw(result_request.content)


class FileStreamer(BaseStreamer):
    def __init__(self, path: str):
        self.path = path

    def consume(self) -> Generator[EchoEvent, None, None]:
        with zipfile.ZipFile(self.path) as echo_file_zip:
            assert len(echo_file_zip.namelist()) == 1, echo_file_zip.namelist()
            with echo_file_zip.open(echo_file_zip.namelist()[0]) as echo_file:
                for line in echo_file:
                    timestamp, data = line.decode().split("\t")
                    try:
                        parsed = EchoEvent.parse_raw(data)
                    except pydantic.ValidationError:
                        pprint(json.loads(data))
                        raise
                    yield parsed
