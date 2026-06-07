# =====================================================================
# 1. BASE VERB GROUPS (Granular reusable permission arrays)
# =====================================================================

# Standard Django CRUD baselines
STANDARD_USER_CRUD = ["add_user", "change_user", "delete_user", "view_user"]
READ_UPDATE_USER = ["view_user", "change_user"]

# Custom granular enterprise permission fragments
STAFF_MGMT_PERMS = [
    "can_register_staff",
    "can_deactivate_user",
    "can_toggle_is_staff",
]

PASSWORD_PERMS = [
    "can_reset_password_other_user",
    "can_change_self_password",
]

PLANT_ENGINEERING_PERMS = [
    "can_assign_plant",
    "can_change_plant",
]

SHED_MGMT_PERMS = [
    "can_assign_shed",
    "can_change_shed",
]

EMPLOYEE_CORE_PERMS = [
    "view_employee",
    "change_employee",
    "can_change_employee_department",
]

# =====================================================================
# 2. COMPOSITE ROLE BUNDLES (Combining fragments into roles)
# =====================================================================
# This allows you to update what a role means globally in one single place

ADMIN_USER_BUNDLE = STANDARD_USER_CRUD + STAFF_MGMT_PERMS + PASSWORD_PERMS
STANDARD_STAFF_USER_BUNDLE = READ_UPDATE_USER + ["can_change_self_password"]

ENGINEER_EMPLOYEE_BUNDLE = EMPLOYEE_CORE_PERMS + PLANT_ENGINEERING_PERMS
FARM_MGR_EMPLOYEE_BUNDLE = (
    EMPLOYEE_CORE_PERMS + SHED_MGMT_PERMS + PLANT_ENGINEERING_PERMS
)


# =====================================================================
# 3. THE ENTERPRISE MATRIX (The exact structure your code reads)
# =====================================================================
# We use Python unpacking to map out models while keeping it perfectly DRY.

PERM_CONFIG = {
    "User": {
        # High level administrative accounts
        "Chief Executive Officer": ADMIN_USER_BUNDLE,
        "System Administrator": ADMIN_USER_BUNDLE,
        # Operational Staff roles with identical base needs
        "Human Resource Officer": STANDARD_STAFF_USER_BUNDLE,
        "Human Resource Manager": STANDARD_STAFF_USER_BUNDLE,
        "Farm Manager": STANDARD_STAFF_USER_BUNDLE,
        "Transport Officer": STANDARD_STAFF_USER_BUNDLE,
        "Lead Transport Officer": STANDARD_STAFF_USER_BUNDLE,
    },
    "Employee": {
        "Senior Maintainance Engineer": ENGINEER_EMPLOYEE_BUNDLE,
        "Senior Chef": ENGINEER_EMPLOYEE_BUNDLE,
        "Lead Housing and Apartment Manager": EMPLOYEE_CORE_PERMS,
        "Lead Nutritionist": EMPLOYEE_CORE_PERMS,
        "Lead Veterinary Officer": EMPLOYEE_CORE_PERMS,
        "General Farm Manager": FARM_MGR_EMPLOYEE_BUNDLE,
        "Farm Manager": FARM_MGR_EMPLOYEE_BUNDLE,
    },
    # You can quickly map out other entities inheriting shared bundles
    "UserAddress": {
        "Chief Executive Officer": ADMIN_USER_BUNDLE,
        "System Administrator": ADMIN_USER_BUNDLE,
        "Human Resource Officer": STANDARD_STAFF_USER_BUNDLE,
    },
}
