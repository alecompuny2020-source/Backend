from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

now = timezone.now
now_iso = timezone.now().isoformat()

OTP_CODE_LENGTH = getattr(settings, "OTP_CODE_LENGTH", 6)
OTP_EXPIRATION_TIME_MINUTES = getattr(settings, "OTP_EXPIRATION_TIME_MINUTES", 5)

TOKEN_TYPE_REGISTRATION = "registration"
TOKEN_TYPE_LOGIN = "login"
TOKEN_TYPE_PASSWORD_RESET = "password_reset"
TOKEN_TYPE_TRANSACTION_AUTH = "transaction_auth"

REGISTRATION_STATUS = [
    ("PENDING", _("Pending Verification")),
    ("VERIFIED", _("Verified & Approved")),
    ("REJECTED", _("Rejected/Incomplete")),
    ("REVOKED", _("Revoked/Terminated")),
]

ADDRESS_TYPES = [
    ("shipping", _("Shipping")),
    ("billing", _("Billing")),
    ("home", _("Home")),
    ("work", _("Work")),
]

MARITAL_STATUSES = [
    ("single", _("Single")),
    ("maried", _("Maried")),
    ("devoced", _("Devoced")),
]

TITLE_CHOICES = [
    ("mr", _("Mr")),
    ("ms", _("Ms")),
    ("mrs", _("Mrs")),
    ("dr", _("Doctor")),
    ("prof", _("Professor")),
    ("eng", _("Engineer")),
]

GENDER_CHOICES = [
    ("male", _("Male")),
    ("female", _("Female")),
    ("other", _("Other")),
    ("prefer_not_to_say", _("Prefer Not to Say")),
]

BOOKING_STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("ON_ROUTE", "On Route"),
    ("COMPLETED", "Completed"),
    ("CANCELLED", "Cancelled"),
]

EMPLOYMENT_TYPES = [
    ("FULL_TIME", _("Full-Time Regular")),
    ("CONTRACT", _("Contractor")),
    ("CASUAL", _("Casual Laborer")),
]

PAYMENT_METHOD_CHOICES = [
    ("Cash", "Cash"),
    ("Card", "Credit/Debit Card"),
    ("MOMO", "Mobile Money"),
    ("Transfer", "Bank Transfer"),
    ("Other", "Other"),
    ("Uknown", "Uknown"),
]

COMMUNICATION_CHOICES = [
    ("email", _("Email")),
    ("phone", _("Phone/SMS")),
    ("both", _("Both")),
]

ITEM_DISPOSITION_CHOICES = [
    ("SOLD", "Successfully Sold"),
    ("RETURNED", "Returned by Customer"),
    ("CHANGED", "Exchanged for Different Product"),
    ("DAMAGED", "Damaged/Defective (Pre-delivery)"),
    ("REFUND_ISSUED", "Item Refunded"),
]

UNIT_CHOICES = [
    ("pc", "Piece"),
    ("box", "Box"),
    ("kg", "Kilogram"),
]

SALE_STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("PARTIAL", "Partial"),
    ("PAID", "Paid"),
    ("FAILED", "Failed"),
    ("REFUNDED", "Refunded"),
]


STORAGE_UNIT_TYPES = [
    ("SHELF", _("Shelf (Rafu)")),
    ("KABATI", _("Cabinet (Kabati)")),
    ("CLIPBOARD", _("Clipboard")),
    ("DRAWER", _("Drawer (Droo)")),
    ("COLD_ROOM", _("Cold Room Rack")),
]

READINESS_CHOICES = [
    ("READY", _("Ready for Sale")),
    ("NOT_READY", _("Not Ready / WIP")),
    ("QUARANTINE", _("Under Inspection")),
    ("EXPIRED", _("Expired / Waste")),
]

CUSTOMER_TYPE = [
    ("RETAIL", _("Retail")),
    ("WHOLESALE", _("Wholesale")),
    ("DISTRIBUTOR", _("Distributor")),
]

CARRIER_TYPES = [
    ("INTERNAL", _("Farm Fleet")),
    ("THIRD_PARTY", _("External Courier")),
    ("PICKUP", _("Customer Pickup")),
]

ORDER_STATUS = [
    ("PENDING", _("Pending")),
    ("CONFIRMED", _("Confirmed")),
    ("DISPATCHED", _("Dispatched")),
    ("DELIVERED", _("Delivered")),
    ("CANCELLED", _("Cancelled")),
]

STOCK_MOVEMENT_TYPES = [
    ("SALE", _("Sale")),
    ("RETURN", _("Return")),
    ("RESTOCK", _("Restock")),
    ("ADJUST", _("Adjustment")),
    ("TRANSFER", _("Internal Transfer")),
]


LANGUAGE_CHOICES = [
    ("en-us", _("English (US)")),
    ("en-gb", _("English (British)")),
    ("sw", _("Kiswahili")),
]

TOKEN_TYPE_CHOICES = [
    (TOKEN_TYPE_REGISTRATION, _("Registration")),
    (TOKEN_TYPE_LOGIN, _("Login")),
    (TOKEN_TYPE_PASSWORD_RESET, _("Password Reset")),
    (TOKEN_TYPE_TRANSACTION_AUTH, _("Transaction Authorization")),
]

TYPE_CHOICES = [(0, "User"), (1, "Group"), (2, "Broadcast"), (3, "Agent")]

UOM_CHOICES = [
    ("TRAY", _("Tray")),
    ("KG", _("Kilogram")),
    ("PCS", _("Pieces")),
    ("BAG", _("Bag")),
]

PRODUCT_CATEGORY_CHOICES = [
    ("EGG", _("Eggs")),
    ("MEAT", _("Meat/Poultry")),
    ("BY_PRODUCT", _("By-Products (Manure/Feathers)")),
    ("EQUIPMENT", _("Farm Equipment/Assets")),
]

ID_TYPES = [
    ("NIDA", _("NIDA (National ID)")),
    ("PASSPORT", _("Passport")),
    ("VOTER_ID", _("Voter ID")),
    ("DRIVING_LICENSE", _("Driving License")),
]

BOOKING_STATUS = [
    ("PENDING", _("Pending/Inquiry")),
    ("CONFIRMED", _("Confirmed/Deposit Paid")),
    ("CANCELLED", _("Cancelled")),
    ("COMPLETED", _("Event Finished")),
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

CYCLE_STATUS = [
    ("SETTING", _("Setting")),
    ("CANDLING", _("Candling")),
    ("HATCHED", _("Hatched")),
    ("FAILED", _("Failed")),
]

CURRENCY_CHOICES = [
    ("TZS", _("Tanzanian Shilling")),
    ("GBP", _("British Pound")),
    ("USD", _("US Dollar")),
    ("KES", _("Kenyan Shilling")),
]

# CURRENCY_CHOICES = [('USD', 'USD $'), ('TZS', 'TZS TSh'), ('EUR', 'EUR €'), ('KES', 'KES KSh')]

PAYMENT_METHOD_CHOICES = [
    ("CASH", _("Cash")),
    ("CREDIT_CARD", _("Credit Card")),
    ("BANK_TRANSFER", _("Bank Transfer")),
    ("MOBILE_MONEY", _("Mobile Money (M-Pesa/Tigo Pesa)")),
    ("ONLINE_WALLET", _("Online Wallet")),
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

RATE_TYPES = [("FLAT", _("Flat Rate")), ("PER_KG", _("Cost Per KG"))]

UNIT_TYPES = [
    ("SINGLE", _("Single Room")),
    ("BEDSITTER", _("Bedsitter")),
    ("APARTMENT", _("Full Apartment")),
    ("SHOP", _("Commercial Shop Space")),
]

ASSET_TYPE_CHOICES = [
    ("FARM", _("Farm/Production Site")),
    ("BUILDING", _("Building/Structure")),
    ("ZONE", _("Recreation/Common Zone")),
    ("UNIT", _("Specific Rental/Housing Unit")),
]


BIRD_TYPE_CHOICES = [
    ("BROILER", _("Broiler")),
    ("LAYER", _("Layer")),
    ("KUCHI", _("Kuchi")),
    ("LOCAL", _("Local")),
]

HEALTH_RECORD_TYPE = [
    ("VACCINATION", _("Vaccination")),
    ("MEDICATION", _("Medication/Treatment")),
    ("PROCEDURE", _("General Procedure (e.g., De-beaking)")),
    ("LAB_RESULT", _("Laboratory Test Result")),
]

DISPOSAL_METHOD_CHOICES = [
    ("INCINERATION", _("Incineration")),
    ("COMPOSTING", _("Composting")),
    ("SALE", _("Sale to Third Party")),
    ("LANDFILL", _("Landfill")),
    ("RECYCLE", _("Recycling")),
]

OUTBREAK_STATUS = [
    ("ACTIVE", _("Active Outbreak")),
    ("CONTAINED", _("Contained/Under Treatment")),
    ("RESOLVED", _("Resolved/Closed")),
]

BATCH_STATUS_CHOICES = [
    ("ACTIVE", _("Active")),
    ("DEPLETED", _("Depleted")),
    ("QUARANTINED", _("Quarantined")),
    ("PROCESSING", _("In Processing Plant")),
]

EMPLOYEE_ROLE_CHOICES = [
    ("FARM_MANAGER", _("Farm Manager")),
    ("VET_OFFICER", _("Veterinary Officer")),
    ("PLANT_SUPERVISOR", _("Processing Plant Supervisor")),
    ("ACCOUNTANT", _("Accountant")),
    ("ATTENDANT", _("General Attendant")),
]
