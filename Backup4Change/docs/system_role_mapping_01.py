# Enterprise System Role Mapping
# Separation of Concern: Actor -> Department -> Granular System -> Actions

SYSTEM_ROLE_MAPPING = {
    "RECREATION_ZONE_MANAGEMENT_SYSTEM": {
        "mpambaji": {
            "department": "decollations",
            "actions": ["add_decoration", "view_event_layout", "manage_inventory"],
        },
        "Hospitality and ukaribishaji": {
            "department": "Recreation management",
            "actions": ["check_in_guest", "view_facility_status", "add_booking"],
        },
        "Ground and greenery keeper": {
            "department": "Recreation management",
            "actions": ["update_landscape_log", "view_irrigation_schedule"],
        },
        "Playground and leisure supervisor": {
            "department": "Recreation management",
            "actions": ["view_geofence", "monitor_equipment_safety"],
        },
        "Lead Ground and greenery keeper": {
            "department": "Recreation management",
            "actions": ["approve_landscape_plan", "manage_ground_staff"],
        },
        "Lead Playground and leisure supervisor": {
            "department": "Recreation management",
            "actions": ["manage_leisure_policy", "view_safety_audit"],
        },
    },
    "POULTRY_FARM_MANAGEMENT_INFORMATION_SYSTEM": {
        "Flock and shed attendant": {
            "department": "Farm management",
            "actions": ["add_feeding_log", "view_flock_status", "update_shed_data"],
        },
        "Farm manager": {
            "department": "Administration",
            "actions": ["view_production_kpi", "approve_farm_requisition"],
        },
    },
    "BREEDING_AND_HATCHERY_MANAGEMENT_SYSTEM": {
        "Incubator and Hatchery specialist": {
            "department": "Breeding and hatching",
            "actions": ["add_incubation_log", "view_genetics", "monitor_hatch_rate"],
        }
    },
    "FEED_MANAGEMENT_SYSTEM": {
        "Nutritionist": {
            "department": "Feed management",
            "actions": ["add_formula", "view_feed_stock", "manage_ingredients"],
        },
        "Lead Nutritionist": {
            "department": "Feed management",
            "actions": ["approve_formula", "manage_feed_suppliers"],
        },
    },
    "POULTRY_HEALTH_MANAGEMENT_SYSTEM": {
        "Veterinary officer": {
            "department": "Heath and bio-security",
            "actions": [
                "add_intervention",
                "view_health_record",
                "prescribe_medication",
            ],
        },
        "Lead Veterinary officer": {
            "department": "Heath and bio-security",
            "actions": ["manage_health_policy", "view_outbreak_alerts"],
        },
    },
    "USER_INFORMATION_MANAGEMENT_SYSTEM": {
        "System Administrator": {
            "department": "ICT",
            "actions": ["add_user", "change_user", "assign_role", "view_audit_log"],
        },
        "Network Administrator": {
            "department": "ICT",
            "actions": ["manage_network_access", "monitor_traffic"],
        },
        "Cyber security Officer": {
            "department": "ICT",
            "actions": ["audit_system_security", "view_incident_report"],
        },
        "ICT_Officer": {
            "department": "ICT",
            "actions": ["support_ticket_resolution", "manage_it_assets"],
        },
    },
    "WASTE_MANAGEMENT_SYSTEM": {
        "sanitation and waste supervisor (watu wa usafi)": {
            "department": "Waste management",
            "actions": ["add_waste_log", "view_disposal_points"],
        },
        "Lead sanitation and waste supervisor": {
            "department": "Waste management",
            "actions": ["manage_waste_contracts", "view_sanitation_compliance"],
        },
    },
    "EXPENSES_TRACKING_SYSTEM": {
        "Financial officer or muhasibu": {
            "department": "finance",
            "actions": ["add_expense", "view_reimbursement", "approve_payment"],
        }
    },
    "COMMUNICATION_AND_MEDIA_INFORMATION_MANAGEMENT_SYSTEM": {
        "Content creator": {
            "department": "Media and communication management",
            "actions": ["add_media", "view_engagement_metrics"],
        },
        "Digital platform and community coordinator": {
            "department": "Media and communication management",
            "actions": ["manage_social_channels", "moderate_community"],
        },
    },
    "FINANCE_SYSTEM": {
        "Financial officer or muhasibu": {
            "department": "finance",
            "actions": ["view_cashflow", "manage_tax_records"],
        }
    },
    "POULTRY_FARM_ACCOUNTING_SYSTEM": {
        "Financial officer or muhasibu": {
            "department": "finance",
            "actions": ["view_ledger", "view_balance_sheet", "process_invoice"],
        }
    },
    "POULTRY_PRODUCTION_MANAGEMENT_SYSTEM": {
        "General Farm manager": {
            "department": "Administration",
            "actions": ["view_production_cycle", "manage_resource_allocation"],
        }
    },
    "POULTRY_PROCESSING_MANAGEMENT_SYSTEM": {
        "Processing plant supervisor": {
            "department": "Processing and packaging",
            "actions": ["view_processing_line", "update_yield_data"],
        },
        "Chef/ mpish": {
            "department": "jikon",
            "actions": ["view_available_stock", "update_meal_prep"],
        },
    },
    "EMPLOYEE_MANAGEMENT_SYSTEM": {
        "System Administrator": {
            "department": "ICT",
            "actions": ["manage_employee_profile", "view_payroll_linkage"],
        }
    },
    "LOGISTIC_AND_TRANSPORT_MANAGEMENT_SYSTEM": {
        "Transport Officer": {
            "department": "Logistic officer",
            "actions": ["add_fleet", "view_vehicle", "change_vehicle", "view_driver"],
        },
        "Lead Transport Officer": {
            "department": "Logistic officer",
            "actions": ["approve_fuel_request", "manage_fleet_lifecycle"],
        },
        "Security and bio-exclusion officer": {
            "department": "Safety and security",
            "actions": ["view_geofence", "view_telemetry", "check_biosecurity_log"],
        },
        "Lead Security and bio-exclusion officer": {
            "department": "Safety and security",
            "actions": ["manage_security_protocol", "view_incident_log"],
        },
    },
    "HOUSING_MANAGEMENT_SYSTEM": {
        "Housing and apartment manager": {
            "department": "Apartment management",
            "actions": ["view_unit", "change_tenancy", "link_rent_deduction"],
        },
        "Lead Housing and apartment manager": {
            "department": "Apartment management",
            "actions": ["approve_lease", "manage_property_portfolio"],
        },
        "Maintenance engineer": {
            "department": "Infrastructure",
            "actions": ["view_building", "add_maintenance_request"],
        },
        "Senior Maintenance engineer": {
            "department": "Infrastructure",
            "actions": ["approve_work_order", "view_infrastructure_kpi"],
        },
    },
    "PRODUCT_MANAGEMENT_SYSTEM": {
        "Sales agent": {
            "department": "Product management",
            "actions": ["view_stock", "add_sales_order"],
        },
        "Delivery and sale agent": {
            "department": "Product management",
            "actions": ["view_delivery_schedule", "update_order_status"],
        },
        "Manager masoko": {
            "department": "Product management",
            "actions": ["view_sales_analytics", "manage_marketing_campaign"],
        },
        "Packaging manager": {
            "department": "Processing and packaging",
            "actions": ["view_inventory", "add_stock_movement"],
        },
    },
    "EXTERNAL_VISITOR_SYSTEM": {
        "Visitors / Customer /": {
            "department": "External",
            "actions": ["view_product", "place_order", "send_feedback"],
        }
    },
}
