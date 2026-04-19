"""
POULTRY PERSONNEL DICTIONARY
Module 9: Operational Role & Benefit Mapping
Description: This dictionary defines the specific roles, responsibilities,
and benefit packages for a scalable poultry ecosystem.
"""

POULTRY_PERSONNEL_DICTIONARY = {
    "ADMIN_MANAGEMENT": {
        "FARM_MANAGER": {
            "role_title": "General Farm Manager",
            "department": "Administration",
            "core_responsibilities": [
                "Overall flock lifecycle management",
                "Financial oversight and P&L accountability",
                "Supply chain coordination (Feed/Vaccine procurement)",
                "Resource allocation across all 9 modules",
            ],
            "benefits": {
                "monetary": [
                    "Performance-based profit sharing",
                    "Annual salary review",
                ],
                "allowances": ["Housing allowance", "Communication/Airtime stipend"],
                "health": ["Full medical cover for family"],
                "tools": ["Company vehicle", "Laptop/Tablet for API monitoring"],
            },
            "kpi_metrics": [
                "Overall Farm FCR",
                "Net Profit Margin",
                "Annual Batch Success Rate",
            ],
        },
        "ACCOUNTANT": {
            "role_title": "Farm Accountant / Financial Officer",
            "department": "Finance",
            "core_responsibilities": [
                "Ledger management and tax compliance",
                "Payroll processing for all employees",
                "Cost-center analysis for every bird batch",
                "Inventory valuation (Product vs. Waste)",
            ],
            "benefits": {
                "monetary": ["Professional membership fee coverage (CPA/ACCA)"],
                "allowances": ["Transport allowance"],
                "health": ["Standard individual medical cover"],
                "tools": ["Accounting software access", "High-security workstation"],
            },
            "kpi_metrics": [
                "Audit accuracy",
                "Payroll timeliness",
                "Expense variance reduction",
            ],
        },
    },
    "TECHNICAL_VETERINARY": {
        "VET_OFFICER": {
            "role_title": "Lead Veterinary Officer",
            "department": "Health & Biosecurity",
            "core_responsibilities": [
                "Designing vaccination and medication protocols",
                "Conducting post-mortems and disease diagnosis",
                "Enforcing strict biosecurity at farm entries",
                "Hatchery health audits",
            ],
            "benefits": {
                "monetary": ["Professional indemnity insurance"],
                "allowances": ["Hazard allowance", "Vehicle maintenance stipend"],
                "health": ["Enhanced medical cover (Chemical/Pathogen exposure)"],
                "tools": [
                    "Vet kit",
                    "Laboratory access",
                    "Cold-chain storage for vaccines",
                ],
            },
            "kpi_metrics": [
                "Mortality Rate %",
                "Vaccination Compliance",
                "Outbreak Response Time",
            ],
        },
        "NUTRITIONIST": {
            "role_title": "Poultry Nutritionist",
            "department": "Feed Management",
            "core_responsibilities": [
                "Formulating feed ratios for different growth stages",
                "Quality testing of raw materials (Maize, Soya, etc.)",
                "Optimizing feed cost vs. bird weight gain",
                "Monitoring silo storage conditions",
            ],
            "benefits": {
                "monetary": ["Research and Development (R&D) bonus"],
                "allowances": ["Standard transport allowance"],
                "health": ["Standard individual medical cover"],
                "tools": ["Feed analysis software", "Lab testing equipment"],
            },
            "kpi_metrics": [
                "Target FCR Achievement",
                "Feed Waste Reduction",
                "Raw Material Quality Score",
            ],
        },
    },
    "PRODUCTION_OPERATIONS": {
        "HATCHERY_OPERATOR": {
            "role_title": "Incubation & Hatchery Specialist",
            "department": "Breeding & Hatching",
            "core_responsibilities": [
                "Monitoring incubator temperature and humidity",
                "Executing candling and egg transfer processes",
                "Sorting and grading day-old chicks",
                "Maintaining hatchery hygiene (Sterilization)",
            ],
            "benefits": {
                "monetary": ["Production incentive per 1,000 chicks hatched"],
                "allowances": ["Shift allowance (Night monitoring)"],
                "health": ["Standard medical cover"],
                "tools": ["Protective hatchery gear", "Precision grading tools"],
            },
            "kpi_metrics": [
                "Hatchability %",
                "Chick Quality Grade A Rate",
                "Hatchery Mortality %",
            ],
        },
        "FLOCK_ATTENDANT": {
            "role_title": "Flock / Shed Attendant",
            "department": "Farm Management",
            "core_responsibilities": [
                "Daily bird feeding and water management",
                "Collection of eggs and mortality recording",
                "Maintaining litter quality and shed ventilation",
                "Reporting early signs of bird distress",
            ],
            "benefits": {
                "monetary": ["Overtime pay for weekend shifts"],
                "allowances": ["On-farm meal provision", "Laundry allowance (for PPE)"],
                "health": ["Vaccinations (Tetanus/Flu)"],
                "tools": ["Boots, Overalls, Respirators", "Daily log tablets"],
            },
            "kpi_metrics": [
                "Feed intake consistency",
                "Litter dryness score",
                "Daily log accuracy",
            ],
        },
    },
    "PROCESSING_LOGISTICS": {
        "SLAUGHTER_SUPERVISOR": {
            "role_title": "Processing Plant Supervisor",
            "department": "Processing & Packaging",
            "core_responsibilities": [
                "Overseeing slaughter and dressing quality",
                "Ensuring HACCP and Halal compliance",
                "Tracking yield percentages (Live vs. Dressed)",
                "Managing cold-room temperatures",
            ],
            "benefits": {
                "monetary": ["Hazard pay for machinery operation"],
                "allowances": ["Protective clothing allowance"],
                "health": ["Annual respiratory and health checkups"],
                "tools": ["Processing line equipment", "Cold-chain monitoring tools"],
            },
            "kpi_metrics": [
                "Yield % Optimization",
                "Processing Speed",
                "Zero-Contamination Score",
            ],
        },
        "LOGISTICS_AGENT": {
            "role_title": "Delivery & Sales Agent",
            "department": "Product Management",
            "core_responsibilities": [
                "Safe transport of live or processed products",
                "Managing customer delivery orders via API",
                "Ensuring vehicle cleanliness (Bio-exclusion)",
                "Collection of payments for cash-on-delivery",
            ],
            "benefits": {
                "monetary": ["Sales commission per order fulfilled"],
                "allowances": ["Fuel and Airtime allowance"],
                "health": ["Personal accident insurance"],
                "tools": ["GPS tracking device", "Mobile POS terminal"],
            },
            "kpi_metrics": [
                "On-time Delivery %",
                "Vehicle Up-time",
                "Customer Satisfaction Score",
            ],
        },
    },
    "ESTATE_RECREATION_MANAGEMENT": {
        "PROPERTY_MANAGER": {
            "role_title": "Housing & Apartment Manager",
            "department": "Apartment Management (Module 11)",
            "core_responsibilities": [
                "Managing tenant (wapangaji) onboarding and lease agreements",
                "Overseeing rent collection and utility billing (LUKU/Water)",
                "Coordinating unit maintenance and repairs",
                "Handling staff housing allocation for farm employees",
            ],
            "benefits": {
                "monetary": ["Commission on new external tenant acquisition"],
                "allowances": ["Communication allowance", "Commuter allowance"],
                "health": ["Standard health cover"],
                "tools": ["Property Management Dashboard access", "Mobile Work Phone"],
            },
            "kpi_metrics": [
                "Occupancy Rate %",
                "Rent Collection Timeliness",
                "Maintenance Response Time",
            ],
        },
        "RECREATION_SUPERVISOR": {
            "role_title": "Playground & Leisure Supervisor",
            "department": "Recreation Management (Module 12)",
            "core_responsibilities": [
                "Managing visitor entry and enjoyment zone safety",
                "Organizing events (Birthdays, Group retreats, Garden visits)",
                "Maintaining the 'Green View' and playground equipment",
                "Customer service for visitors coming for reassurance",
            ],
            "benefits": {
                "monetary": ["Event-based bonuses (per booked party)"],
                "allowances": ["Hospitality allowance", "Weekend shift premium"],
                "health": ["Standard medical cover"],
                "tools": ["Ticketing system access", "Safety inspection kit"],
            },
            "kpi_metrics": [
                "Visitor Satisfaction Score",
                "Zone Utilization Rate",
                "Safety Incident Zero-Rate",
            ],
        },
        "GARDENER_LANDSCAPER": {
            "role_title": "Grounds & Greenery Keeper",
            "department": "Recreation Management (Module 12)",
            "core_responsibilities": [
                "Maintaining the playground lawns and garden aesthetics",
                "Applying fertilizer and irrigation to green spaces",
                "Daily cleaning of recreational zones",
                "Ensuring farm-stay aesthetics meet enjoyment standards",
            ],
            "benefits": {
                "monetary": ["Seasonal performance bonus"],
                "allowances": ["Protective gear (PPE) allowance", "Lunch provided"],
                "health": ["Tetanus and respiratory checkups"],
                "tools": ["Landscaping tools", "Automated irrigation controls"],
            },
            "kpi_metrics": [
                "Garden Health Score",
                "Aesthetic Cleanliness Rating",
                "Tool Maintenance Log Accuracy",
            ],
        },
    },
}


SUPPLEMENTAL_ROLES = {
    "INFRASTRUCTURE_MAINTENANCE": {
        "BIOGAS_EQUIPMENT_TECHNICIAN": {
            "role_title": "Senior Maintenance Engineer",
            "department": "Infrastructure",
            "core_responsibilities": [
                "Maintaining automated feeding systems and hatchery incubators",
                "Managing farm waste-to-energy (Biogas) systems",
                "Repairing electrical and plumbing issues in Rental Units (Module 11)",
                "Maintaining playground mechanical rides and irrigation (Module 12)",
            ],
            "benefits": {
                "monetary": ["On-call emergency allowance"],
                "allowances": [
                    "Mobile workshop/tool allowance",
                    "Transport for site-to-site travel",
                ],
                "health": ["Standard health cover with injury riders"],
                "tools": ["Engineering toolkit", "Digital diagnostic multimeters"],
            },
            "kpi_metrics": [
                "Asset Up-time %",
                "Preventative Maintenance Compliance",
                "Repair Turnaround Time",
            ],
        }
    },
    "HOSPITALITY_EXPERIENCE": {
        "EVENT_COORDINATOR": {
            "role_title": "Hospitality & Farm-Stay Host",
            "department": "Recreation Management (Module 12)",
            "core_responsibilities": [
                "Greeting visitors at 'Enjoyment Locations'",
                "Organizing guided 'Farm Tours' for students and tourists",
                "Managing bookings for the green view lounges",
                "Coordinating catering for on-site parties/retreats",
            ],
            "benefits": {
                "monetary": ["Commission on event sales"],
                "allowances": ["Entertainment/Hospitality stipend"],
                "health": ["Standard health cover"],
                "tools": [
                    "Event management software",
                    "Uniform/Professional attire allowance",
                ],
            },
            "kpi_metrics": [
                "Guest Satisfaction Score (CSAT)",
                "Repeat Visit Rate",
                "Event Revenue per SQM",
            ],
        }
    },
    "PROTECTION_BIOSECURITY": {
        "BIOSECURITY_GUARD": {
            "role_title": "Security & Bio-Exclusion Officer",
            "department": "Safety & Security",
            "core_responsibilities": [
                "Monitoring farm perimeter and entry/exit logs",
                "Enforcing disinfection protocols for vehicles and visitors",
                "Patrolling the Recreation Zone and Apartment blocks",
                "Preventing theft of birds, feed, and tenant property",
            ],
            "benefits": {
                "monetary": ["Night-shift hazard pay"],
                "allowances": ["Uniform and combat boot allowance", "On-site housing"],
                "health": ["Life insurance and accidental disability cover"],
                "tools": [
                    "Biometric logging system",
                    "Patrol vehicle/bicycle",
                    "CCTV monitoring access",
                ],
            },
            "kpi_metrics": [
                "Security Incident Rate (Zero-target)",
                "Biosecurity Protocol Adherence %",
                "Response Time to Alarms",
            ],
        }
    },
    "DIGITAL_SYSTEMS_SUPPORT": {
        "COMMUNICATIONS_MODERATOR": {
            "role_title": "Digital Platform & Community Coordinator",
            "department": "Unified Communication (Module 13)",
            "core_responsibilities": [
                "Managing internal and external chat channels",
                "Training AI bots for automated customer/tenant replies",
                "Moderating community forums for the Recreation Zone (Module 12)",
                "Analyzing communication logs for operational bottlenecks",
            ],
            "benefits": {
                "monetary": ["Digital efficiency bonus"],
                "allowances": ["High-speed data/internet stipend"],
                "health": ["Standard medical cover"],
                "tools": [
                    "Admin access to Chat API",
                    "Advanced data analytics dashboard",
                ],
            },
            "kpi_metrics": [
                "Bot Resolution Rate %",
                "Average Response Time",
                "User Engagement Score",
            ],
        }
    },
    "ENVIRONMENTAL_SANITATION": {
        "WASTE_MANAGEMENT_OFFICER": {
            "role_title": "Sanitation & Waste Supervisor",
            "department": "Waste Management (Module 14)",
            "core_responsibilities": [
                "Managing collection schedules for farm manure and residential trash",
                "Ensuring medical waste (from Module 4) is incinerated safely",
                "Optimizing the sale of organic fertilizer to local farmers",
                "Maintaining the cleanliness of waste transit zones",
            ],
            "benefits": {
                "monetary": ["Hazard pay for handling biological waste"],
                "allowances": [
                    "Extra uniform/PPE allowance",
                    "Sanitation soap stipend",
                ],
                "health": ["Monthly respiratory and skin health screenings"],
                "tools": [
                    "Waste tracking scales",
                    "Incinerator control access",
                    "Protective gears",
                ],
            },
            "kpi_metrics": [
                "Waste Segregation Accuracy %",
                "Revenue from By-products",
                "Site Cleanliness Score",
            ],
        }
    },
    "SYSTEM_ADMINISTRATION": {
        "DATA_INTEGRITY_OFFICER": {
            "role_title": "Database & Systems Auditor",
            "department": "IT / Admin",
            "core_responsibilities": [
                "Reviewing the 'Trash' (Module 15) to ensure no unauthorized deletions",
                "Restoring data accidentally deleted by farm managers",
                "Performing the 'Permanent Purge' of trash items older than 30 days",
                "Auditing system logs to maintain data flow integrity",
            ],
            "benefits": {
                "monetary": ["Security clearance bonus"],
                "allowances": ["Remote work stipend"],
                "health": ["Standard individual medical cover"],
                "tools": ["Super-Admin API Keys", "Encrypted workstation"],
            },
            "kpi_metrics": [
                "Data Recovery Rate",
                "Unauthorized Deletion Rate",
                "Audit Log Accuracy",
            ],
        }
    },
}
