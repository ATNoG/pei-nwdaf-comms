# pei-nwdaf-kafka
Kafka interface component for Intelligence in Action. The goal is to abstract kafka-related logic from other components to ease communication.

# TODO:

- [ ] Create a protocol for communication between components via Kafka
- [ ] Rename the class from Middleware to something else :)
- [ ] Add a Dockerfile (so far it's feasible in a single command but further configuration may be required)

# Usage
0. (For now) run a Kafka container with `docker run -p 9092:9092 apache/kafka:4.1.1` (be sure to pull the image first)
1. Import the KMiddleware class and instantiate with the desired topics (or add more later)
2. Start the object with `.start()`
3. While messages are stored in the object's data structures, you may run `produce(topic: str)` to send any sort of event to Kafka

# Run tests

```py
pytest
```

To see all available tests you can run:

```py
pytest --collect-only
```
