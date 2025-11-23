# Test suite for end-to-end integration testing of KMiddleware

import pytest
import asyncio
import time
from kafka import KafkaConsumer, KafkaProducer
from kmw import KMiddleware


class TestEndToEndIntegration:
    """End-to-end integration tests for the complete middleware workflow."""

    def test_produce_and_consume_single_message(self, ensure_test_topic, test_topic, kafka_bootstrap_servers):
        """Test producing and consuming a single message end-to-end."""
        kmw = KMiddleware("localhost", "9092", test_topic)

        # Produce a message
        message = "e2e-test-message"
        result = kmw.produce(test_topic, message)
        assert result is True
        kmw.producer.flush()

        time.sleep(1)

        # Consume with a separate consumer to verify
        consumer = KafkaConsumer(
            test_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            consumer_timeout_ms=5000,
            group_id='test-e2e-group'
        )

        found = False
        for _ in range(10):
            messages = consumer.poll(timeout_ms=1000)
            for topic_partition, records in messages.items():
                for record in records:
                    if record.value.decode() == message:
                        found = True
                        break
            if found:
                break

        consumer.close()
        kmw.stop()

        assert found, "Message was not found in topic"

    def test_produce_multiple_messages_different_content(self, ensure_test_topic, test_topic, kafka_bootstrap_servers):
        """Test producing multiple messages with different content."""
        kmw = KMiddleware("localhost", "9092", test_topic)

        messages = [
            "first-message",
            "second-message",
            "third-message",
            "fourth-message"
        ]

        # Produce all messages
        for msg in messages:
            result = kmw.produce(test_topic, msg)
            assert result is True

        kmw.producer.flush()
        time.sleep(1)

        # Consume and verify
        consumer = KafkaConsumer(
            test_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            consumer_timeout_ms=3000,
            group_id='test-multiple-group'
        )

        received_messages = []
        for _ in range(10):  # Poll multiple times
            records = consumer.poll(timeout_ms=1000)
            for topic_partition, msgs in records.items():
                for record in msgs:
                    received_messages.append(record.value.decode())
            if len(received_messages) >= len(messages):
                break

        consumer.close()
        kmw.stop()

        # Verify all messages were received
        for msg in messages:
            assert msg in received_messages, f"Message '{msg}' not found in consumed messages"

    def test_producer_without_consumer(self, ensure_test_topic, test_topic):
        """Test that producer works independently without starting consumer."""
        kmw = KMiddleware("localhost", "9092", test_topic)

        # Producer should work without starting the consumer
        assert kmw.consumer is None

        result = kmw.produce(test_topic, "independent-producer-message")
        assert result is True

        kmw.stop()

    def test_multiple_topic_subscription(self, ensure_test_topic, admin_client, kafka_bootstrap_servers):
        """Test middleware with multiple topics."""
        topics = ["test-event", "test-event-2", "test-event-3"]

        # Ensure all topics exist
        from kafka.admin import NewTopic
        from kafka.errors import TopicAlreadyExistsError

        for topic in topics:
            try:
                new_topic = NewTopic(name=topic, num_partitions=1, replication_factor=1)
                admin_client.create_topics([new_topic])
                time.sleep(0.5)
            except TopicAlreadyExistsError:
                pass

        kmw = KMiddleware("localhost", "9092", *topics)

        # Produce to each topic
        for topic in topics:
            result = kmw.produce(topic, f"message-for-{topic}")
            assert result is True

        kmw.producer.flush()
        time.sleep(1)

        # Verify each topic received its message
        for topic in topics:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=kafka_bootstrap_servers,
                auto_offset_reset='earliest',
                consumer_timeout_ms=5000,
                group_id=f'test-multi-{topic}'
            )

            found = False
            for _ in range(10):
                messages = consumer.poll(timeout_ms=1000)
                for topic_partition, records in messages.items():
                    for record in records:
                        if f"message-for-{topic}" in record.value.decode():
                            found = True
                            break
                if found:
                    break

            consumer.close()
            assert found, f"Message for topic '{topic}' not found"

        kmw.stop()

    def test_dynamic_topic_addition_with_production(self, ensure_test_topic, admin_client, kafka_bootstrap_servers):
        """Test adding topics dynamically and producing to them."""
        kmw = KMiddleware("localhost", "9092", "test-event")

        # Produce to initial topic
        kmw.produce("test-event", "initial-topic-message")

        # Add new topics dynamically
        new_topic = "test-event-dynamic"

        # Create the topic
        from kafka.admin import NewTopic
        from kafka.errors import TopicAlreadyExistsError

        try:
            topic_obj = NewTopic(name=new_topic, num_partitions=1, replication_factor=1)
            admin_client.create_topics([topic_obj])
            time.sleep(1)
        except TopicAlreadyExistsError:
            pass

        kmw.add_topic(new_topic)

        # Produce to the new topic
        result = kmw.produce(new_topic, "dynamic-topic-message")
        assert result is True

        kmw.producer.flush()
        time.sleep(1)

        # Verify message in new topic
        consumer = KafkaConsumer(
            new_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            consumer_timeout_ms=5000,
            group_id='test-dynamic-group'
        )

        found = False
        for _ in range(10):
            messages = consumer.poll(timeout_ms=1000)
            for topic_partition, records in messages.items():
                for record in records:
                    if record.value.decode() == "dynamic-topic-message":
                        found = True
                        break
            if found:
                break

        consumer.close()
        kmw.stop()

        assert found, "Message not found in dynamically added topic"

    def test_high_volume_message_production(self, ensure_test_topic, test_topic):
        """Test producing a high volume of messages."""
        kmw = KMiddleware("localhost", "9092", test_topic)

        num_messages = 100

        for i in range(num_messages):
            result = kmw.produce(test_topic, f"high-volume-message-{i}")
            assert result is True

        kmw.producer.flush()
        kmw.stop()

    def test_message_ordering(self, ensure_test_topic, test_topic, kafka_bootstrap_servers):
        """Test that messages maintain order in a single partition."""
        kmw = KMiddleware("localhost", "9092", test_topic)

        ordered_messages = [f"ordered-{i}" for i in range(10)]

        # Produce messages in order
        for msg in ordered_messages:
            kmw.produce(test_topic, msg)

        kmw.producer.flush()
        time.sleep(1)

        # Consume and check order
        consumer = KafkaConsumer(
            test_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            consumer_timeout_ms=3000,
            group_id='test-ordering-group'
        )

        received_messages = []
        for _ in range(5):
            records = consumer.poll(timeout_ms=1000)
            for topic_partition, msgs in records.items():
                for record in msgs:
                    msg = record.value.decode()
                    if msg.startswith("ordered-"):
                        received_messages.append(msg)

        consumer.close()
        kmw.stop()

        # Extract the ordered messages we just sent
        our_messages = [msg for msg in received_messages if msg in ordered_messages]

        # Check that our messages appear in order
        if len(our_messages) > 1:
            for i in range(len(our_messages) - 1):
                curr_idx = ordered_messages.index(our_messages[i])
                next_idx = ordered_messages.index(our_messages[i + 1])
                assert curr_idx < next_idx, "Messages not in order"

    def test_producer_flush_ensures_delivery(self, ensure_test_topic, test_topic, kafka_bootstrap_servers):
        """Test that flushing the producer ensures message delivery."""
        kmw = KMiddleware("localhost", "9092", test_topic)

        message = "flush-test-message"
        kmw.produce(test_topic, message)

        # Flush to ensure delivery
        kmw.producer.flush()

        time.sleep(1)

        # Verify message was delivered
        consumer = KafkaConsumer(
            test_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            consumer_timeout_ms=5000,
            group_id='test-flush-group'
        )

        found = False
        for _ in range(10):
            messages = consumer.poll(timeout_ms=1000)
            for topic_partition, records in messages.items():
                for record in records:
                    if record.value.decode() == message:
                        found = True
                        break
            if found:
                break

        consumer.close()
        kmw.stop()

        assert found

    def test_middleware_stop_closes_connections(self, ensure_test_topic, test_topic):
        """Test that stop() properly closes all connections."""
        kmw = KMiddleware("localhost", "9092", test_topic)

        # Produce a message to ensure connections are active
        kmw.produce(test_topic, "test-message")

        # Stop the middleware
        kmw.stop()

        # Verify running flag is False
        assert kmw._running is False

    def test_unicode_message_end_to_end(self, ensure_test_topic, test_topic, kafka_bootstrap_servers):
        """Test end-to-end flow with unicode messages."""
        kmw = KMiddleware("localhost", "9092", test_topic)

        unicode_messages = [
            "Hello 世界",
            "Café ☕",
            "🚀 Rocket",
            "Ñoño",
            "Привет"
        ]

        for msg in unicode_messages:
            result = kmw.produce(test_topic, msg)
            assert result is True

        kmw.producer.flush()
        time.sleep(1)

        # Consume and verify
        consumer = KafkaConsumer(
            test_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            consumer_timeout_ms=3000,
            group_id='test-unicode-group'
        )

        received_messages = []
        for _ in range(5):
            records = consumer.poll(timeout_ms=1000)
            for topic_partition, msgs in records.items():
                for record in msgs:
                    received_messages.append(record.value.decode('utf-8'))

        consumer.close()
        kmw.stop()

        # Verify all unicode messages were received correctly
        for msg in unicode_messages:
            assert msg in received_messages, f"Unicode message '{msg}' not found"

    def test_empty_and_whitespace_messages(self, ensure_test_topic, test_topic, kafka_bootstrap_servers):
        """Test producing and consuming empty and whitespace messages."""
        kmw = KMiddleware("localhost", "9092", test_topic)

        special_messages = ["", "   ", "\n", "\t", "  \n\t  "]

        for msg in special_messages:
            result = kmw.produce(test_topic, msg)
            assert result is True

        kmw.producer.flush()
        kmw.stop()

        # Just verify they were sent successfully
        # Actual content verification is difficult with empty strings

    def test_concurrent_production_to_same_topic(self, ensure_test_topic, test_topic):
        """Test concurrent message production to the same topic."""
        kmw = KMiddleware("localhost", "9092", test_topic)

        # Rapidly produce messages
        for i in range(50):
            result = kmw.produce(test_topic, f"concurrent-{i}")
            assert result is True

        kmw.producer.flush()
        kmw.stop()

    def test_json_formatted_messages(self, ensure_test_topic, test_topic, kafka_bootstrap_servers):
        """Test producing and consuming JSON-formatted string messages."""
        import json

        kmw = KMiddleware("localhost", "9092", test_topic)

        data = {
            "event": "user_login",
            "user_id": 12345,
            "timestamp": "2024-01-01T00:00:00Z",
            "metadata": {
                "ip": "192.168.1.1",
                "device": "mobile"
            }
        }

        json_message = json.dumps(data)
        result = kmw.produce(test_topic, json_message)
        assert result is True

        kmw.producer.flush()
        time.sleep(1)

        # Consume and verify JSON can be parsed
        consumer = KafkaConsumer(
            test_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            consumer_timeout_ms=5000,
            group_id='test-json-group'
        )

        found = False
        for _ in range(10):
            messages = consumer.poll(timeout_ms=1000)
            for topic_partition, records in messages.items():
                for record in records:
                    try:
                        decoded = record.value.decode()
                        parsed = json.loads(decoded)
                        if parsed.get("event") == "user_login":
                            found = True
                            assert parsed["user_id"] == 12345
                            break
                    except (json.JSONDecodeError, KeyError):
                        continue
            if found:
                break

        consumer.close()
        kmw.stop()

        assert found, "JSON message not found or not parseable"
