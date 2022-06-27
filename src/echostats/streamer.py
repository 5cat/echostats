import time
import zipfile
from abc import ABC
from abc import abstractmethod
from contextlib import ExitStack
from typing import Generator
from typing import Iterable

import requests
from echostats._abc import BaseConsumer
from echostats._abc import ConsumerDependent
from echostats._abc import ConsumerMapping
from echostats.models import ConsumerEvent
from echostats.models import EchoEvent
from echostats.models import StreamEvent


class BaseStreamer(ABC):
    @abstractmethod
    def read(self) -> Generator[StreamEvent, None, None]:
        ...

    def consume(self, consumers: Iterable[BaseConsumer]):
        with ExitStack() as stack:
            for consumer in consumers:
                for conti in consumer.get_context_managers():
                    stack.enter_context(conti)
            for stream_event in self.read():
                echo_event = EchoEvent.parse_raw(stream_event.data)
                event = ConsumerEvent.construct(
                    stream_event=stream_event, echo_event=echo_event
                )
                for consumer in consumers:
                    consumer.consume(event)

    def resolve(self, dependents: Iterable[ConsumerDependent]) -> ConsumerMapping:
        consumer_dict = {}
        for dependent in dependents:
            for consumer_class in dependent.get_dependencies():
                if consumer_class not in consumer_dict:
                    consumer_dict[consumer_class] = consumer_class()

        self.consume(consumer_dict.values())
        safe_consumer_dict = ConsumerMapping(consumer_dict)
        for dependent in dependents:
            dependent.init(safe_consumer_dict)
        return safe_consumer_dict


class OnlineStreamer(BaseStreamer):
    def __init__(self, ip: str, rate: float = 10):
        self.ip = ip
        self.count = 0
        self.rate = rate

    def read(self) -> Generator[StreamEvent, None, None]:
        while True:
            time.sleep(1 / self.rate)
            result_request = requests.get(f"http://{self.ip}:6721/session")
            if result_request.status_code == 404:
                print("skipped")
                continue

            print(f"{result_request.status_code=}")
            yield StreamEvent(data=result_request.content)


class FileStreamer(BaseStreamer):
    def __init__(self, path: str):
        self.path = path

    def read(self) -> Generator[StreamEvent, None, None]:
        with zipfile.ZipFile(self.path) as echo_file_zip:
            assert len(echo_file_zip.namelist()) == 1, echo_file_zip.namelist()
            with echo_file_zip.open(echo_file_zip.namelist()[0]) as echo_file:
                for line in echo_file:
                    event_time, data = line.decode().split("\t")
                    yield StreamEvent(data=data, datetime=event_time)
