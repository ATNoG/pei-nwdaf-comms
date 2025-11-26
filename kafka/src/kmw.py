# KAFKA PYTHON BRIDGE
# An abstraction layer to ease communication of whichever component with Kafka
#
# Author: Miguel Neto

import asyncio

from typing import List, Iterable, Optional, TypedDict
import logging
from collections.abc import Callable

import re

from kafka import KafkaConsumer, KafkaProducer, TopicPartition
from kafka.cluster import ClusterMetadata
from kafka.errors import KafkaTimeoutError

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
                    datefmt="%m-%d %H:%M:%S",
                    handlers=[
                        # logging.FileHandler(f"./logs/student_{datetime.datetime.now().strftime("%d_%m_%y_at_%H_%M_%S")}.log"),
                        logging.StreamHandler()
                    ])

# Noisy logs begone!
kafka_loggers = ['kafka', 'kafka.producer', 'kafka.consumer', 'kafka.conn',
                 'kafka.protocol', 'kafka.client', 'kafka.cluster', 'kafka.coordinator',
                 'kafka.metrics', 'kafka.record', 'kafka.serializer', 'kafka.server',
                 'kafka.oauth', 'kafka.sasl']

for logger_name in kafka_loggers:
    kafka_logger = logging.getLogger(logger_name)
    kafka_logger.setLevel(logging.CRITICAL)  # Only show CRITICAL errors (practically nothing)
    kafka_logger.propagate = False  # Disable propagation to root logger

logger = logging.getLogger(__name__)

# TODO: Analyze whether multiprocessing would be a better choice
class PyKafBridge():
    def __init__(self, *topics, hostname: str = 'localhost', port: str = '9092', debug_label: str = 'PKB'):
        self._hostname = hostname
        self._port = port
        self._topics = set(topics)
        self.topic_binds = dict()
        self._consumer_data = {topic: list() for topic in self._topics}

        self._last_consumed = dict()

        # TODO: See if we use JSON or not (changes implementation slightly)
        boostrap_server = f'{self._hostname}:{self._port}'
        self.producer = KafkaProducer(bootstrap_servers=boostrap_server)
        self.consumer: Optional[KafkaConsumer] = None

        self._metadata = ClusterMetadata(bootstrap_servers=boostrap_server)

        self._consumer_task: Optional[asyncio.Task] = None
        self._running = False

        self._debug_label = debug_label

    def last_consumed(self, topic: str):
        if self._last_consumed.get(topic):
            return self._last_consumed[topic]
        return -1

    def add_topic_and_subtopic(self, parent: str):
        pat = f"\\.?{parent}(\\..*)?"
        if self.consumer:
            self.consumer.subscribe(pattern=pat)

        topic: str
        for topic in self._metadata.topics():
            if re.search(pat, topic):
                self._topics.add(topic)

    def bind_topic(self, topic: str, func: Callable):
        if self.topic_binds.get(topic):
            self.topic_binds[topic].append([func])
        else:
            self.topic_binds[topic] = [func]

    def add_topic(self, topic: str) -> None:
        if self.consumer:
            self.consumer.subscribe((topic,))

        self._topics.add(topic)
        self._consumer_data[topic] = list()

    def extend_topics(self, topics: Iterable) -> None:
        if self.consumer:
            self.consumer.subscribe(topics)

        self._topics.update(topics)
        for topic in topics:
            self._consumer_data[topic] = list()

    def metrics(self, topic=None) -> dict:
        """ Get consumer metrics """
        if not self.consumer:
            logger.warning("Consumer not initialized")
            return {}

        return self.consumer.metrics()

    async def _run(self):
        """ Deprecated """
        consumer_task = asyncio.create_task(self.consume())
        try:
            await consumer_task
        except KeyboardInterrupt:
            logger.info("Shutdown signal received: keyboard interrupt")
            self._running = False
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                logger.error("There was an error cancelling: asyncio.CancelledError")
            except e:
                logger.error(f"Fatal error: {e}")
        except e:
            logger.error(f"Fatal error: {e}")

    async def start(self) -> None:
        """ Initialize consumer and start the event loop. """
        if not self._topics:
            logger.warning("No topics to subscribe to")
            return

        bootstrap_servers = f'{self._hostname}:{self._port}'
        self.consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers)
        self.consumer.subscribe(tuple(self._topics))
        self._running = True

        self._consumer_task = asyncio.create_task(self.consume())

        logger.info(f"Started Kafka middleware, subscribed to: {self._topics}")

    async def stop(self) -> None:
        self._running = False

        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass

        if self.consumer:
            self.consumer.close()

        self.producer.close()
        logger.info("Stopping...")

    def get_topic(self, topic: str):
        data = self._consumer_data.get(topic)
        return data if data else {}

    # TODO:
    # EXTRA: offset behaviour must be tracked
    async def consume(self) -> None:
        """ Consume events from subscribed topics. (WIP) """
        if not self.consumer:
            logger.error("Consumer not initialized")
            return

        loop = asyncio.get_event_loop()

        try:
            while self._running:
                # Run blocking consumer poll in executor to avoid blocking event loop. #asyncioflex
                msg: dict = await loop.run_in_executor(None, self.consumer.poll, 1000)

                topic_part: TopicPartition
                for topic_part in msg.keys():
                    topic = topic_part.topic
                    for contents in msg[topic_part]:

                        data = {
                            'offset': contents.offset,
                            'content': contents.value.decode(),
                            'timestamp': contents.timestamp,
                        }

                        # Transform data with functions bound to that topic
                        if self.topic_binds.get(topic):
                            for func in self.topic_binds[topic]:
                                data = func(data)

                        self._consumer_data[topic].append(data)
                        self._last_consumed[topic] = data['offset']
                # logger.info(f"msg: {msg}")
                # logger.debug(f"data: {self._consumer_data}")

                await asyncio.sleep(0)

        except asyncio.CancelledError:
            logger.info("Consumer task cancelled")

    # TODO: Better traceback formatting
    #       May use transactions in specific cases
    def produce(self, topic: str, message: str) -> bool:
        """ Send an event. Using str for now for simplicity. Returns true on success """
        try:
            self.producer.send(topic, message.encode())
            logger.debug(f"Message sent to topic {topic}")
            return True
        except KafkaTimeoutError:
            logger.error(f"Failed to send to topic {topic}: timeout")
            return False
        except Exception as e:
            logger.error(f"Error sending to topic {topic}: {e}")
            return False


if __name__ == '__main__':
    async def main():
        pk1 = PyKafBridge('test-event')
        pk2 = PyKafBridge()

        await pk1.start()

        await asyncio.sleep(.5)

        pk2.produce('test-event', 'MESSAGE1')
        pk2.produce('test-event', 'MESSAGE2')

        def transform_message(data: dict):
            data['content'] = data['content'].lower()
            return data

        pk2.produce('test-event', 'MESSAGE3')

        await asyncio.sleep(1)

        pk1.bind_topic('test-event', transform_message)

        pk2.produce('test-event', 'MESSAGE4')
        pk2.produce('test-event', 'MESSAGE5')

        await asyncio.sleep(1)

        data = pk1.get_topic('test-event')

        for d in data:
            logger.debug(f'{d}')

        logger.debug(pk1.last_consumed('test-event'))

        await pk1.stop()
        await pk2.stop()

    asyncio.run(main())
