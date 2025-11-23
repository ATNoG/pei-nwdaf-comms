# Test suite for KMiddleware producer functionality

import pytest
import time
from kafka import KafkaConsumer
from kafka.errors import KafkaTimeoutError
from kmw import KMiddleware


class TestProducer:
    """Test cases for KMiddleware message production."""

    def test_produce_message_to_topic(self, kmiddleware, ensure_test_topic, test_topic, kafka_bootstrap_servers):
        """Test producing a message to a topic."""
        kmw = kmiddleware
        message = "Hello, Kafka!"

        result = kmw.produce(test_topic, message)
        assert result is True
        kmw.producer.flush()

        time.sleep(1)  # Give Kafka time to propagate

        # Create a fresh consumer starting from earliest
        consumer = KafkaConsumer(
            test_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            consumer_timeout_ms=5000,
            group_id='test-produce-message-group'
        )

        # Poll for messages
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
        assert found, "Message not found in topic"

    def test_produce_multiple_messages(self, kmiddleware, ensure_test_topic, test_topic, kafka_bootstrap_servers):
        """Test producing multiple messages to a topic."""
        kmw = kmiddleware
        messages = ["message1", "message2", "message3"]

        for msg in messages:
            result = kmw.produce(test_topic, msg)
            assert result is True

        kmw.producer.flush()
        time.sleep(1)

        # Create fresh consumer
        consumer = KafkaConsumer(
            test_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            consumer_timeout_ms=5000,
            group_id='test-multiple-messages-group'
        )

        received_messages = []
        for _ in range(10):
            records = consumer.poll(timeout_ms=1000)
            for topic_partition, msgs in records.items():
                for record in msgs:
                    received_messages.append(record.value.decode())

        consumer.close()

        for msg in messages:
            assert msg in received_messages

    def test_produce_empty_message(self, kmiddleware, ensure_test_topic, test_topic):
        """Test producing an empty message."""
        kmw = kmiddleware

        result = kmw.produce(test_topic, "")

        assert result is True

    def test_produce_special_characters(self, kmiddleware, ensure_test_topic, test_topic, kafka_bootstrap_servers):
        """Test producing messages with special characters."""
        kmw = kmiddleware
        special_message = "Special chars: !@#$%^&*()_+-=[]{}|;:',.<>?/~`"

        result = kmw.produce(test_topic, special_message)
        assert result is True
        kmw.producer.flush()

        time.sleep(1)

        consumer = KafkaConsumer(
            test_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            consumer_timeout_ms=5000,
            group_id='test-special-chars-group'
        )

        found = False
        for _ in range(10):
            messages = consumer.poll(timeout_ms=1000)
            for topic_partition, records in messages.items():
                for record in records:
                    if record.value.decode() == special_message:
                        found = True
                        break
            if found:
                break

        consumer.close()
        assert found, "Special character message not found"

    def test_produce_unicode_message(self, kmiddleware, ensure_test_topic, test_topic, kafka_bootstrap_servers):
        """Test producing messages with unicode characters."""
        kmw = kmiddleware
        unicode_message = "Hello 世界 🌍 café"

        result = kmw.produce(test_topic, unicode_message)
        assert result is True
        kmw.producer.flush()

        time.sleep(1)

        consumer = KafkaConsumer(
            test_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            consumer_timeout_ms=5000,
            group_id='test-unicode-group'
        )

        found = False
        for _ in range(10):
            messages = consumer.poll(timeout_ms=1000)
            for topic_partition, records in messages.items():
                for record in records:
                    if record.value.decode() == unicode_message:
                        found = True
                        break
            if found:
                break

        consumer.close()
        assert found, "Unicode message not found"

    def test_produce_long_message(self, kmiddleware, ensure_test_topic, test_topic):
        """Test producing a very long message."""
        kmw = kmiddleware
        long_message = "A" * 10000  # 10KB message

        result = kmw.produce(test_topic, long_message)

        assert result is True

    def test_produce_to_nonexistent_topic(self, kmiddleware):
        """Test producing to a topic that doesn't exist (should auto-create or handle gracefully)."""
        kmw = kmiddleware

        # Kafka auto-creates topics by default, so this should succeed
        result = kmw.produce("nonexistent-topic-12345", "test message")

        # Should return True even for auto-created topics
        assert result is True

    def test_produce_returns_true_on_success(self, kmiddleware, ensure_test_topic, test_topic):
        """Test that produce returns True on successful send."""
        kmw = kmiddleware

        result = kmw.produce(test_topic, "success test")

        assert isinstance(result, bool)
        assert result is True

    def test_producer_encoding(self, kmiddleware, ensure_test_topic, test_topic, kafka_bootstrap_servers):
        """Test that messages are properly encoded as bytes."""
        kmw = kmiddleware
        message = "encoding test"

        kmw.produce(test_topic, message)
        kmw.producer.flush()

        time.sleep(1)

        consumer = KafkaConsumer(
            test_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            consumer_timeout_ms=5000,
            group_id='test-encoding-group'
        )

        found = False
        for _ in range(10):
            messages = consumer.poll(timeout_ms=1000)
            for topic_partition, records in messages.items():
                for record in records:
                    if record.value.decode() == message:
                        assert isinstance(record.value, bytes)
                        found = True
                        break
            if found:
                break

        consumer.close()
        assert found, "Message not found for encoding test"

    def test_rapid_message_production(self, kmiddleware, ensure_test_topic, test_topic):
        """Test rapid sequential message production."""
        kmw = kmiddleware

        num_messages = 50
        for i in range(num_messages):
            result = kmw.produce(test_topic, f"rapid-message-{i}")
            assert result is True

    def test_produce_newline_characters(self, kmiddleware, ensure_test_topic, test_topic, kafka_bootstrap_servers):
        """Test producing messages with newline characters."""
        kmw = kmiddleware
        multiline_message = "Line 1\nLine 2\nLine 3"

        result = kmw.produce(test_topic, multiline_message)
        assert result is True
        kmw.producer.flush()

        time.sleep(1)

        consumer = KafkaConsumer(
            test_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            consumer_timeout_ms=5000,
            group_id='test-newline-group'
        )

        found = False
        for _ in range(10):
            messages = consumer.poll(timeout_ms=1000)
            for topic_partition, records in messages.items():
                for record in records:
                    decoded = record.value.decode()
                    if decoded == multiline_message:
                        assert "\n" in decoded
                        found = True
                        break
            if found:
                break

        consumer.close()
        assert found, "Multiline message not found"

    def test_produce_json_like_string(self, kmiddleware, ensure_test_topic, test_topic, kafka_bootstrap_servers):
        """Test producing JSON-formatted strings."""
        kmw = kmiddleware
        json_message = '{"key": "value", "number": 42, "nested": {"inner": "data"}}'

        result = kmw.produce(test_topic, json_message)
        assert result is True
        kmw.producer.flush()

        time.sleep(1)

        consumer = KafkaConsumer(
            test_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            consumer_timeout_ms=5000,
            group_id='test-json-string-group'
        )

        found = False
        for _ in range(10):
            messages = consumer.poll(timeout_ms=1000)
            for topic_partition, records in messages.items():
                for record in records:
                    decoded = record.value.decode()
                    if decoded == json_message:
                        found = True
                        break
            if found:
                break

        consumer.close()
        assert found, "JSON message not found"

    def test_produce_numeric_strings(self, kmiddleware, ensure_test_topic, test_topic):
        """Test producing numeric strings."""
        kmw = kmiddleware

        numeric_messages = ["123", "456.789", "-999", "0"]

        for msg in numeric_messages:
            result = kmw.produce(test_topic, msg)
            assert result is True

    def test_producer_exists_after_init(self, kmiddleware):
        """Test that producer is available after middleware initialization."""
        kmw = kmiddleware

        assert kmw.producer is not None
        assert hasattr(kmw.producer, 'send')
        assert hasattr(kmw.producer, 'close')
