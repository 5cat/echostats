from abc import ABC
from abc import abstractmethod
from contextlib import AbstractContextManager
from typing import Callable
from typing import Iterable
from typing import Iterator
from typing import Type
from typing import TypeVar

import plotly.graph_objects as go
from echostats.models import ConsumerEvent
from typing_extensions import Self


class BaseConsumer(ABC):
    @abstractmethod
    def consume(self, event: ConsumerEvent) -> None:
        ...

    def get_context_managers(self) -> Iterable[AbstractContextManager]:
        return []


def consumer(func: Callable[[ConsumerEvent], None]) -> Type[BaseConsumer]:
    class Wrapped(BaseConsumer):
        def consume(self, event: ConsumerEvent) -> None:
            func(event)

    return Wrapped


class BaseGrapher(ABC):
    @abstractmethod
    def generate_figure(self) -> go.Figure:
        ...


ConsumerTypeVar = TypeVar("ConsumerTypeVar", bound=BaseConsumer)
from typing import Mapping


class ConsumerMapping(Mapping):
    def __init__(self, mapping):
        self.mapping = mapping

    def __getitem__(self, __k: Type[ConsumerTypeVar]) -> ConsumerTypeVar:
        return self.mapping[__k]

    def __len__(self) -> int:
        return len(self.mapping)

    def __iter__(self) -> Iterator[Type[ConsumerTypeVar]]:
        return iter(self.mapping)


class ConsumerDependent(ABC):
    @abstractmethod
    def get_dependencies(self) -> Iterable[Type[BaseConsumer]]:
        ...

    @abstractmethod
    def init(self, dependencies: ConsumerMapping) -> None:
        ...
