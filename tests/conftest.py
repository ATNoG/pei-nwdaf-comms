# Pytest configuration and shared fixtures for Kafka middleware tests

import pytest
import time
from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError
import sys
import os

from src.kmw import KMiddleware

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture(scope="session")
def kafka_bootstrap_servers():
    """Kafka bootstrap servers for testing."""
    return "localhost:9092"


@pytest.fixture(scope="session")
def kafka_hostname():
    """Kafka hostname for testing."""
    return "localhost"


@pytest.fixture(scope="session")
def kafka_port():
    """Kafka port for testing."""
    return "9092"


@pytest.fixture(scope="function")
def test_topic():
    """Test topic name."""
    return "test-event"


@pytest.fixture(scope="function")
def admin_client(kafka_bootstrap_servers):
    """Kafka admin client for managing topics."""
    client = KafkaAdminClient(
        bootstrap_servers=kafka_bootstrap_servers,
        client_id="test-admin"
    )
    yield client
    client.close()


@pytest.fixture(scope="function")
def ensure_test_topic(admin_client, test_topic):
    """Ensure test topic exists before running tests."""
    try:
        topic = NewTopic(
            name=test_topic,
            num_partitions=1,
            replication_factor=1
        )
        admin_client.create_topics([topic], validate_only=False)
        time.sleep(1)  # Give Kafka time to create the topic
    except TopicAlreadyExistsError:
        pass  # Topic already exists, which is fine

    yield test_topic

    # Cleanup: delete messages by seeking to end (optional)
    # Note: We don't delete the topic to avoid issues with topic deletion delays


@pytest.fixture(scope="function")
def kmiddleware(kafka_hostname, kafka_port, test_topic):
    """Create a KMiddleware instance for testing."""
    middleware = KMiddleware(kafka_hostname, kafka_port, test_topic)
    yield middleware
    # Cleanup
    if middleware._running:
        middleware.stop()


@pytest.fixture(scope="function")
def kmiddleware_no_topics(kafka_hostname, kafka_port):
    """Create a KMiddleware instance without topics."""
    middleware = KMiddleware(kafka_hostname, kafka_port)
    yield middleware
    # Cleanup
    if middleware._running:
        middleware.stop()


@pytest.fixture(scope="function")
def kafka_producer(kafka_bootstrap_servers):
    """Standalone Kafka producer for testing."""
    producer = KafkaProducer(bootstrap_servers=kafka_bootstrap_servers)
    yield producer
    producer.close()
