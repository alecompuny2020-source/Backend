Backend/
├── .git/                       # Git repository
├── .env                        # Environment variables
├── .gitignore                  # Git exclusion rules
├── manage.py                   # Django management script
├── requirements/               # Dependencies split by environment
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── docs/                       # Architecture, strategy, and audit documentation
│   ├── schema.yml              # API documentation
│   ├── findings.py             # Research and alternative possibilities
│   ├── audit_structure.py      # Enterprise-wide audit flow
│   ├── folder_structure.py     # Source of truth for project layout
│   ├── groups_mapping.py       # Roles, groups, and permissions logic
│   └── tech_strategy.py        # Technologies and implementation methods
├── main/                       # Core project configuration
│   ├── settings/               # Environment-specific settings
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── routers.py              # Multi-database routing for data isolation
│   ├── celery.py               # Celery and distributed task configuration
│   ├── urls.py                 # Master URL routing
│   └── wsgi.py / asgi.py       # Deployment and socket configurations
├── common/                     # Global project-wide shared logic
│   ├── renderers.py            # Standardized JSON response formatting
│   ├── exceptions.py           # Global exception and error handlers
│   ├── middleware.py           # Enterprise audit tracking and custom middleware
│   ├── pagination.py           # Standardized pagination classes
│   ├── validators.py           # Shared data validation logic
│   ├── choices.py              # Centralized choice constants and enums
│   ├── mixins.py               # Reusable class-based mixins
│   ├── sender.py               # SMS and Email gateway integration
│   ├── security.py             # OTP, JWT, and encryption handlers
│   ├── utils.py                # Formatting and shared helper functions
│   ├── services/               # Cross-domain business logic (Auth, Onboarding)
│   └── permissions/            # RBAC and permission configurations
├── apps/                       # Modular business domains
│   ├── core/                   # Identity, account, and authentication domain
│   │   ├── models/             # Database schema definitions
│   │   ├── migrations/         # Database migration files
│   │   ├── serializers/        # Request validation and JSON transformation
│   │   ├── views/              # Viewsets and endpoint logic
│   │   ├── selectors.py        # Complex read operations and data retrieval
│   │   ├── signals.py          # Post-save and model-level triggers
│   │   ├── admin.py            # Administrative interface configuration
│   │   └── urls.py             # App-level routing
│   ├── hrms/                   # Human Resource (Payroll, Departments, Employee)
│   ├── pfls/                   # Poultry Farm Logistics (Hatcheries, Sheds, Feed)
│   ├── rms/                    # Recruitment Management (ATS, Applicant Tracking)
│   └── reporting/              # Dedicated BI and Analytics domain (CQRS)
│       ├── views.py            # Materialized view and reporting endpoints
│       └── services/           # FPDF and ApexCharts generation logic
├── workers/                    # Asynchronous and event-driven processing
│   ├── celery_app.py           # Background task definitions
│   └── kafka_consumers.py      # ML event-stream and data pipeline consumers
├── media/                      # User-uploaded files and resources
│   └── uploads/
├── static/ & templates/        # Global static assets and HTML templates
├── locale/                     # Internationalization (English/Swahili)
└── tests/                      # Testing suite
    ├── user_account_test.py
    ├── profile_test.py
    └── email_test.py
