# Test suite for KMiddleware initialization and basic setup

import pytest
from kmw import KMiddleware


class TestKMiddlewareInitialization:
    """Test cases for KMiddleware initialization."""

    def test_init_no_topics(self, kafka_hostname, kafka_port):
        """Test initialization without any topics."""
        kmw = KMiddleware(kafka_hostname, kafka_port)

        assert kmw._hostname == kafka_hostname
        assert kmw._port == kafka_port
        assert len(kmw._topics) == 0
        assert kmw._consumer_data == {}
        assert kmw.producer is not None
        assert kmw.consumer is None
        assert kmw._running is False

    def test_init_single_topic(self, kafka_hostname, kafka_port, test_topic):
        """Test initialization with a single topic."""
        kmw = KMiddleware(kafka_hostname, kafka_port, test_topic)

        assert kmw._hostname == kafka_hostname
        assert kmw._port == kafka_port
        assert test_topic in kmw._topics
        assert len(kmw._topics) == 1
        assert test_topic in kmw._consumer_data
        assert kmw._consumer_data[test_topic] == frozenset()
        assert kmw.producer is not None
        assert kmw.consumer is None
        assert kmw._running is False

    def test_init_multiple_topics(self, kafka_hostname, kafka_port):
        """Test initialization with multiple topics."""
        topics = ["test-event", "test-event-2", "test-event-3"]
        kmw = KMiddleware(kafka_hostname, kafka_port, *topics)

        assert kmw._hostname == kafka_hostname
        assert kmw._port == kafka_port
        assert len(kmw._topics) == 3
        for topic in topics:
            assert topic in kmw._topics
            assert topic in kmw._consumer_data
            assert kmw._consumer_data[topic] == frozenset()
        assert kmw.producer is not None
        assert kmw.consumer is None
        assert kmw._running is False

    def test_producer_created_on_init(self, kafka_hostname, kafka_port):
        """Test that producer is created during initialization."""
        kmw = KMiddleware(kafka_hostname, kafka_port)

        assert kmw.producer is not None
        assert hasattr(kmw.producer, 'send')
        assert hasattr(kmw.producer, 'close')

    def test_consumer_not_created_on_init(self, kafka_hostname, kafka_port, test_topic):
        """Test that consumer is NOT created during initialization."""
        kmw = KMiddleware(kafka_hostname, kafka_port, test_topic)

        assert kmw.consumer is None

    def test_bootstrap_servers_format(self, kafka_hostname, kafka_port):
        """Test that bootstrap servers are formatted correctly."""
        kmw = KMiddleware(kafka_hostname, kafka_port)

        expected_bootstrap = f"{kafka_hostname}:{kafka_port}"
        # Producer config should contain the bootstrap servers as a list
        bootstrap_servers = kmw.producer.config['bootstrap_servers']
        assert isinstance(bootstrap_servers, str)
        assert expected_bootstrap in bootstrap_servers

    def test_topics_stored_as_set(self, kafka_hostname, kafka_port):
        """Test that topics are stored as a set (no duplicates)."""
        topics = ["test-event", "test-event", "test-event-2"]
        kmw = KMiddleware(kafka_hostname, kafka_port, *topics)

        assert isinstance(kmw._topics, set)
        assert len(kmw._topics) == 2  # Duplicates removed

    def test_consumer_data_initialization(self, kafka_hostname, kafka_port):
        """Test that consumer_data is properly initialized for all topics."""
        topics = ["test-event", "test-event-2", "test-event-3"]
        kmw = KMiddleware(kafka_hostname, kafka_port, *topics)

        assert len(kmw._consumer_data) == 3
        for topic in topics:
            assert topic in kmw._consumer_data
            assert isinstance(kmw._consumer_data[topic], frozenset)
            assert len(kmw._consumer_data[topic]) == 0
