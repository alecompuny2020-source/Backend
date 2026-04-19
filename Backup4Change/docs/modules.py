# The "Wonderful" 2026 Enterprise Project Roadmap
# This dictionary splits each model category into functional modules
# for granular API implementation.

PROJECT_MODULE_MAP = {
    "AUTHENTICATION_&_IDENTITY": {
        "user_models": ["UserProfiles", "Permissions", "AuthAudit", "JidManagement"]
    },
    "CORE_INFRASTRUCTURE": {
        "registration_models": [
            "EntityRegistration",
            "LicenseManagement",
            "Certifications",
        ],
        "pground_models": ["ProjectGrounds", "SiteMaps", "GeoFencing"],
    },
    "LIVESTOCK_OPERATIONS": {
        "farm_models": ["FarmLocations", "FlockManagement", "ProductionCycles"],
        "breeding_models": ["BreedingPrograms", "Incubation", "GeneticsTracking"],
        "health_models": [
            "VaccinationSchedules",
            "DiseaseMonitoring",
            "VetInterventions",
        ],
        "housing_models": ["PenManagement", "ClimateControl", "HousingAssignments"],
    },
    "RESOURCE_MANAGEMENT": {
        "employee_models": [
            "HRProfile",
            "PayrollSystem",
            "NextOfKin",
            "ShiftSchedules",
        ],
        "feed_models": [
            "FeedFormulation",
            "NutritionalTracking",
            "ConsumptionAnalysis",
        ],
        "waste_models": ["ByProductTracking", "DisposalLogs", "EnvironmentalImpact"],
    },
    "SUPPLY_CHAIN_&_REVENUE": {
        "inventory_models": [
            "WarehouseOps",
            "StorageUnits",
            "ReadinessTracking",
            "StockMovements",
        ],
        "processing_models": ["SlaughterhouseOps", "PackagingLogic", "QualityControl"],
        "sales_models": [
            "CRM",
            "OrderManagement",
            "PricingStrategies",
            "KioskInterface",
        ],
        "shipping_models": ["CarrierManagement", "DispatchLogs", "DeliveryProof"],
    },
    "FINANCIAL_ENGINE": {
        "expenses_models": ["Procurement", "PayeeDatabase", "OpExTracking"],
        "accounting_models": ["GeneralLedger", "AccountsReceivable", "BalanceSheet"],
        "charting_models": ["FinancialAnalytics", "ReportingEngine", "KPI_Dashboard"],
    },
}
