from abc import ABC
from abc import abstractmethod
from contextlib import AbstractContextManager
from typing import Callable
from typing import Iterable
from typing import Type

from echostats.models import ConsumerEvent
from plotly.graph_objects import Figure as PlotlyFigure


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
