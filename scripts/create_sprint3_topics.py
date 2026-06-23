"""Create Sprint 3 Kafka topics (idempotent).

Usage:
    uv run python scripts/create_sprint3_topics.py
"""
from kafka.admin import KafkaAdminClient, NewTopic

BOOTSTRAP_SERVERS = "localhost:9092"
PARTITIONS = 6
REPLICATION = 1

TOPICS = [
    "ipe.mo.capacity_scored",
    "ipe.resolution.proposed",
    "ipe.resolution.approved",
    "ipe.delay.logged",
    "ipe.dlq.cap-svc",
    "ipe.dlq.res-svc",
    "ipe.dlq.del-svc",
]


def main():
    admin = KafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVERS)
    existing = admin.list_topics()
    new_topics = []
    for t in TOPICS:
        if t not in existing:
            new_topics.append(NewTopic(
                name=t,
                num_partitions=PARTITIONS,
                replication_factor=REPLICATION,
            ))
            print(f"  Creating {t}...")
        else:
            print(f"  EXISTS {t}")

    if new_topics:
        admin.create_topics(new_topics)
        print(f"\nCreated {len(new_topics)} new topics.")
    else:
        print("\nAll topics already exist.")

    admin.close()


if __name__ == "__main__":
    main()
