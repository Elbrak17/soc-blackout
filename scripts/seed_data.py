#!/usr/bin/env python3
"""
SOC Blackout — Synthetic Data Seeder
Generates realistic incident response data across 4 Elasticsearch indices:
  - soc-logs     : Application/system logs with error patterns
  - soc-metrics  : Infrastructure metrics (CPU, memory, disk, network)
  - soc-incidents: Historical incident knowledge base
  - soc-actions  : Audit log of agent actions (starts empty)
"""

import os
import sys
import json
import random
import hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv
from faker import Faker

# Load .env from project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
fake = Faker()

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

ES_URL = os.getenv("ELASTICSEARCH_URL", "")
ES_API_KEY = os.getenv("ELASTICSEARCH_API_KEY", "")
ES_CLOUD_ID = os.getenv("ELASTICSEARCH_CLOUD_ID", "")


def get_es_client() -> Elasticsearch:
    """Create Elasticsearch client from environment variables."""
    if ES_CLOUD_ID and ES_API_KEY:
        return Elasticsearch(cloud_id=ES_CLOUD_ID, api_key=ES_API_KEY)
    if ES_URL and ES_API_KEY:
        return Elasticsearch(ES_URL, api_key=ES_API_KEY)
    if ES_URL:
        return Elasticsearch(ES_URL)

    print("\n❌ ERROR: No Elasticsearch connection configured!")
    print("   Edit the .env file at the project root with your credentials:")
    print(f"   → {PROJECT_ROOT / '.env'}")
    print("")
    print("   Required:")
    print("     ELASTICSEARCH_URL=https://your-project.es.us-central1.gcp.elastic.cloud")
    print("     ELASTICSEARCH_API_KEY=your-api-key")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Index mappings
# ---------------------------------------------------------------------------

MAPPINGS = {
    "soc-logs": {
        "mappings": {
            "properties": {
                "@timestamp": {"type": "date"},
                "service": {"type": "keyword"},
                "level": {"type": "keyword"},
                "message": {"type": "text"},
                "host": {"type": "keyword"},
                "trace_id": {"type": "keyword"},
            }
        }
    },
    "soc-metrics": {
        "mappings": {
            "properties": {
                "@timestamp": {"type": "date"},
                "host": {"type": "keyword"},
                "cpu_pct": {"type": "float"},
                "mem_pct": {"type": "float"},
                "disk_io": {"type": "float"},
                "net_in": {"type": "long"},
                "net_out": {"type": "long"},
            }
        }
    },
    "soc-incidents": {
        "mappings": {
            "properties": {
                "incident_id": {"type": "keyword"},
                "title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "root_cause": {"type": "text"},
                "resolution": {"type": "text"},
                "services_affected": {"type": "keyword"},
                "severity": {"type": "keyword"},
                "duration_min": {"type": "integer"},
                "created_at": {"type": "date"},
                "tags": {"type": "keyword"},
                "runbook": {"type": "text"},
            }
        }
    },
    "soc-actions": {
        "mappings": {
            "properties": {
                "@timestamp": {"type": "date"},
                "action_type": {"type": "keyword"},
                "description": {"type": "text"},
                "confidence": {"type": "integer"},
                "status": {"type": "keyword"},
                "incident_ref": {"type": "keyword"},
            }
        }
    },
}

# ---------------------------------------------------------------------------
# Data generation constants
# ---------------------------------------------------------------------------

SERVICES = [
    "api-gateway", "auth-service", "payment-service",
    "user-service", "notification-service", "search-service",
    "order-service", "inventory-service",
]

HOSTS = [
    "prod-web-01", "prod-web-02", "prod-web-03",
    "prod-app-01", "prod-app-02",
    "prod-db-01", "prod-db-02",
    "prod-cache-01",
]

LOG_LEVELS_NORMAL = ["INFO", "DEBUG", "INFO", "INFO", "WARN", "INFO"]
LOG_LEVELS_INCIDENT = ["ERROR", "CRITICAL", "ERROR", "FATAL", "ERROR", "WARN"]

NORMAL_MESSAGES = [
    "Request processed successfully in {t}ms",
    "Health check passed for {service}",
    "Connection pool at {n}% capacity",
    "Cache hit ratio: {n}%",
    "Scheduled task completed: cleanup_old_sessions",
    "User authentication successful for user_id={uid}",
    "Database query executed in {t}ms",
    "Rate limiter reset for {service}",
]

ERROR_MESSAGES_BY_SCENARIO = {
    "cpu_spike": [
        "CPU throttling detected on {host}: usage at {n}%",
        "Thread pool exhausted on {host}, {n} tasks queued",
        "Request timeout after 30000ms on {service}",
        "GC pause exceeded threshold: {t}ms on {host}",
        "Load balancer health check failed for {host}",
    ],
    "oom_crash": [
        "OutOfMemoryError: Java heap space on {host}",
        "Container killed by OOM killer: {service} on {host}",
        "Memory allocation failed: requested {n}MB, available 12MB",
        "Pod {service} restarting due to OOMKilled on {host}",
        "Heap dump generated: /var/log/{service}/heap_{t}.hprof",
    ],
    "cascading_failure": [
        "Connection refused to {service} from {host}",
        "Circuit breaker OPEN for {service}: 15 failures in 60s",
        "Downstream dependency {service} unavailable, returning 503",
        "Retry exhausted for {service} after 3 attempts",
        "Dead letter queue growing: {n} messages pending for {service}",
        "Cascading timeout: {service} -> payment-service -> auth-service",
    ],
}

# ---------------------------------------------------------------------------
# Historical incidents knowledge base
# ---------------------------------------------------------------------------

HISTORICAL_INCIDENTS = [
    {
        "incident_id": "INC-001",
        "title": "Payment service OOM crash during Black Friday surge",
        "root_cause": "Memory leak in payment-service connection pool. The JDBC connection pool was not releasing connections on transaction timeout, leading to heap exhaustion under load.",
        "resolution": "Patched connection pool library to v3.2.1, added connection timeout of 30s, increased heap to 4GB, and added memory-based autoscaling.",
        "services_affected": ["payment-service", "order-service", "api-gateway"],
        "severity": "critical",
        "duration_min": 45,
        "tags": ["oom", "memory", "payment", "connection-pool", "black-friday"],
        "runbook": "When payment-service experiences OOM: 1) Check heap usage with `kubectl top pods -n payments`. 2) If heap > 90%, restart the pod: `kubectl rollout restart deployment/payment-service`. 3) Check connection pool metrics: `GET /actuator/metrics/hikaricp.connections.active`. 4) If connections are not being released, apply hotfix: scale up replicas to 5 and patch connection timeout. 5) Monitor for 15 minutes. 6) If issue persists, failover to payment-service-backup.",
    },
    {
        "incident_id": "INC-002",
        "title": "API Gateway CPU spike from recursive middleware loop",
        "root_cause": "A misconfigured middleware in api-gateway caused a recursive call loop when processing requests with specific headers. CPU spiked to 100% across all gateway pods.",
        "resolution": "Identified the faulty middleware rule via CPU profiling, rolled back to previous gateway config version, added middleware stack depth limit of 10.",
        "services_affected": ["api-gateway", "auth-service"],
        "severity": "critical",
        "duration_min": 32,
        "tags": ["cpu", "api-gateway", "middleware", "recursion", "config"],
        "runbook": "When api-gateway CPU spikes above 95%: 1) Check recent config deployments: `kubectl get configmap api-gateway-config -o yaml`. 2) Compare with last known good config. 3) If config changed recently, rollback: `kubectl rollout undo deployment/api-gateway`. 4) If CPU stays high, check for recursive middleware: `curl localhost:8080/actuator/threaddump | grep middleware`. 5) Scale up to absorb traffic while investigating.",
    },
    {
        "incident_id": "INC-003",
        "title": "Cascading failure from auth-service certificate expiry",
        "root_cause": "TLS certificate for auth-service expired at 00:00 UTC. All services depending on auth-service started failing, creating a cascade. Circuit breakers activated but the retry storms amplified the load.",
        "resolution": "Renewed TLS certificate, restarted auth-service, then gradually reopened circuit breakers across dependent services. Added certificate expiry monitoring to prevent recurrence.",
        "services_affected": ["auth-service", "api-gateway", "payment-service", "user-service", "order-service"],
        "severity": "critical",
        "duration_min": 67,
        "tags": ["cascading", "tls", "certificate", "auth", "circuit-breaker"],
        "runbook": "When auth-service connections are refused across multiple services: 1) Check auth-service TLS cert: `openssl s_client -connect auth-service:443 2>/dev/null | openssl x509 -noout -dates`. 2) If cert expired, renew immediately: `certbot renew --deploy-hook 'kubectl rollout restart deployment/auth-service'`. 3) After auth is back, reset circuit breakers on dependent services one at a time, starting with api-gateway. 4) Monitor error rates for 30 minutes before declaring resolved.",
    },
    {
        "incident_id": "INC-004",
        "title": "Search service latency spike from unoptimized Elasticsearch query",
        "root_cause": "A new feature deployment included a wildcard query on a large index without proper filters, causing ES cluster CPU to saturate and search latency to spike to 15s.",
        "resolution": "Identified the offending query via slow query log, added index filters and pagination, redeployed search-service with the fix.",
        "services_affected": ["search-service"],
        "severity": "high",
        "duration_min": 22,
        "tags": ["latency", "elasticsearch", "query", "search"],
        "runbook": "When search-service latency exceeds 5s: 1) Check ES slow query log: `GET /_nodes/stats/indices/search`. 2) Identify the slow query. 3) If wildcard query, add filters or convert to prefix query. 4) If cluster CPU > 90%, enable circuit breaker: `PUT /_cluster/settings {\"transient\": {\"indices.breaker.total.limit\": \"70%\"}}`. 5) Redeploy search-service with fix.",
    },
    {
        "incident_id": "INC-005",
        "title": "Database connection exhaustion on prod-db-01",
        "root_cause": "A background job in user-service opened database connections without closing them properly. After 6 hours of running, all 200 connection slots on prod-db-01 were consumed.",
        "resolution": "Killed the runaway background job, released stale connections, patched user-service to use connection pooling with max 20 connections per service instance.",
        "services_affected": ["user-service", "auth-service", "order-service"],
        "severity": "high",
        "duration_min": 38,
        "tags": ["database", "connections", "leak", "user-service", "production"],
        "runbook": "When database connections are exhausted: 1) Check active connections: `SELECT count(*) FROM pg_stat_activity WHERE state = 'active'`. 2) Identify the service holding most connections: `SELECT application_name, count(*) FROM pg_stat_activity GROUP BY application_name ORDER BY count DESC`. 3) Kill idle connections: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < NOW() - interval '10 minutes'`. 4) Restart the offending service. 5) Add connection pool limits.",
    },
    {
        "incident_id": "INC-006",
        "title": "Notification service disk full causing message loss",
        "root_cause": "Notification service log volume on prod-app-02 filled the disk to 100%. The service could not write to its message queue, causing notifications to be silently dropped.",
        "resolution": "Cleared old logs, rotated log files, added log retention policy (7 days max, 10GB cap), added disk usage monitoring alert at 80%.",
        "services_affected": ["notification-service"],
        "severity": "medium",
        "duration_min": 18,
        "tags": ["disk", "logs", "notification", "message-loss"],
        "runbook": "When disk usage exceeds 90% on any host: 1) Check what's consuming disk: `du -sh /var/log/* | sort -rh | head`. 2) If logs, rotate immediately: `logrotate -f /etc/logrotate.conf`. 3) Delete logs older than 7 days: `find /var/log -name '*.log' -mtime +7 -delete`. 4) Restart the affected service. 5) Verify message queue is draining: `curl localhost:8080/actuator/metrics/queue.size`.",
    },
    {
        "incident_id": "INC-007",
        "title": "Cache stampede on prod-cache-01 after cold restart",
        "root_cause": "After a planned maintenance restart of prod-cache-01, all cached data was evicted. The simultaneous cache miss storm from all services overwhelmed the database backend.",
        "resolution": "Implemented cache warming script that pre-populates hot keys before bringing cache online. Added gradual traffic ramp-up after cache restart.",
        "services_affected": ["api-gateway", "search-service", "user-service", "order-service"],
        "severity": "high",
        "duration_min": 25,
        "tags": ["cache", "stampede", "cold-start", "redis"],
        "runbook": "After cache restart: 1) Run cache warming script before routing traffic: `python warm_cache.py --keys hot_keys.txt`. 2) Enable gradual traffic ramp: increase weight from 10% to 100% over 10 minutes. 3) Monitor cache hit ratio: should reach >80% within 5 minutes. 4) If DB load spikes, temporarily enable read replicas.",
    },
    {
        "incident_id": "INC-008",
        "title": "Inventory service race condition causing overselling",
        "root_cause": "Concurrent stock decrement operations on inventory-service were not using optimistic locking. Under high load, multiple orders could reserve the same unit of stock.",
        "resolution": "Added optimistic locking with version check on inventory updates. Implemented idempotency keys for order placement. Added stock reconciliation job running every 5 minutes.",
        "services_affected": ["inventory-service", "order-service"],
        "severity": "critical",
        "duration_min": 90,
        "tags": ["race-condition", "inventory", "concurrency", "data-integrity"],
        "runbook": "When overselling is detected: 1) Immediately pause order intake: `kubectl scale deployment/order-service --replicas=0`. 2) Run stock reconciliation: `python reconcile_stock.py --fix`. 3) Contact affected customers. 4) Deploy fix with optimistic locking. 5) Resume order service with reduced replicas, monitor for 1 hour.",
    },
]


# ---------------------------------------------------------------------------
# Data generators
# ---------------------------------------------------------------------------

def _ts(base: datetime, offset_minutes: float) -> str:
    """Return ISO timestamp string."""
    return (base + timedelta(minutes=offset_minutes)).isoformat()


def _trace() -> str:
    return hashlib.md5(fake.uuid4().encode()).hexdigest()[:16]


def generate_normal_logs(base: datetime, count: int = 200) -> list[dict]:
    """Generate baseline healthy-system log entries."""
    docs = []
    for i in range(count):
        offset = random.uniform(-60, 0)
        service = random.choice(SERVICES)
        host = random.choice(HOSTS)
        msg_template = random.choice(NORMAL_MESSAGES)
        msg = msg_template.format(
            t=random.randint(2, 500),
            service=service,
            n=random.randint(10, 95),
            uid=fake.random_int(1000, 99999),
        )
        docs.append({
            "_index": "soc-logs",
            "@timestamp": _ts(base, offset),
            "service": service,
            "level": random.choice(LOG_LEVELS_NORMAL),
            "message": msg,
            "host": host,
            "trace_id": _trace(),
        })
    return docs


def generate_incident_logs(base: datetime, scenario: str, count: int = 80) -> list[dict]:
    """Generate error logs for a specific incident scenario."""
    error_msgs = ERROR_MESSAGES_BY_SCENARIO[scenario]
    docs = []

    # Errors cluster in the last 15 minutes
    for i in range(count):
        offset = random.uniform(-15, 0)
        service = random.choice(SERVICES[:4])
        host = random.choice(HOSTS[:4])
        msg_template = random.choice(error_msgs)
        msg = msg_template.format(
            host=host,
            service=service,
            n=random.randint(85, 100),
            t=random.randint(1000, 30000),
        )
        docs.append({
            "_index": "soc-logs",
            "@timestamp": _ts(base, offset),
            "service": service,
            "level": random.choice(LOG_LEVELS_INCIDENT),
            "message": msg,
            "host": host,
            "trace_id": _trace(),
        })
    return docs


def generate_normal_metrics(base: datetime, count: int = 100) -> list[dict]:
    """Generate baseline healthy metrics."""
    docs = []
    for i in range(count):
        offset = random.uniform(-60, 0)
        host = random.choice(HOSTS)
        docs.append({
            "_index": "soc-metrics",
            "@timestamp": _ts(base, offset),
            "host": host,
            "cpu_pct": round(random.uniform(10, 55), 1),
            "mem_pct": round(random.uniform(30, 70), 1),
            "disk_io": round(random.uniform(0.5, 20), 2),
            "net_in": random.randint(100_000, 5_000_000),
            "net_out": random.randint(50_000, 3_000_000),
        })
    return docs


def generate_incident_metrics(base: datetime, scenario: str, count: int = 50) -> list[dict]:
    """Generate anomalous metrics for a specific scenario."""
    docs = []
    target_hosts = random.sample(HOSTS[:4], 2)

    for i in range(count):
        offset = random.uniform(-15, 0)
        host = random.choice(target_hosts)

        if scenario == "cpu_spike":
            cpu = round(random.uniform(92, 100), 1)
            mem = round(random.uniform(60, 80), 1)
        elif scenario == "oom_crash":
            cpu = round(random.uniform(50, 75), 1)
            mem = round(random.uniform(95, 100), 1)
        else:  # cascading_failure
            cpu = round(random.uniform(80, 98), 1)
            mem = round(random.uniform(75, 95), 1)

        docs.append({
            "_index": "soc-metrics",
            "@timestamp": _ts(base, offset),
            "host": host,
            "cpu_pct": cpu,
            "mem_pct": mem,
            "disk_io": round(random.uniform(50, 200), 2),
            "net_in": random.randint(10_000_000, 50_000_000),
            "net_out": random.randint(5_000_000, 30_000_000),
        })
    return docs


def generate_incidents() -> list[dict]:
    """Generate the historical incidents knowledge base."""
    docs = []
    for inc in HISTORICAL_INCIDENTS:
        doc = {
            "_index": "soc-incidents",
            **inc,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(7, 180))).isoformat(),
        }
        docs.append(doc)
    return docs


# ---------------------------------------------------------------------------
# Index management
# ---------------------------------------------------------------------------

def create_indices(es: Elasticsearch) -> None:
    """Create indices with proper mappings, deleting existing ones."""
    for index_name, mapping in MAPPINGS.items():
        if es.indices.exists(index=index_name):
            print(f"  Deleting existing index: {index_name}")
            es.indices.delete(index=index_name)
        print(f"  Creating index: {index_name}")
        es.indices.create(index=index_name, body=mapping)


def seed_scenario(es: Elasticsearch, scenario: str) -> None:
    """Seed data for a specific incident scenario."""
    now = datetime.now(timezone.utc)
    print(f"\n  Seeding scenario: {scenario}")

    # Normal baseline
    normal_logs = generate_normal_logs(now, count=200)
    normal_metrics = generate_normal_metrics(now, count=100)

    # Incident data
    incident_logs = generate_incident_logs(now, scenario, count=80)
    incident_metrics = generate_incident_metrics(now, scenario, count=50)

    # Historical incidents
    incidents = generate_incidents()

    all_docs = normal_logs + normal_metrics + incident_logs + incident_metrics + incidents

    print(f"  Bulk indexing {len(all_docs)} documents...")
    success, errors = helpers.bulk(es, all_docs, raise_on_error=False)
    print(f"  ✅ Indexed {success} docs, {len(errors) if isinstance(errors, list) else 0} errors")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  SOC Blackout — Data Seeder")
    print("=" * 60)

    es = get_es_client()

    # Verify connection
    info = es.info()
    print(f"\n  Connected to: {info['cluster_name']} (v{info['version']['number']})")

    # Create indices
    print("\n📦 Creating indices...")
    create_indices(es)

    # Ask which scenario to seed
    scenarios = ["cpu_spike", "oom_crash", "cascading_failure"]
    print("\n🎭 Available demo scenarios:")
    for i, s in enumerate(scenarios, 1):
        print(f"  {i}. {s}")
    print(f"  4. ALL scenarios (combined)")

    choice = input("\n  Choose scenario [1-4, default=4]: ").strip() or "4"

    if choice == "4":
        for s in scenarios:
            seed_scenario(es, s)
    else:
        idx = int(choice) - 1
        if 0 <= idx < len(scenarios):
            seed_scenario(es, scenarios[idx])
        else:
            print("  Invalid choice, seeding all.")
            for s in scenarios:
                seed_scenario(es, s)

    # Verify
    print("\n📊 Index verification:")
    for idx_name in MAPPINGS:
        es.indices.refresh(index=idx_name)
        count = es.count(index=idx_name)["count"]
        print(f"  {idx_name}: {count} documents")

    print("\n✅ Seeding complete! You can now use SOC Blackout.")
    print("=" * 60)


if __name__ == "__main__":
    main()
