# System Role Mapping for an Enterprise
# Separation of Concern: Maps Actors -> Departments -> Systems -> Actions


SYSTEM_ROLE_MAPPING = {
    # --- 1. RECREATION & HOSPITALITY MANAGEMENT SYSTEM ---
    "RECREATION_ZONE_MANAGEMENT_SYSTEM": {
        "HOSPITALITY_COORDINATOR": {
            "department": "Recreation management",
            "actions": [
                "check_in_guest",
                "view_facility_status",
                "add_booking",
                "process_ticket_sale",
            ],
        },
        "MPAMBAJI_DECOR_SPECIALIST": {
            "department": "decollations",
            "actions": [
                "add_decoration",
                "view_event_layout",
                "manage_decoration_inventory",
                "update_venue_setup",
            ],
        },
        "GROUND_GREENERY_KEEPER": {
            "department": "Recreation management",
            "actions": [
                "update_landscape_log",
                "view_irrigation_schedule",
                "report_equipment_fault",
            ],
        },
        "LEAD_GROUND_GREENERY_KEEPER": {
            "department": "Recreation management",
            "actions": [
                "approve_landscape_plan",
                "manage_ground_staff",
                "view_infrastructure_kpi",
            ],
        },
        "PLAYGROUND_LEISURE_SUPERVISOR": {
            "department": "Recreation management",
            "actions": ["view_geofence", "monitor_equipment_safety", "report_incident"],
        },
        "LEAD_PLAYGROUND_LEISURE_SUPERVISOR": {
            "department": "Recreation management",
            "actions": [
                "manage_leisure_policy",
                "view_safety_audit",
                "assign_supervisor_shifts",
            ],
        },
    },
    # --- 2. POULTRY FARM MANAGEMENT INFORMATION SYSTEM ---
    "POULTRY_FARM_MANAGEMENT_SYSTEM": {
        "FLOCK_SHED_ATTENDANT": {
            "department": "Farm management",
            "actions": [
                "add_daily_observation",
                "log_mortality",
                "update_water_intake",
                "log_egg_collection",
            ],
        },
        "FARM_MANAGER": {
            "department": "Administration",
            "actions": [
                "approve_batch_movement",
                "view_kpi_dashboard",
                "assign_shed_worker",
                "manage_biosecurity_lockdown",
            ],
        },
        "HATCHERY_SPECIALIST": {
            "department": "Breeding and Hatchery",
            "actions": [
                "manage_incubation_cycle",
                "log_hatch_results",
                "update_breeder_traits",
                "check_egg_fertility",
            ],
        },
        "VETERINARY_OFFICER": {
            "department": "Animal Health",
            "actions": [
                "prescribe_medication",
                "log_vaccination",
                "declare_disease_outbreak",
                "issue_health_clearance",
            ],
        },
    },
    # --- 3. FEED & NUTRITION SYSTEM ---
    "FEED_NUTRITION_MANAGEMENT_SYSTEM": {
        "FEED_MILL_OPERATOR": {
            "department": "Production",
            "actions": [
                "log_feed_production",
                "view_feed_formula",
                "update_ingredient_stock",
            ],
        },
        "NUTRITIONIST": {
            "department": "Research and Development",
            "actions": [
                "update_composition_metadata",
                "analyze_fcr_performance",
                "approve_new_feed_brand",
            ],
        },
    },
    # --- 4. PROCESSING PLANT MANAGEMENT SYSTEM ---
    "PROCESSING_PLANT_MANAGEMENT_SYSTEM": {
        "PLANT_OPERATIVE": {
            "department": "Processing",
            "actions": [
                "log_slaughter_count",
                "record_dressed_weight",
                "update_environmental_logs",
                "log_reject_reason",
            ],
        },
        "PACKAGING_MANAGER": {
            "department": "Processing and packaging",
            "actions": [
                "generate_label_code",
                "verify_seal_integrity",
                "update_packaged_stock",
                "view_inventory_levels",
            ],
        },
        "QUALITY_ASSURANCE_OFFICER": {
            "department": "Safety and Compliance",
            "actions": [
                "inspect_chiller_temp",
                "verify_halal_compliance",
                "reject_contaminated_batch",
                "audit_hygiene_standards",
            ],
        },
    },
    # --- 5. HUMAN RESOURCE & ONBOARDING SYSTEM ---
    "HUMAN_RESOURCE_MANAGEMENT_SYSTEM": {
        "HR_OFFICER": {
            "department": "Human Resources",
            "actions": [
                "register_employee",
                "verify_id_documents",
                "update_employment_type",
                "terminate_contract",
            ],
        },
        "RECRUITMENT_MANAGER": {
            "department": "Human Resources",
            "actions": [
                "post_job_opening",
                "view_applicant_profile",
                "onboard_new_hire",
                "schedule_interview",
            ],
        },
        "TRAINING_COORDINATOR": {
            "department": "Human Resources",
            "actions": [
                "assign_training_module",
                "view_employee_certifications",
                "update_skills_matrix",
            ],
        },
    },
    # --- 6. PAYROLL & FINANCIAL LEDGER SYSTEM ---
    "PAYROLL_FINANCIAL_SYSTEM": {
        "PAYROLL_ACCOUNTANT": {
            "department": "Finance",
            "actions": [
                "generate_payroll_record",
                "approve_benefits",
                "process_tax_deductions",
                "view_net_pay_report",
            ],
        },
        "CASHIER_PISH_AGENT": {
            "department": "Finance",
            "actions": [
                "process_cash_disbursement",
                "update_payment_status",
                "verify_mobile_money_ref",
            ],
        },
    },
    # --- 7. LOGISTICS & FLEET MANAGEMENT SYSTEM ---
    "LOGISTICS_TRANSPORT_MANAGEMENT_SYSTEM": {
        "TRANSPORT_OFFICER": {
            "department": "Logistic officer",
            "actions": [
                "add_fleet",
                "view_vehicle",
                "change_vehicle",
                "view_driver",
                "assign_vehicle",
            ],
        },
        "LEAD_TRANSPORT_OFFICER": {
            "department": "Logistic officer",
            "actions": [
                "approve_fuel_request",
                "manage_fleet_lifecycle",
                "view_maintenance_schedule",
            ],
        },
        "FLEET_DRIVER": {
            "department": "Logistics",
            "actions": [
                "update_trip_telemetry",
                "log_fuel_consumption",
                "report_vehicle_fault",
                "update_cargo_temp",
            ],
        },
        "SECURITY_BIO_EXCLUSION_OFFICER": {
            "department": "Safety and security",
            "actions": [
                "view_geofence",
                "view_telemetry",
                "check_biosecurity_log",
                "verify_vehicle_disinfection",
            ],
        },
    },
    # --- 8. INVENTORY & PRODUCT STOCK SYSTEM ---
    "PRODUCT_INVENTORY_MANAGEMENT_SYSTEM": {
        "WAREHOUSE_KEEPER": {
            "department": "Storage",
            "actions": [
                "update_stock_count",
                "log_stock_movement",
                "verify_storage_temperature",
                "process_restock",
            ],
        },
        "PROCUREMENT_OFFICER": {
            "department": "Supply Chain",
            "actions": [
                "view_low_stock_alerts",
                "create_purchase_order",
                "manage_vendor_list",
                "evaluate_supplier",
            ],
        },
    },
    # --- 9. HOUSING & TENANCY MANAGEMENT SYSTEM ---
    "HOUSING_TENANCY_MANAGEMENT_SYSTEM": {
        "APARTMENT_MANAGER": {
            "department": "Apartment management",
            "actions": [
                "view_unit",
                "change_tenancy",
                "link_rent_deduction",
                "manage_lease_agreement",
            ],
        },
        "LEAD_HOUSING_MANAGER": {
            "department": "Apartment management",
            "actions": [
                "approve_lease",
                "manage_property_portfolio",
                "audit_tenant_payments",
            ],
        },
    },
    # --- 10. INFRASTRUCTURE & MAINTENANCE SYSTEM ---
    "INFRASTRUCTURE_MAINTENANCE_SYSTEM": {
        "MAINTENANCE_ENGINEER": {
            "department": "Infrastructure",
            "actions": [
                "view_building",
                "add_maintenance_request",
                "update_repair_status",
                "log_spare_parts",
            ],
        },
        "SENIOR_MAINTENANCE_ENGINEER": {
            "department": "Infrastructure",
            "actions": [
                "approve_work_order",
                "view_infrastructure_kpi",
                "schedule_preventive_maintenance",
            ],
        },
    },
    # --- 11. WASTE & CIRCULAR ECONOMY SYSTEM ---
    "WASTE_MANAGEMENT_SYSTEM": {
        "WASTE_COORDINATOR": {
            "department": "Sanitation",
            "actions": [
                "log_waste_collection",
                "record_disposal_method",
                "manage_recycling_outflow",
            ],
        },
        "ENVIRONMENTAL_AUDITOR": {
            "department": "Compliance",
            "actions": [
                "view_emission_logs",
                "verify_hazardous_disposal",
                "generate_sustainability_report",
            ],
        },
    },
    # --- 12. SALES & RETAIL SYSTEM ---
    "SALES_RETAIL_MANAGEMENT_SYSTEM": {
        "SALES_AGENT": {
            "department": "Product management",
            "actions": ["view_stock", "add_sales_order", "process_refund"],
        },
        "DELIVERY_AND_SALE_AGENT": {
            "department": "Product management",
            "actions": [
                "view_delivery_schedule",
                "update_order_status",
                "collect_customer_signature",
            ],
        },
        "MARKETING_MANAGER_MASOKO": {
            "department": "Product management",
            "actions": [
                "view_sales_analytics",
                "manage_marketing_campaign",
                "update_product_pricing",
            ],
        },
    },
    # --- 13. KITCHEN & CATERING SYSTEM ---
    "KITCHEN_MANAGEMENT_SYSTEM": {
        "CHEF_MPISHI": {
            "department": "jikon",
            "actions": [
                "view_meal_plan",
                "update_kitchen_stock",
                "log_meal_distribution",
            ],
        }
    },
    # --- 14. SECURITY & SURVEILLANCE SYSTEM ---
    "SECURITY_MANAGEMENT_SYSTEM": {
        "SECURITY_GUARD": {
            "department": "Safety and security",
            "actions": [
                "log_entry_exit",
                "report_security_breach",
                "view_perimeter_status",
            ],
        }
    },
    # --- 15. EXTERNAL CUSTOMER & VISITOR SYSTEM ---
    "EXTERNAL_VISITOR_SYSTEM": {
        "VISITOR_CUSTOMER": {
            "department": "External",
            "actions": [
                "browse_products",
                "add_to_cart",
                "submit_review",
                "update_own_profile",
                "track_order",
            ],
        }
    },
    # --- 16. LEGAL & REGISTRATION HISTORY SYSTEM ---
    "LEGAL_REGISTRATION_AUDIT_SYSTEM": {
        "LEGAL_OFFICER": {
            "department": "Legal",
            "actions": [
                "verify_registration_history",
                "audit_contracts",
                "view_tenant_registration_logs",
            ],
        }
    },
    # --- 17. EXECUTIVE STRATEGY & GLOBAL CONTROL ---
    "EXECUTIVE_MANAGEMENT_SYSTEM": {
        "CHIEF_FINANCIAL_OFFICER": {
            "department": "Executive Office",
            "actions": [
                "view_enterprise_pnl",
                "approve_large_expenditure",
                "audit_payroll_summary",
                "view_tax_compliance",
            ],
        },
        "INTERNAL_AUDITOR": {
            "department": "Internal Audit",
            "actions": [
                "view_action_logs",
                "verify_stock_reconciliation",
                "check_system_overrides",
                "audit_health_protocols",
            ],
        },
        "CHIEF_EXECUTIVE_OFFICER": {
            "department": "Executive Office",
            "actions": ["__all__"],
        },
    },
}
