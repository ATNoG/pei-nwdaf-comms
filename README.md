# pei-nwdaf-comms
General communication components related to Intelligence in Action (WIP)

# Kafka

## TODO:

- [ ] Create a protocol for communication between components via Kafka


## Usage
1. Run a Kafka container with `docker run -p 9092:9092 apache/kafka:4.1.1` (be sure to pull the image first: `docker pull apache/kafka:4.1.1`)*
    1. To create a topic run `topic.sh CONTAINER TOPIC -c`
    2. To describe a topic run `topic.sh CONTAINER TOPIC -l`
    3. To remove a topic run `topic.sh CONTAINER TOPIC -r`
2. Import the PyKafBridge class and instantiate with the desired topics (or add more later)
3. Start the consumer with `.start()`
4. Whilst messages are stored in the class, you may run `.produce(topic: str)` to send any sort of event to Kafka
5. To get messages received on subscribed topics, run `.get_topic(topic_name: str)`

**Note:** You may bind functions to topics so their contents are automatically transformed.
Those binding functions must respect the following structure:

```py
def f(x: dict):
    # Do something with x
    return x  # Whether it was changed or not!
```

Then do `.bind_topic(topic, func)`

`x` is a **dictionary** with some of the data fetched from the Kafka event:

| Field       | Type   | Description                                  |
|-------------|--------|----------------------------------------------|
| `topic`       | `string` | The topic it belongs to                      |
| `offset`      | `int`    | Identifier for the order of messages within a topic's partition |
| `content`     | `string` | The actual message                           |
| `timestamp`   | `int`    | Timestamp of the message                              |

Topic partitions are to be analyzed in further development, along with an established protocol for components to communicate with eachother.

# Nginx

Nginx's container is ready yet **waiting for further pipeline implementation** to actually interact with the components (as in reverse-proxying)
