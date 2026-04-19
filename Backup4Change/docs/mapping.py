# mapping.py
# This file serves as the source of truth for the project's Architectural Strategy.

ARCHITECTURE_MAPPING = {
    "PROJECT_NAME": "Enterprise Django-Angular Platform",
    "CORE_STRUCTURE": "Modularized App Pattern",
    "STRATEGY_MAP": [
        {
            "point": "1. Multi-Database / 7. PgBouncer",
            "location": "main/routers.py",
            "role": "Routing logic for data isolation and connection pooling management.",
        },
        {
            "point": "2. JSONField / 8. GIN Indexes",
            "location": "core/models/",
            "role": "Defining schema-less data structures with optimized search performance.",
        },
        {
            "point": "3. Atomic Transactions",
            "location": "core/views/commands.py",
            "role": "Ensuring database integrity during complex write operations.",
        },
        {
            "point": "4. Materialized Views / 13. CQRS (Read)",
            "location": "core/views/queries.py",
            "role": "High-performance data retrieval for ApexCharts and analytics.",
        },
        {
            "point": "5. Redis Caching / 14. Write-ahead Caching",
            "location": "core/utils/cache_manager.py",
            "role": "Latency reduction and temporary storage before DB persistence.",
        },
        {
            "point": "6. Async Processes / 10. Bulk Process",
            "location": "core/reports/tasks.py",
            "role": "Offloading heavy computations and batch DB updates to Celery workers.",
        },
        {
            "point": "9. Real-time Alerting",
            "location": "core/signals/alerts.py",
            "role": "Triggering WebSocket notifications via Redis Pub/Sub.",
        },
        {
            "point": "11. Query Reduction",
            "location": "core/serializers/",
            "role": "Optimizing DB hits using select_related and prefetch_related in logic.",
        },
        {
            "point": "12. Event Driven / 15. Kafka/RabbitMQ",
            "location": "core/signals/handlers.py",
            "role": "Decoupling systems by emitting state-change events to the message broker.",
        },
        {
            "point": "16. Machine Learning",
            "location": "core/helpers/ml_engine.py",
            "role": "Housing prediction algorithms and recommendation logic.",
        },
        {
            "point": "Reporting Logic",
            "location": "core/reports/generator.py",
            "role": "Generating professional PDFs using FPDF from query data.",
        },
    ],
    "FRONTEND_INTEGRATION": {
        "framework": "Angular (Standalone: True)",
        "styling": "Tailwind CSS + PrimeNG (tailwindcss-primeui)",
        "charts": "ApexCharts",
        "strategy": "Optimistic updates to handle CQRS eventual consistency.",
    },
}
