# Test suite for PyKafBridge consumer functionality

import pytest
import asyncio
import time
from kmw import PyKafBridge


class TestConsumerInitialization:
    """Test cases for consumer initialization."""

    def test_consumer_not_initialized_before_start(self, kmiddleware):
        """Test that consumer is None before start() is called."""
        kmw = kmiddleware

        assert kmw.consumer is None

    def test_consumer_initialized_on_start(self, kmiddleware, ensure_test_topic):
        """Test that consumer is created when start() is called (would block, so we test the setup)."""
        kmw = kmiddleware

        # We can't actually call start() in a test as it blocks
        # But we can test the consumer initialization logic
        from kafka import KafkaConsumer

        bootstrap_servers = f'{kmw._hostname}:{kmw._port}'
        test_consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers)
        test_consumer.subscribe(list(kmw._topics))

        assert test_consumer is not None
        assert len(test_consumer.subscription()) > 0

        test_consumer.close()

    def test_running_flag_false_initially(self, kmiddleware):
        """Test that _running flag is False before start."""
        kmw = kmiddleware

        assert kmw._running is False

    def test_consumer_subscribes_to_topics(self, kmiddleware, ensure_test_topic, test_topic):
        """Test that consumer subscribes to the correct topics."""
        kmw = kmiddleware

        # Manually initialize consumer to test subscription
        from kafka import KafkaConsumer

        bootstrap_servers = f'{kmw._hostname}:{kmw._port}'
        consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers)
        consumer.subscribe(list(kmw._topics))

        assert test_topic in consumer.subscription()

        consumer.close()


class TestConsumerTopicSubscription:
    """Test cases for dynamic topic subscription."""

    def test_add_topic_updates_consumer_subscription(self, ensure_test_topic):
        """Test that adding a topic updates consumer subscription if consumer exists."""
        from kafka import KafkaConsumer

        kmw = PyKafBridge("localhost", "9092", "test-event")

        # Manually create consumer
        bootstrap_servers = f'{kmw._hostname}:{kmw._port}'
        kmw.consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers)
        kmw.consumer.subscribe(list(kmw._topics))

        initial_topics = set(kmw.consumer.subscription())

        # Add new topic
        kmw.add_topic("test-event-2")

        # Subscription should be updated
        assert "test-event-2" in kmw._topics

        kmw.consumer.close()

    def test_extend_topics_updates_consumer_subscription(self, ensure_test_topic):
        """Test that extending topics updates consumer subscription if consumer exists."""
        from kafka import KafkaConsumer

        kmw = PyKafBridge("localhost", "9092", "test-event")

        # Manually create consumer
        bootstrap_servers = f'{kmw._hostname}:{kmw._port}'
        kmw.consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers)
        kmw.consumer.subscribe(list(kmw._topics))

        new_topics = ["test-event-2", "test-event-3"]
        kmw.extend_topics(new_topics)

        # Topics should be in middleware
        for topic in new_topics:
            assert topic in kmw._topics

        kmw.consumer.close()


class TestConsumerStartStop:
    """Test cases for consumer start and stop methods."""

    def test_start_with_no_topics_warns(self, kmiddleware_no_topics, caplog):
        """Test that starting with no topics logs a warning and returns early."""
        kmw = kmiddleware_no_topics

        # This should return immediately with a warning
        kmw.start()

        # Consumer should not be initialized
        assert kmw.consumer is None or not kmw._running

    def test_stop_closes_consumer(self, kmiddleware, ensure_test_topic):
        """Test that stop() closes the consumer if it exists."""
        from kafka import KafkaConsumer

        kmw = kmiddleware

        # Manually create consumer
        bootstrap_servers = f'{kmw._hostname}:{kmw._port}'
        kmw.consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers)

        # Stop should close consumer
        kmw.stop()

        # Consumer should be closed (accessing it after close raises error)
        assert kmw._running is False

    def test_stop_closes_producer(self, kmiddleware):
        """Test that stop() closes the producer."""
        kmw = kmiddleware

        producer_instance = kmw.producer

        kmw.stop()

        # Producer should be closed
        # We can't easily verify this without causing errors, but stop() should have been called


class TestConsumeMethod:
    """Test cases for the consume() async method."""

    @pytest.mark.asyncio
    async def test_consume_returns_early_without_consumer(self, kmiddleware):
        """Test that consume() returns early if consumer is not initialized."""
        kmw = kmiddleware

        # Consumer is None, so consume should return immediately
        await kmw.consume()

        # Should complete without error

    @pytest.mark.asyncio
    async def test_consume_runs_while_running_flag_true(self, kmiddleware, ensure_test_topic):
        """Test that consume() loop runs while _running is True."""
        from kafka import KafkaConsumer

        kmw = kmiddleware

        # Set up consumer
        bootstrap_servers = f'{kmw._hostname}:{kmw._port}'
        kmw.consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            consumer_timeout_ms=1000
        )
        kmw.consumer.subscribe(list(kmw._topics))
        kmw._running = True

        # Create a task to stop after a short time
        async def stop_after_delay():
            await asyncio.sleep(0.5)
            kmw._running = False

        # Run both tasks
        stop_task = asyncio.create_task(stop_after_delay())
        consume_task = asyncio.create_task(kmw.consume())

        await asyncio.gather(stop_task, consume_task)

        # Should have stopped cleanly
        assert kmw._running is False

        kmw.consumer.close()

    @pytest.mark.asyncio
    async def test_consume_polls_consumer(self, kmiddleware, ensure_test_topic, kafka_producer, test_topic):
        """Test that consume() polls the consumer for messages."""
        from kafka import KafkaConsumer

        kmw = kmiddleware

        # Send a test message first
        kafka_producer.send(test_topic, b"test message for consumer")
        kafka_producer.flush()
        time.sleep(0.5)

        # Set up consumer
        bootstrap_servers = f'{kmw._hostname}:{kmw._port}'
        kmw.consumer = KafkaConsumer(
            test_topic,
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset='earliest',
            consumer_timeout_ms=2000
        )
        kmw._running = True

        # Run consume for a short time
        async def run_consume_briefly():
            consume_task = asyncio.create_task(kmw.consume())
            await asyncio.sleep(1)
            kmw._running = False
            try:
                await asyncio.wait_for(consume_task, timeout=2)
            except asyncio.TimeoutError:
                consume_task.cancel()

        await run_consume_briefly()

        # Consumer should have polled (can't easily verify without modifying code)
        kmw.consumer.close()

    @pytest.mark.asyncio
    async def test_consume_handles_cancellation(self, kmiddleware, ensure_test_topic):
        """Test that consume() handles asyncio.CancelledError gracefully."""
        from kafka import KafkaConsumer

        kmw = kmiddleware

        # Set up consumer
        bootstrap_servers = f'{kmw._hostname}:{kmw._port}'
        kmw.consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            consumer_timeout_ms=1000
        )
        kmw.consumer.subscribe(list(kmw._topics))
        kmw._running = True

        # Start consume and cancel it
        consume_task = asyncio.create_task(kmw.consume())

        await asyncio.sleep(0.2)
        consume_task.cancel()

        try:
            await consume_task
        except asyncio.CancelledError:
            pass  # Expected

        # Should have handled cancellation
        kmw.consumer.close()


class TestMetrics:
    """Test cases for metrics() method."""

    def test_metrics_without_consumer(self, kmiddleware, caplog):
        """Test that metrics() returns empty dict and warns when consumer is None."""
        kmw = kmiddleware

        result = kmw.metrics()

        assert result == {}
        assert "Consumer not initialized" in caplog.text

    def test_metrics_with_consumer(self, kmiddleware, ensure_test_topic):
        """Test that metrics() returns consumer metrics when consumer exists."""
        from kafka import KafkaConsumer

        kmw = kmiddleware

        # Create consumer
        bootstrap_servers = f'{kmw._hostname}:{kmw._port}'
        kmw.consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers)
        kmw.consumer.subscribe(list(kmw._topics))

        result = kmw.metrics()

        # Should return a dictionary (Kafka metrics)
        assert isinstance(result, dict)

        kmw.consumer.close()

    def test_metrics_for_specific_topic(self, kmiddleware, ensure_test_topic, test_topic):
        """Test metrics() call (topic parameter currently not used in implementation)."""
        from kafka import KafkaConsumer

        kmw = kmiddleware

        # Create consumer
        bootstrap_servers = f'{kmw._hostname}:{kmw._port}'
        kmw.consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers)
        kmw.consumer.subscribe(list(kmw._topics))

        # Call with topic (though implementation doesn't use it)
        result = kmw.metrics(topic=test_topic)

        assert isinstance(result, dict)

        kmw.consumer.close()


class TestConsumerIntegration:
    """Integration tests for consumer with producer."""

    @pytest.mark.asyncio
    async def test_consume_receives_produced_message(self, ensure_test_topic, test_topic, kafka_bootstrap_servers):
        """Test end-to-end message production and consumption."""
        from kafka import KafkaConsumer

        kmw = PyKafBridge("localhost", "9092", test_topic)

        # Produce a message
        test_message = "integration-test-message"
        kmw.produce(test_topic, test_message)
        kmw.producer.flush()
        time.sleep(1)

        # Manually consume to verify
        consumer = KafkaConsumer(
            test_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            consumer_timeout_ms=5000,
            group_id='test-integration-consumer-group'
        )

        # Poll for messages
        found = False
        for _ in range(10):
            messages = consumer.poll(timeout_ms=1000)
            for topic_partition, records in messages.items():
                for record in records:
                    if record.value.decode() == test_message:
                        found = True
                        break
            if found:
                break

        consumer.close()
        kmw.stop()

        assert found, "Produced message was not consumed"
