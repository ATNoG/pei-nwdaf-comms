# Test suite for PyKafBridge topic management functionality

import pytest
from kmw import PyKafBridge


class TestTopicManagement:
    """Test cases for adding and managing topics in PyKafBridge."""

    def test_add_topic_to_empty_middleware(self, kmiddleware_no_topics):
        """Test adding a topic to middleware with no initial topics."""
        kmw = kmiddleware_no_topics

        assert len(kmw._topics) == 0

        kmw.add_topic("test-event")

        assert "test-event" in kmw._topics
        assert len(kmw._topics) == 1
        assert "test-event" in kmw._consumer_data
        assert kmw._consumer_data["test-event"] == frozenset()

    def test_add_topic_to_existing_topics(self, kmiddleware):
        """Test adding a topic when topics already exist."""
        kmw = kmiddleware

        initial_count = len(kmw._topics)

        kmw.add_topic("test-event-2")

        assert "test-event-2" in kmw._topics
        assert len(kmw._topics) == initial_count + 1
        assert "test-event-2" in kmw._consumer_data
        assert kmw._consumer_data["test-event-2"] == frozenset()

    def test_add_duplicate_topic(self, kmiddleware):
        """Test adding a topic that already exists (set should prevent duplicates)."""
        kmw = kmiddleware

        initial_count = len(kmw._topics)

        # Add a topic that already exists
        kmw.add_topic("test-event")

        # Set should prevent duplicates
        assert len(kmw._topics) == initial_count

    def test_extend_topics_with_list(self, kmiddleware_no_topics):
        """Test extending topics with a list of new topics."""
        kmw = kmiddleware_no_topics

        new_topics = ["test-event", "test-event-2", "test-event-3"]

        kmw.extend_topics(new_topics)

        assert len(kmw._topics) == 3
        for topic in new_topics:
            assert topic in kmw._topics
            assert topic in kmw._consumer_data
            assert kmw._consumer_data[topic] == frozenset()

    def test_extend_topics_with_tuple(self, kmiddleware_no_topics):
        """Test extending topics with a tuple."""
        kmw = kmiddleware_no_topics

        new_topics = ("test-event", "test-event-2")

        kmw.extend_topics(new_topics)

        assert len(kmw._topics) == 2
        for topic in new_topics:
            assert topic in kmw._topics
            assert topic in kmw._consumer_data

    def test_extend_topics_with_set(self, kmiddleware_no_topics):
        """Test extending topics with a set."""
        kmw = kmiddleware_no_topics

        new_topics = {"test-event", "test-event-2", "test-event-3"}

        kmw.extend_topics(new_topics)

        assert len(kmw._topics) == 3
        for topic in new_topics:
            assert topic in kmw._topics

    def test_extend_topics_to_existing_topics(self, kmiddleware):
        """Test extending topics when some already exist."""
        kmw = kmiddleware

        initial_count = len(kmw._topics)

        new_topics = ["test-event-2", "test-event-3"]

        kmw.extend_topics(new_topics)

        assert len(kmw._topics) == initial_count + 2
        for topic in new_topics:
            assert topic in kmw._topics
            assert topic in kmw._consumer_data

    def test_extend_topics_with_duplicates(self, kmiddleware_no_topics):
        """Test extending topics with duplicate topic names."""
        kmw = kmiddleware_no_topics

        new_topics = ["test-event", "test-event-2", "test-event"]

        kmw.extend_topics(new_topics)

        # Set should remove duplicates
        assert len(kmw._topics) == 2
        assert "test-event" in kmw._topics
        assert "test-event-2" in kmw._topics

    def test_extend_topics_empty_list(self, kmiddleware):
        """Test extending topics with an empty list."""
        kmw = kmiddleware

        initial_count = len(kmw._topics)

        kmw.extend_topics([])

        assert len(kmw._topics) == initial_count

    def test_add_topic_initializes_consumer_data(self, kmiddleware_no_topics):
        """Test that adding a topic initializes its consumer_data entry."""
        kmw = kmiddleware_no_topics

        kmw.add_topic("new-topic")

        assert "new-topic" in kmw._consumer_data
        assert isinstance(kmw._consumer_data["new-topic"], frozenset)
        assert len(kmw._consumer_data["new-topic"]) == 0

    def test_extend_topics_initializes_all_consumer_data(self, kmiddleware_no_topics):
        """Test that extending topics initializes consumer_data for all topics."""
        kmw = kmiddleware_no_topics

        topics = ["topic1", "topic2", "topic3"]
        kmw.extend_topics(topics)

        for topic in topics:
            assert topic in kmw._consumer_data
            assert isinstance(kmw._consumer_data[topic], frozenset)
            assert len(kmw._consumer_data[topic]) == 0

    def test_multiple_add_topic_calls(self, kmiddleware_no_topics):
        """Test multiple sequential add_topic calls."""
        kmw = kmiddleware_no_topics

        kmw.add_topic("topic1")
        kmw.add_topic("topic2")
        kmw.add_topic("topic3")

        assert len(kmw._topics) == 3
        assert "topic1" in kmw._topics
        assert "topic2" in kmw._topics
        assert "topic3" in kmw._topics

        for topic in ["topic1", "topic2", "topic3"]:
            assert topic in kmw._consumer_data
