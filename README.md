# pei-nwdaf-comms

> Project for PEI evaluation 25/26

## Overview

General communication infrastructure components for the NWDAF (Network Data Analytics Function) system. Provides Kafka abstraction layer and reverse proxy configuration for inter-service communication within the "Intelligence in Action" platform.

## Technologies

- **Apache Kafka** 4.1.1 - Distributed event streaming
- **Python** - Core application language
- **Confluent Kafka** 2.12.2 - Python Kafka client library
- **AsyncIO** - Python async/await framework for non-blocking operations
- **Nginx** - Alpine-based reverse proxy server
- **Docker** - Containerization
- **pytest** - Testing framework

## Components

### 1. Kafka Module (`/kafka`)

**PyKafBridge** - Python abstraction layer providing simplified Kafka producer/consumer functionality

**Features**:
- Async-first design using Python asyncio
- Dynamic topic subscription and pattern-based topic discovery
- Message transformation through topic binding functions
- Offset tracking and partition assignment management
- Graceful consumer/producer lifecycle management
- Built-in error handling and logging
- Multiple consumer groups support for independent message consumption

**Message Structure**:
| Field | Type | Description |
|-------|------|-------------|
| `topic` | `string` | The topic it belongs to |
| `offset` | `int` | Message order identifier within partition |
| `content` | `string` | The actual message |
| `timestamp` | `int` | Message timestamp |

### 2. Nginx Module (`/nginx`)

**API Gateway** - Configured as reverse proxy routing to backend services

**Routes**:
- Dashboard Backend (root `/`)
- ML API (`/api/ml/`)
- Data Ingestion API (`/api/data-ingestion/`)
- Keycloak authentication (planned)
- Policy API (planned)
- Decision API (planned)

**Features**:
- Security headers (XSS protection, frame options, CSP)
- Gzip compression enabled
- Alpine-based lightweight container
- Optimized buffer configurations
- Health check endpoint

## Usage

### Kafka

1. Run Kafka container:
   ```bash
   docker run -p 9092:9092 apache/kafka:4.1.1
   ```

2. Topic management:
   ```bash
   topic.sh CONTAINER TOPIC -c  # Create topic
   topic.sh CONTAINER TOPIC -l  # Describe topic
   topic.sh CONTAINER TOPIC -r  # Remove topic
   ```

3. Import and use PyKafBridge:
   ```python
   from kmw import PyKafBridge

   # Instantiate with desired topics
   bridge = PyKafBridge(topics=["my-topic"])

   # Start consumer (blocking until ready)
   bridge.start_consumer()

   # Produce messages
   bridge.produce(topic="my-topic", message="data")

   # Consume messages
   messages = bridge.get_topic("my-topic")

   # Close gracefully
   bridge.close()
   ```

4. Topic binding for message transformation:
   ```python
   def transform(x: dict):
       # Transform message content
       return x

   bridge.bind_topic("my-topic", transform)
   ```

## Testing

Pytest suite covering:
- Single consumer/producer scenarios
- Multiple consumers with single producer
- Message transformation via topic bindings
- Multiple producers with single consumer

```bash
pytest tests/
```

## Development Status

- **Kafka component**: Core functionality complete, protocol standardization pending
- **Nginx component**: Container ready, awaiting full pipeline implementation for inter-component communication

## TODO

- Create protocol for communication between components via Kafka
- Implement full reverse proxy pipeline
- Complete Keycloak integration
