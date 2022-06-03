from . import BaseConsumer
from ..models import ConsumerEvent


class DebuggerConsumer(BaseConsumer):
    def consume(self, event: ConsumerEvent) -> None:
        print(repr(event.echo_event))
