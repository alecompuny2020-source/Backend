from django.utils.translation import gettext_lazy as _

# Complete mapping of Role Titles to Department metadata.
# This ensures that when a Group is created, the system knows which Department to link it to.

DEPARTMENT_DICTIONARY = {
    # --- Executive & Admin ---
    "Chief Executive Officer": {
        "name": "Executive Office",
        "code": "EXEC",
        "description": _("Top-level strategy, enterprise P&L, and global decision making.")
    },
    "System Administrator": {
        "name": "IT / Admin",
        "code": "ITAD",
        "description": _("System health, user access control, and data integrity oversight.")
    },
    "General Farm Manager": {
        "name": "Administration",
        "code": "ADMIN",
        "description": _("Overall flock lifecycle management and resource allocation.")
    },
    "Farm Manager": {
        "name": "Administration",
        "code": "ADMIN",
        "description": _("Day-to-day management of farm modules and staff coordination.")
    },
    "Treasurer": {
        "name": "Finance",
        "code": "FIN",
        "description": _("Financial records, treasury management, and budget tracking.")
    },

    # --- Human Resources ---
    "Human Resource Manager": {
        "name": "Human Resource",
        "code": "HR",
        "description": _("Staffing strategy, payroll management, and employee relations.")
    },
    "Human Resource Officer": {
        "name": "Human Resource",
        "code": "HR",
        "description": _("Personnel record keeping and daily HR administrative tasks.")
    },
    "Recruitment Manager": {
        "name": "Human Resource",
        "code": "HR",
        "description": _("Talent acquisition and onboarding processes.")
    },

    # --- Logistics & Transport ---
    "Lead Transport Officer": {
        "name": "Logistics and Transport",
        "code": "LOGS",
        "description": _("Fleet oversight, delivery scheduling, and logistics strategy.")
    },
    "Transport Officer": {
        "name": "Logistics and Transport",
        "code": "LOGS",
        "description": _("Vehicle dispatch, shipment tracking, and delivery execution.")
    },
    "Derivery and Sales Agent": {
        "name": "Logistics and Transport",
        "code": "LOGS",
        "description": _("Field sales and product delivery coordination.")
    },

    # --- Recreation & Hospitality ---
    "Receptionist": {
        "name": "Recreation management",
        "code": "RECM",
        "description": _("Front-desk operations and guest check-ins.")
    },
    "Lead Ground and Greenery Keeper": {
        "name": "Recreation management",
        "code": "RECM",
        "description": _("Oversight of landscaping and greenery maintenance.")
    },
    "Ground and Greenery Keeper": {
        "name": "Recreation management",
        "code": "RECM",
        "description": _("Daily landscaping, gardening, and site aesthetics.")
    },
    "Lead Playground and Leisure Supervisor": {
        "name": "Recreation management",
        "code": "RECM",
        "description": _("Supervision of leisure zones and equipment safety standards.")
    },
    "Playground and Leisure Supervisor": {
        "name": "Recreation management",
        "code": "RECM",
        "description": _("Monitoring of leisure activities and equipment usage.")
    },

    # --- Health, Bio-Security & Sanitation ---
    "Lead Veterinary Officer": {
        "name": "Health and Bio-Security",
        "code": "HLTH",
        "description": _("Head of veterinary services and bio-exclusion protocols.")
    },
    "Veterinary Officer": {
        "name": "Health and Bio-Security",
        "code": "HLTH",
        "description": _("Flock health monitoring and medical treatment.")
    },
    "Security and Bio-exclusion Officer": {
        "name": "Security & Bio-security",
        "code": "SEC",
        "description": _("Site security and implementation of bio-security barriers.")
    },
    "Lead Sanitation and Waster Supervisor": {
        "name": "Sanitation & Waste",
        "code": "WASH",
        "description": _("Waste management strategy and sanitation compliance.")
    },
    "Sanitation and Waster Supervisor": {
        "name": "Sanitation & Waste",
        "code": "WASH",
        "description": _("Execution of sanitation protocols and waste disposal.")
    },
    "Decollation Officer": {
        "name": "decollations",
        "code": "DECO",
        "description": _("Management of event layouts and venue decorations.")
    },

    # --- Production & Specialized Technical ---
    "Lead Nutritionist": {
        "name": "Nutrition & Feed Management",
        "code": "NUTR",
        "description": _("Feed formulation and nutritional quality control.")
    },
    "Nutritionist": {
        "name": "Nutrition & Feed Management",
        "code": "NUTR",
        "description": _("Monitoring bird nutritional intake and feed conversion.")
    },
    "Incubation and Hatchery Specialist": {
        "name": "Hatchery & Breeding",
        "code": "HATCH",
        "description": _("Management of incubator settings and hatchling care.")
    },
    "Flock and Shed Attendant": {
        "name": "Production",
        "code": "PROD",
        "description": _("Daily care of birds and maintenance of shed conditions.")
    },

    # --- Engineering & Maintenance ---
    "Senior Maintainance Engineer": {
        "name": "Maintenance & Engineering",
        "code": "ENGR",
        "description": _("Overseeing complex repairs and facility infrastructure.")
    },
    "Maintainance Engineer": {
        "name": "Maintenance & Engineering",
        "code": "ENGR",
        "description": _("Routine equipment maintenance and infrastructure repair.")
    },
    "Lead Housing and Apartment Manager": {
        "name": "Housing & Facility",
        "code": "HOUS",
        "description": _("Management of staff housing and apartment facilities.")
    },
    "Housing and Apartment Manager": {
        "name": "Housing & Facility",
        "code": "HOUS",
        "description": _("Apartment allocation and facility utility monitoring.")
    },

    # --- Processing & Sales ---
    "Processing Plant Supervisor": {
        "name": "Processing & Value Addition",
        "code": "PROC",
        "description": _("Supervising slaughter, processing, and plant safety.")
    },
    "Packaging Manager": {
        "name": "Processing & Value Addition",
        "code": "PROC",
        "description": _("Managing packaging inventory and product labelling.")
    },
    "Senior Chef": {
        "name": "Processing & Value Addition",
        "code": "PROC",
        "description": _("Culinary management for value-added poultry products.")
    },
    "Chef": {
        "name": "Processing & Value Addition",
        "code": "PROC",
        "description": _("Preparation of food products and kitchen management.")
    },
    "Marketing Manager": {
        "name": "Sales & Marketing",
        "code": "MKTG",
        "description": _("Brand management and sales campaign strategy.")
    },
    "Sales Agent": {
        "name": "Sales & Marketing",
        "code": "MKTG",
        "description": _("Direct customer engagement and sales execution.")
    },

    # --- Digital & Content ---
    "Digital Platform and Community Cordinator": {
        "name": "IT / Admin",
        "code": "ITAD",
        "description": _("Management of online communities and platform engagement.")
    },
    "Content Creator": {
        "name": "IT / Admin",
        "code": "ITAD",
        "description": _("Developing digital content for marketing and training.")
    },

    # --- External Roles ---
    "Customer": {
        "name": "External",
        "code": "EXT",
        "description": _("External clients purchasing products or services.")
    },
    "Visitor": {
        "name": "External",
        "code": "EXT",
        "description": _("Temporary guests accessing limited site facilities.")
    },
    "Tenant": {
        "name": "External",
        "code": "EXT",
        "description": _("External parties renting facility space or apartments.")
    },
}
