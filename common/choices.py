"""
CHOICES AND CONSTANTS REGISTRY

This file serves as the central source of truth for all standardized choices,
lookups, and configuration constants used across the Enterprise System

Responsibility:
- Maintain consistency in database values.
- Provide human-readable, translatable labels for the UI.
- Define application-wide configuration (OTP, Token Types).
"""

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


""" SYSTEM CONFIGURATION & AUTHENTICATION """

now = timezone.now
now_iso = timezone.now().isoformat()
current_time = timezone.now()

OTP_CODE_LENGTH = getattr(settings, "OTP_CODE_LENGTH", 6)
OTP_EXPIRATION_TIME_MINUTES = getattr(settings, "OTP_EXPIRATION_TIME_MINUTES", 5)

TOKEN_TYPE_REGISTRATION = "registration"
TOKEN_TYPE_LOGIN = "login"
TOKEN_TYPE_PASSWORD_RESET = "password_reset"
TOKEN_TYPE_TRANSACTION_AUTH = "transaction_auth"
TOKEN_TYPE_EMAIL_CHANGE = "email_change"
TOKEN_TYPE_PHONE_VERIFICATION = "phone_verification"
TOKEN_TYPE_2FA_ENABLE = "2fa_enable"
TOKEN_TYPE_ACCOUNT_DELETION = "account_deletion"
TOKEN_TYPE_STAFF_INVITATION = "staff_invitation"

TOKEN_TYPE_CHOICES = [
    (TOKEN_TYPE_REGISTRATION, _("Registration")),
    (TOKEN_TYPE_LOGIN, _("Login")),
    (TOKEN_TYPE_PASSWORD_RESET, _("Password Reset")),
    (TOKEN_TYPE_TRANSACTION_AUTH, _("Transaction Authorization")),
    (TOKEN_TYPE_EMAIL_CHANGE, _("Email Change Verification")),
    (TOKEN_TYPE_PHONE_VERIFICATION, _("Phone Number Verification")),
    (TOKEN_TYPE_2FA_ENABLE, _("Two-Factor Auth Enablement")),
    (TOKEN_TYPE_ACCOUNT_DELETION, _("Account Deletion Confirmation")),
    (TOKEN_TYPE_STAFF_INVITATION, _("Staff Onboarding Invitation")),
]

COMMUNICATION_CHOICES = [
    ("email", _("Email")),
    ("phone", _("Phone/SMS")),
    ("both", _("Both")),
]

LANGUAGE_CHOICES = [
    ("en-us", _("English (US)")),
    ("en-gb", _("English (British)")),
    ("sw", _("Kiswahili")),
]


""" USER PROFILE & HR """

REGISTRATION_STATUS = [
    ("PENDING", _("Pending Verification")),
    ("VERIFIED", _("Verified & Approved")),
    ("REJECTED", _("Rejected/Incomplete")),
    ("REVOKED", _("Revoked/Terminated")),
]

TITLE_CHOICES = [
    # Standard Social Titles
    ("mr", _("Mr.")),
    ("mrs", _("Mrs.")),
    ("ms", _("Ms.")),
    ("miss", _("Miss")),

    # Professional & Academic Titles
    ("dr", _("Dr.")),
    ("prof", _("Prof.")),
    ("eng", _("Eng.")),
    ("arch", _("Arch.")),
    ("adv", _("Adv.")),
    ("cpa", _("CPA")),

    # Specialized/Medical (Useful for Vet Officers)
    ("vet", _("Vet.")),
    ("pharm", _("Pharm.")),

    # Religious/Honorable (Optional based on your region)
    ("rev", _("Rev.")),
    ("hon", _("Hon.")),
]

GENDER_CHOICES = [
    ("male", _("Male")),
    ("female", _("Female")),
    ("other", _("Other")),
    ("prefer_not_to_say", _("Prefer Not to Say")),
]

MARITAL_STATUSES = [
    ("single", _("Single")),
    ("married", _("Married")),
    ("divorced", _("Divorced")),
]

ID_TYPES = [
    ("NIDA", _("NIDA (National ID)")),
    ("PASSPORT", _("Passport")),
    ("VOTER_ID", _("Voter ID")),
    ("DRIVING_LICENSE", _("Driving License")),
]

EMPLOYEE_ROLE_CHOICES = [
    ("FARM_MANAGER", _("Farm Manager")),
    ("VET_OFFICER", _("Veterinary Officer")),
    ("PLANT_SUPERVISOR", _("Processing Plant Supervisor")),
    ("ACCOUNTANT", _("Accountant")),
    ("ATTENDANT", _("General Attendant")),
]

EMPLOYMENT_TYPES = [
    ("FULL_TIME", _("Full-Time Regular")),
    ("CONTRACT", _("Contractor")),
    ("CASUAL", _("Casual Laborer")),
]


""" LOGISTICS, SHIPPING & INVENTORY """

ORDER_STATUS = [
    ("PENDING", _("Pending")),
    ("CONFIRMED", _("Confirmed")),
    ("DISPATCHED", _("Dispatched")),
    ("DELIVERED", _("Delivered")),
    ("CANCELLED", _("Cancelled")),
]

SHIPPING_CHOICES = [
    ("REQUESTED", _("Request Received")),
    ("PACKING", _("In Packaging")),
    ("COLLECTED", _("Collected by Carrier")),
    ("DEPARTED", _("Departed Facility")),
    ("IN_TRANSIT", _("In Transit")),
    ("OUT_FOR_DELIVERY", _("Out for Delivery")),
    ("DELIVERED", _("Delivered")),
    ("FAILED", _("Delivery Failed")),
]

CARRIER_TYPES = [
    ("INTERNAL", _("Farm Fleet")),
    ("THIRD_PARTY", _("External Courier")),
    ("PICKUP", _("Customer Pickup")),
]

STOCK_MOVEMENT_TYPES = [
    ("SALE", _("Sale")),
    ("RETURN", _("Return")),
    ("RESTOCK", _("Restock")),
    ("ADJUST", _("Adjustment")),
    ("TRANSFER", _("Internal Transfer")),
]

STORAGE_UNIT_TYPES = [
    ("SHELF", _("Shelf (Rafu)")),
    ("KABATI", _("Cabinet (Kabati)")),
    ("CLIPBOARD", _("Clipboard")),
    ("DRAWER", _("Drawer (Droo)")),
    ("COLD_ROOM", _("Cold Room Rack")),
]

ITEM_DISPOSITION_CHOICES = [
    ("SOLD", _("Successfully Sold")),
    ("RETURNED", _("Returned by Customer")),
    ("CHANGED", _("Exchanged for Different Product")),
    ("DAMAGED", _("Damaged/Defective (Pre-delivery)")),
    ("REFUND_ISSUED", _("Item Refunded")),
]

ADDRESS_TYPES = [
    ("shipping", _("Shipping")),
    ("billing", _("Billing")),
    ("home", _("Home")),
    ("work", _("Work")),
]


""" FARM PRODUCTION & HEALTH """

PRODUCT_CATEGORY_CHOICES = [
    ("EGG", _("Eggs")),
    ("MEAT", _("Meat/Poultry")),
    ("BY_PRODUCT", _("By-Products (Manure/Feathers)")),
    ("EQUIPMENT", _("Farm Equipment/Assets")),
]

BIRD_TYPE_CHOICES = [
    ("BROILER", _("Broiler")),
    ("LAYER", _("Layer")),
    ("KUCHI", _("Kuchi")),
    ("LOCAL", _("Local")),
]

BATCH_STATUS_CHOICES = [
    ("ACTIVE", _("Active")),
    ("DEPLETED", _("Depleted")),
    ("QUARANTINED", _("Quarantined")),
    ("PROCESSING", _("In Processing Plant")),
]

CYCLE_STATUS = [
    ("SETTING", _("Setting")),
    ("CANDLING", _("Candling")),
    ("HATCHED", _("Hatched")),
    ("FAILED", _("Failed")),
]

READINESS_CHOICES = [
    ("READY", _("Ready for Sale")),
    ("NOT_READY", _("Not Ready / WIP")),
    ("QUARANTINE", _("Under Inspection")),
    ("EXPIRED", _("Expired / Waste")),
]

HEALTH_RECORD_TYPE = [
    ("VACCINATION", _("Vaccination")),
    ("MEDICATION", _("Medication/Treatment")),
    ("PROCEDURE", _("General Procedure (e.g., De-beaking)")),
    ("LAB_RESULT", _("Laboratory Test Result")),
]

OUTBREAK_STATUS = [
    ("ACTIVE", _("Active Outbreak")),
    ("CONTAINED", _("Contained/Under Treatment")),
    ("RESOLVED", _("Resolved/Closed")),
]

DISPOSAL_METHOD_CHOICES = [
    ("INCINERATION", _("Incineration")),
    ("COMPOSTING", _("Composting")),
    ("SALE", _("Sale to Third Party")),
    ("LANDFILL", _("Landfill")),
    ("RECYCLE", _("Recycling")),
]


""" SALES, FINANCE & BOOKING """

CURRENCY_CHOICES = [
    ("TZS", _("Tanzanian Shilling")),
    ("GBP", _("British Pound")),
    ("USD", _("US Dollar")),
    ("KES", _("Kenyan Shilling")),
]

PAYMENT_METHOD_CHOICES = [
    ("CASH", _("Cash")),
    ("CREDIT_CARD", _("Credit Card")),
    ("BANK_TRANSFER", _("Bank Transfer")),
    ("MOBILE_MONEY", _("Mobile Money (M-Pesa/Tigo Pesa)")),
    ("ONLINE_WALLET", _("Online Wallet")),
]

SALE_STATUS_CHOICES = [
    ("PENDING", _("Pending")),
    ("PARTIAL", _("Partial")),
    ("PAID", _("Paid")),
    ("FAILED", _("Failed")),
    ("REFUNDED", _("Refunded")),
]

CUSTOMER_TYPE = [
    ("RETAIL", _("Retail")),
    ("WHOLESALE", _("Wholesale")),
    ("DISTRIBUTOR", _("Distributor")),
]

BOOKING_STATUS = [
    ("PENDING", _("Pending/Inquiry")),
    ("CONFIRMED", _("Confirmed/Deposit Paid")),
    ("CANCELLED", _("Cancelled")),
    ("COMPLETED", _("Event Finished")),
]



""" ASSETS & FACILITIES """

ASSET_TYPE_CHOICES = [
    ("FARM", _("Farm/Production Site")),
    ("BUILDING", _("Building/Structure")),
    ("ZONE", _("Recreation/Common Zone")),
    ("UNIT", _("Specific Rental/Housing Unit")),
]

UNIT_TYPES = [
    ("SINGLE", _("Single Room")),
    ("BEDSITTER", _("Bedsitter")),
    ("APARTMENT", _("Full Apartment")),
    ("SHOP", _("Commercial Shop Space")),
]



""" UNITS OF MEASURE & GENERAL TASK STATUS """

UOM_CHOICES = [
    ("TRAY", _("Tray")),
    ("KG", _("Kilogram")),
    ("PCS", _("Pieces")),
    ("BAG", _("Bag")),
]

UNIT_CHOICES = [
    ("pc", _("Piece")),
    ("box", _("Box")),
    ("kg", _("Kilogram")),
]

RATE_TYPES = [
    ("FLAT", _("Flat Rate")),
    ("PER_KG", _("Cost Per KG"))
]

STATUS_CHOICES = [
    ("OPEN", _("Open")),
    ("IN_PROGRESS", _("In Progress")),
    ("CLOSED", _("Resolved")),
]

PRIORITY_CHOICES = [
    ("LOW", _("Low")),
    ("NORMAL", _("Normal")),
    ("URGENT", _("Urgent/Safety")),
]



""" MISCELLANEOUS / LEGACY """

TYPE_CHOICES = [(0, "User"), (1, "Group"), (2, "Broadcast"), (3, "Agent")]
