# KAFKA PYTHON MIDDLEWARE
# An abstraction layer to ease communication of whatever component with Kafka
#
# Author: Miguel Neto

import asyncio

from typing import List, Iterable, Optional
import logging

from kafka import KafkaConsumer, KafkaProducer

from kafka.errors import KafkaTimeoutError

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
                    datefmt="%m-%d %H:%M:%S",
                    handlers=[
                        # logging.FileHandler(f"./logs/student_{datetime.datetime.now().strftime("%d_%m_%y_at_%H_%M_%S")}.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

# TODO: Analyze whether multiprocessing would be a better choice
class PyKafBridge():
    def __init__(self, hostname: str, port: str, *topics):
        self._hostname = hostname
        self._port = port
        self._topics = set(topics)
        self._consumer_data = {topic: frozenset() for topic in self._topics}

        # TODO: See if we use JSON or not (changes implementation slightly)
        self.producer = KafkaProducer(bootstrap_servers=f'{self._hostname}:{self._port}')
        self.consumer: Optional[KafkaConsumer] = None

        self._running = False

    def add_topic(self, topic: str) -> None:
        if self.consumer:
            self.consumer.subscribe((topic,))

        self._topics.add(topic)
        self._consumer_data[topic] = frozenset()

    def extend_topics(self, topics: Iterable) -> None:
        if self.consumer:
            self.consumer.subscribe(topics)

        self._topics.update(topics)
        for topic in topics:
            self._consumer_data[topic] = frozenset()

    def metrics(self, topic=None) -> dict:
        """ Get consumer metrics """
        if not self.consumer:
            logger.warning("Consumer not initialized")
            return {}

        return self.consumer.metrics()

    async def _run(self):
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
                pass

    def start(self) -> None:
        """ Initialize consumer and start the event loop. """
        if not self._topics:
            logger.warning("No topics to subscribe to")
            return

        bootstrap_servers = f'{self._hostname}:{self._port}'
        self.consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers)
        self.consumer.subscribe(list(self._topics))
        self._running = True

        logger.info(f"Starting Kafka middleware, subscribed to: {self._topics}")
        asyncio.run(self._run())

    def stop(self) -> None:
        self._running = False

        if self.consumer:
            self.consumer.close()

        self.producer.close()
        logger.info("Stopping...")

    # TODO:
    async def consume(self) -> None:
        """ Consume events from subscribed topics. (WIP) """
        if not self.consumer:
            logger.error("Consumer not initialized")
            return

        loop = asyncio.get_event_loop()

        try:
            while self._running:
                # Run blocking consumer poll in executor to avoid blocking event loop. #asyncioflex
                msg = await loop.run_in_executor(None, self.consumer.poll, 1000)

                logger.debug(f"msg: {msg}")

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
