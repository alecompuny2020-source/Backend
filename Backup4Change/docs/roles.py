# The "Complete" 2026 Enterprise Role Configuration
# Maps Group/Role -> Department -> Granular Module Permissions

ROLE_PERMISSIONS = {
    # --- ICT & ADMINISTRATION ---
    "SYSTEM_ADMINISTRATOR": {
        "department": "ICT",
        "permissions": ["__all__"],  # Full access across all 21 modules
    },
    "NETWORK_ADMINISTRATOR": {
        "department": "ICT",
        "permissions": [
            "infrastructure.view_server",
            "infrastructure.change_network_config",
        ],
    },
    "CYBER_SECURITY_OFFICER": {
        "department": "ICT",
        "permissions": ["security.view_audit_log", "security.manage_encryption"],
    },
    "ICT_OFFICER": {
        "department": "ICT",
        "permissions": ["support.add_ticket", "inventory.view_it_asset"],
    },
    "FARM_MANAGER": {
        "department": "Administration",
        "permissions": [
            "farm.view_productioncycle",
            "employee.view_employee",
            "charting.view_kpi_dashboard",
            "accounting.view_balancesheet",
        ],
    },
    "GENERAL_FARM_MANAGER": {
        "department": "Administration",
        "permissions": ["__all__"],  # Oversight role
    },
    # --- LOGISTICS & TRANSPORT (The Bolt-Style Mobility Actors) ---
    "TRANSPORT_OFFICER": {
        "department": "Logistics",
        "permissions": [
            "mobility.view_vehicle",
            "mobility.change_vehicle",
            "mobility.view_driver",
            "logistics.view_carrier",
            "mobility.view_mobilitybooking",
        ],
    },
    "LEAD_TRANSPORT_OFFICER": {
        "department": "Logistics",
        "permissions": [
            "mobility.add_vehicle",
            "mobility.add_driver",
            "mobility.view_tripledger",
        ],
    },
    "DELIVERY_AGENT": {
        "department": "Product Management",
        "permissions": [
            "mobility.view_mobilitybooking",
            "mobility.change_mobilitybooking",
        ],
    },
    # --- INFRASTRUCTURE & MAINTENANCE ---
    "MAINTENANCE_ENGINEER": {
        "department": "Infrastructure",
        "permissions": [
            "housing.view_building",
            "housing.add_maintenance_request",
            "mobility.view_vehicle",  # To check vehicle health for registry
        ],
    },
    "SENIOR_MAINTENANCE_ENGINEER": {
        "department": "Infrastructure",
        "permissions": ["housing.change_building", "infrastructure.manage_utilities"],
    },
    "HOUSING_MANAGER": {
        "department": "Apartment Management",
        "permissions": [
            "housing.view_unit",
            "housing.change_tenancy",
            "employee.view_employee",
        ],
    },
    # --- FARM & PRODUCTION ---
    "FLOCK_ATTENDANT": {
        "department": "Farm Management",
        "permissions": [
            "farm.view_flock",
            "farm.add_feedinglog",
            "health.view_vaccination",
        ],
    },
    "HATCHERY_SPECIALIST": {
        "department": "Breeding and Hatching",
        "permissions": ["breeding.add_incubationlog", "breeding.view_genetics"],
    },
    "NUTRITIONIST": {
        "department": "Feed Management",
        "permissions": ["feed.add_formulation", "feed.view_feedstock"],
    },
    "VETERINARY_OFFICER": {
        "department": "Health and Bio-security",
        "permissions": ["health.add_intervention", "health.view_healthrecord"],
    },
    # --- SAFETY & SECURITY ---
    "SECURITY_OFFICER": {
        "department": "Safety and Security",
        "permissions": [
            "security.view_geofence",
            "mobility.view_telemetry",
            "registration.view_entityregistration",
        ],
    },
    "LEAD_SECURITY_OFFICER": {
        "department": "Safety and Security",
        "permissions": [
            "security.manage_access_control",
            "security.view_incident_report",
        ],
    },
    # --- WASTE & SANITATION ---
    "SANITATION_SUPERVISOR": {
        "department": "Waste Management",
        "permissions": ["waste.add_wastelog", "waste.view_wastelog"],
    },
    "LEAD_SANITATION_SUPERVISOR": {
        "department": "Waste Management",
        "permissions": ["waste.change_wastelog", "processing.view_processingplant"],
    },
    # --- MEDIA, RECREATION & HOSPITALITY ---
    "CONTENT_CREATOR": {
        "department": "Media & Communication",
        "permissions": ["messaging.add_chat", "sales.view_producttype"],
    },
    "HOSPITALITY_COORDINATOR": {
        "department": "Recreation Management",
        "permissions": ["recreation.view_facility", "hospitality.add_booking"],
    },
    "PLAYGROUND_SUPERVISOR": {
        "department": "Recreation Management",
        "permissions": ["pground.view_geofence", "pground.view_projectground"],
    },
    # --- FINANCE & SALES ---
    "FINANCIAL_OFFICER": {
        "department": "Finance",
        "permissions": [
            "accounting.view_ledger",
            "expenses.add_expense",
            "mobility.view_tripledger",
        ],
    },
    "SALES_AGENT": {
        "department": "Product Management",
        "permissions": ["inventory.view_productstock", "sales.add_salesorder"],
    },
    "PACKAGING_MANAGER": {
        "department": "Processing and Packaging",
        "permissions": ["processing.add_packaginglog", "inventory.add_stockmovement"],
    },
    # --- EXTERNAL ---
    "CUSTOMER": {
        "department": "External",
        "permissions": [
            "sales.view_producttype",
            "messaging.add_chat",
            "mobility.add_mobilitybooking",
        ],
    },
}
