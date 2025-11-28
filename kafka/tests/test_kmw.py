import pytest
import asyncio
from src.kmw import PyKafBridge


@pytest.mark.asyncio
async def test_single_consumer_single_producer():
    """Test basic message consumption with one consumer and one producer"""
    consumer = PyKafBridge('test-event')
    producer = PyKafBridge()

    try:
        await consumer.start_consumer()  # Blocks until ready

        # Produce messages
        producer.produce('test-event', 'TEST_MESSAGE_1')
        producer.produce('test-event', 'TEST_MESSAGE_2')
        producer.produce('test-event', 'TEST_MESSAGE_3')

        await asyncio.sleep(1)  # Wait for consumption

        # Verify messages were consumed
        data = consumer.get_topic('test-event')
        assert len(data) == 3
        assert data[0]['content'] == 'TEST_MESSAGE_1'
        assert data[1]['content'] == 'TEST_MESSAGE_2'
        assert data[2]['content'] == 'TEST_MESSAGE_3'
        assert consumer.last_consumed('test-event') >= 0

    finally:
        producer.producer.flush()
        await consumer.close()


@pytest.mark.asyncio
async def test_multiple_consumers_single_producer():
    """Test that multiple consumers in different groups receive the same messages"""
    consumer1 = PyKafBridge('test-event')
    consumer2 = PyKafBridge('test-event')
    producer = PyKafBridge()

    try:
        await consumer1.start_consumer()  # Blocks until ready
        await consumer2.start_consumer()  # Blocks until ready

        # Produce messages
        producer.produce('test-event', 'MULTI_CONSUMER_1')
        producer.produce('test-event', 'MULTI_CONSUMER_2')

        await asyncio.sleep(1)  # Wait for consumption

        # Both consumers should receive all messages (different consumer groups)
        data1 = consumer1.get_topic('test-event')
        data2 = consumer2.get_topic('test-event')

        assert len(data1) == 2
        assert len(data2) == 2
        assert data1[0]['content'] == 'MULTI_CONSUMER_1'
        assert data2[0]['content'] == 'MULTI_CONSUMER_1'

    finally:
        producer.producer.flush()
        await consumer1.close()
        await consumer2.close()


@pytest.mark.asyncio
async def test_topic_binding_transformation():
    """Test that topic bindings correctly transform messages"""
    consumer = PyKafBridge('test-event')
    producer = PyKafBridge()

    def uppercase_transform(data: dict):
        data['content'] = data['content'].upper()
        return data

    try:
        consumer.bind_topic('test-event', uppercase_transform)
        await consumer.start_consumer()  # Blocks until ready

        # Produce lowercase messages
        producer.produce('test-event', 'lowercase_message')

        await asyncio.sleep(1)  # Wait for consumption

        # Verify transformation was applied
        data = consumer.get_topic('test-event')
        assert len(data) == 1
        assert data[0]['content'] == 'LOWERCASE_MESSAGE'

    finally:
        producer.producer.flush()
        await consumer.close()


@pytest.mark.asyncio
async def test_multiple_producers_single_consumer():
    """Test single consumer receiving from multiple producers"""
    consumer = PyKafBridge('test-event')
    producer1 = PyKafBridge()
    producer2 = PyKafBridge()

    try:
        await consumer.start_consumer()  # Blocks until ready

        # Produce from different producers
        producer1.produce('test-event', 'FROM_PRODUCER_1')
        producer2.produce('test-event', 'FROM_PRODUCER_2')
        producer1.produce('test-event', 'FROM_PRODUCER_1_AGAIN')

        await asyncio.sleep(1)  # Wait for consumption

        # Verify all messages were consumed
        data = consumer.get_topic('test-event')
        assert len(data) == 3

        # Check messages are present (order might vary)
        contents = [d['content'] for d in data]
        assert 'FROM_PRODUCER_1' in contents
        assert 'FROM_PRODUCER_2' in contents
        assert 'FROM_PRODUCER_1_AGAIN' in contents

    finally:
        producer1.producer.flush()
        producer2.producer.flush()
        await consumer.close()
