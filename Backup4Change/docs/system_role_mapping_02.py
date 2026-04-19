# System Role Mapping for an Enterprise
# Separation of Concern: Maps Actors -> Departments -> Systems -> Actions

SYSTEM_ROLE_MAPPING = {
    # --- 1. RECREATION ZONE MANAGEMENT SYSTEM ---
    "RECREATION_ZONE_MANAGEMENT": {
        "HOSPITALITY_COORDINATOR": {
            "department": "Recreation management",
            "actions": ["add_booking", "view_facility", "change_amenity"],
        },
        "PLAYGROUND_LEISURE_SUPERVISOR": {
            "department": "Recreation management",
            "actions": ["view_geofence", "view_projectground", "manage_equipment"],
        },
        "LEAD_PLAYGROUND_LEISURE_SUPERVISOR": {
            "department": "Recreation management",
            "actions": ["__all__"],
        },
        "MPAMBAJI": {
            "department": "decollations",
            "actions": ["view_event_layout", "add_decoration_inventory"],
        },
        "GROUND_GREENERY_KEEPER": {
            "department": "Recreation management",
            "actions": ["view_maintenance_log", "update_landscape_status"],
        },
    },
    # --- 2. POULTRY FARM MANAGEMENT INFORMATION SYSTEM ---
    "POULTRY_FARM_MANAGEMENT": {
        "FARM_MANAGER": {
            "department": "Administration",  #
            "actions": [
                "view_productioncycle",
                "view_kpi_dashboard",
                "manage_farm_inventory",
            ],  #
        },
        "GENERAL_FARM_MANAGER": {
            "department": "Administration",  #
            "actions": ["__all__"],
        },
        "FLOCK_SHED_ATTENDANT": {
            "department": "Farm management",  #
            "actions": ["view_flock", "add_feedinglog", "update_shed_status"],  #
        },
    },
    # --- 3. BREEDING AND HATCHERY MANAGEMENT SYSTEM ---
    "BREEDING_HATCHERY_MANAGEMENT": {
        "INCUBATOR_HATCHERY_SPECIALIST": {
            "department": "Breeding and hatching",  #
            "actions": ["add_incubationlog", "view_genetics", "monitor_temperature"],  #
        }
    },
    # --- 4. FEED MANAGEMENT SYSTEM ---
    "FEED_MANAGEMENT": {
        "NUTRITIONIST": {
            "department": "Feed management",  #
            "actions": ["add_formulation", "view_feedstock", "manage_ingredients"],  #
        },
        "LEAD_NUTRITIONIST": {
            "department": "Feed management",  #
            "actions": ["approve_formula", "view_supplier_quality"],
        },
    },
    # --- 5. POULTRY HEALTH MANAGEMENT SYSTEM ---
    "POULTRY_HEALTH_MANAGEMENT": {
        "VETERINARY_OFFICER": {
            "department": "Heath and bio-security",  #
            "actions": ["add_intervention", "view_healthrecord", "request_vaccine"],  #
        },
        "LEAD_VETERINARY_OFFICER": {
            "department": "Heath and bio-security",  #
            "actions": ["__all__"],
        },
    },
    # --- 6. USER INFORMATION MANAGEMENT SYSTEM ---
    "USER_INFORMATION_MANAGEMENT": {
        "SYSTEM_ADMINISTRATOR": {
            "department": "ICT",  #
            "actions": ["add_user", "change_user", "assign_role", "view_audit_log"],  #
        },
        "ICT_OFFICER": {
            "department": "ICT",  #
            "actions": ["reset_password", "view_user_session"],
        },
        "NETWORK_ADMINISTRATOR": {
            "department": "ICT",  #
            "actions": ["manage_network_access", "view_vpn_logs"],
        },
        "CYBER_SECURITY_OFFICER": {
            "department": "ICT",  #
            "actions": ["audit_permissions", "view_security_incidents"],
        },
    },
    # --- 7. WASTE MANAGEMENT SYSTEM ---
    "WASTE_MANAGEMENT": {
        "SANITATION_WASTE_SUPERVISOR": {
            "department": "Waste management",  #
            "actions": ["add_wastelog", "view_wastelog"],  #
        },
        "LEAD_SANITATION_WASTE_SUPERVISOR": {
            "department": "Waste management",  #
            "actions": ["approve_waste_disposal", "view_compliance_report"],
        },
    },
    # --- 10 & 11. FINANCE & ACCOUNTING SYSTEMS ---
    "FINANCE_ACCOUNTING": {
        "FINANCIAL_OFFICER": {
            "department": "finance",  #
            "actions": ["view_ledger", "view_balancesheet", "add_expense"],  #
        }
    },
    # --- 14. EMPLOYEE MANAGEMENT SYSTEM ---
    "EMPLOYEE_MANAGEMENT": {
        "HOUSING_APARTMENT_MANAGER": {
            "department": "Apartment management",  #
            "actions": ["view_unit", "change_tenancy", "link_rent_deduction"],  #
        },
        "CHEF_MPISH": {
            "department": "jikon",  #
            "actions": ["view_meal_plan", "update_kitchen_stock"],
        },
    },
    # --- 15. LOGISTIC AND TRANSPORT MANAGEMENT SYSTEM ---
    "LOGISTIC_TRANSPORT_MANAGEMENT": {
        "TRANSPORT_OFFICER": {
            "department": "Logistic officer",  #
            "actions": [
                "add_fleet",
                "view_vehicle",
                "change_vehicle",
                "view_driver",
            ],  #
        },
        "LEAD_TRANSPORT_OFFICER": {
            "department": "Logistic officer",  #
            "actions": ["approve_fuel_request", "manage_fleet_lifecycle"],
        },
        "SECURITY_BIO_EXCLUSION_OFFICER": {
            "department": "Safety and security",  #
            "actions": ["view_geofence", "view_telemetry", "check_biosecurity_log"],  #
        },
    },
    # --- 16. HOUSING MANAGEMENT SYSTEM ---
    "HOUSING_MANAGEMENT": {
        "MAINTENANCE_ENGINEER": {
            "department": "Infrastructure",  #
            "actions": [
                "view_building",
                "add_maintenance_request",
                "view_projectground",
            ],  #
        },
        "SENIOR_MAINTENANCE_ENGINEER": {
            "department": "Infrastructure",  #
            "actions": ["__all__"],
        },
    },
}
