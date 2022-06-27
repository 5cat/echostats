from echostats._abc import BaseConsumer
from echostats.models import ConsumerEvent


class DebuggerConsumer(BaseConsumer):
    def consume(self, event: ConsumerEvent) -> None:
        print(repr(event.echo_event))
