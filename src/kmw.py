# KAFKA PYTHON MIDDLEWARE
# An abstraction layer to ease communication of whatever component with Kafka
#
# Author: Miguel Neto

import asyncio

from typing import List, Iterable

from kafka import KafkaConsumer, KafkaProducer

class KMiddleware():
    def __init__(self, hostname: str, port: str, *topics):
        self._hostname = hostname
        self._port = port
        self._topics = set(topics)

    def add_topic(self, topic: str) -> None:
        self._topics.add(topic)

    def add_topics(self, topics: Iterable) -> None:
        self._topics.update(topics)

    # FIXME: produce must not be continuously run but actually run when needed to cast le intel to le kafka

    def start(self):

        self.consumers = dict()
        for topic in topics:
            self.consumers[topic] = KafkaConsumer(topic)
        asyncio.run(self._run())

    async def _run(self):
        kconsumer = asyncio.create_task(self.consume())
        # kproducer = asyncio.create_task(self.produce())
        await asyncio.gather(kconsumer)

    async def consume(self, idx=-1):
        raise NotImplementedError

    async def produce(self):
        raise NotImplementedError
