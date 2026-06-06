"""
CHOICES AND CONSTANTS REGISTRY FOR AN ENTERPRISE

This file serves as the central source of truth for all standardized choices,
lookups, and configuration constants used across the Enterprise System

Responsibility:
- Maintain consistency in database values.
- Provide human-readable, translatable labels for the UI.
- Define application-wide configuration (OTP, Token Types).
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

""" SYSTEM CONFIGURATION & AUTHENTICATION """

now = timezone.now
now_iso = timezone.now().isoformat()
current_time = timezone.now()

OTP_CODE_LENGTH = getattr(settings, "OTP_CODE_LENGTH", 6)
OTP_EXPIRATION_TIME_MINUTES = getattr(settings, "OTP_EXPIRATION_TIME_MINUTES", 5)


class TokenType(models.TextChoices):
    REGISTRATION = "REGISTRATION", _("Registration")
    LOGIN = "LOGIN", _("Login")
    PASSWORD_RESET = "PASSWORD_RESET", _("Password Reset")
    TRANSACTION_AUTH = "TRANSACTION_AUTH", _("Transaction Authorization")
    EMAIL_CHANGE = "EMAIL_CHANGE", _("Email Change Verification")
    PHONE_VERIFICATION = "PHONE_VERIFICATION", _("Phone Number Verification")
    TwoFA_ENABLE = "2FA_ENABLE", _("Two-Factor Auth Enablement")
    ACCOUNT_DELETION = "ACCOUNT_DELETION", _("Account Deletion Confirmation")
    STAFF_INVITATION = "STAFF_INVITATION", _("Staff Onboarding Invitation")


class CommunicationMethod(models.TextChoices):
    EMAIL = "email", _("Email")
    PHONE = "phone", _("Phone")
    BOTH = "both", _("Both")


class LanguageChoice(models.TextChoices):
    EN_US = "en-us", _("English (US)")
    EN_GB = "en-gb", _("English (British)")
    SW = "sw", _("Kiswahili")


""" USER PROFILE & HR """


class RegistrationStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending Verification")
    VERIFIED = "VERIFIED", _("Verified & Approved")
    REJECTED = "REJECTED", _("Rejected/Incomplete")
    REVOKED = "REVOKED", _("Revoked/Terminated")


class UserTitle(models.TextChoices):
    # Standard Social Titles
    MR = "MR", _("Mr.")
    MRS = "MRS", _("Mrs.")
    MS = "MS", _("Ms.")
    MISS = "MISS", _("Miss")

    # Professional & Academic Titles
    DR = "DR", _("Dr.")
    PROF = "PROF", _("Prof.")
    ENG = "ENG", _("Eng.")
    ARCH = "ARCH", _("Arch.")
    ADV = "ADV", _("Adv.")
    CPA = "CPA", _("CPA")

    # Specialized/Medical (Perfect for your Vet Officers)
    VET = "VET", _("Vet.")
    PHARM = "PHARM", _("Pharm.")

    # Religious/Honorable
    REV = "REV", _("Rev.")
    HON = "HON", _("Hon.")


class Gender(models.TextChoices):
    MALE = "MALE", _("Male")
    FEMALE = "FEMALE", _("Female")
    OTHER = "OTHER", _("Other")
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", _("Prefer Not to Say")


class MaritalStatus(models.TextChoices):
    SINGLE = "SINGLE", _("Single")
    MARRIED = "MARRIED", _("Married")
    DIVORCED = "DIVORCED", _("Divorced")


class IdentityType(models.TextChoices):
    NIDA = "NIDA", _("NIDA (National ID)")
    PASSPORT = "PASSPORT", _("Passport")
    VOTER_ID = "VOTER_ID", _("Voter ID")
    DRIVING_LICENSE = "DRIVING_LICENSE", _("Driving License")


class EmploymentType(models.TextChoices):
    FULL_TIME = "FULL_TIME", _("Full-Time Regular")
    CONTRACT = "CONTRACT", _("Contractor")
    CASUAL = "CASUAL", _("Casual Laborer")


class AddressType(models.TextChoices):
    SHIPPING = "SHIPPING", _("Shipping")
    BILLING = "BILLING", _("Billing")
    HOME = "HOME", _("Home")
    WORK = "WORK", _("Work")


""" LOGISTICS, SHIPPING & INVENTORY """


class OrderStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    CONFIRMED = "CONFIRMED", _("Confirmed")
    DISPATCHED = "DISPATCHED", _("Dispatched")
    DELIVERED = "DELIVERED", _("Delivered")
    CANCELLED = "CANCELLED", _("Cancelled")


class ShippingStatus(models.TextChoices):
    REQUESTED = "REQUESTED", _("Request Received")
    PACKING = "PACKING", _("In Packaging")
    COLLECTED = "COLLECTED", _("Collected by Carrier")
    DEPARTED = "DEPARTED", _("Departed Facility")
    IN_TRANSIT = "IN_TRANSIT", _("In Transit")
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY", _("Out for Delivery")
    DELIVERED = "DELIVERED", _("Delivered")
    FAILED = "FAILED", _("Delivery Failed")


class CarrierType(models.TextChoices):
    INTERNAL = "INTERNAL", _("Farm Fleet")
    THIRD_PARTY = "THIRD_PARTY", _("External Courier")
    PICKUP = "PICKUP", _("Customer Pickup")


class StockMovementType(models.TextChoices):
    SALE = "SALE", _("Sale")
    RETURN = "RETURN", _("Return")
    RESTOCK = "RESTOCK", _("Restock")
    ADJUST = "ADJUST", _("Adjustment")
    TRANSFER = "TRANSFER", _("Internal Transfer")


class StorageUnitType(models.TextChoices):
    SHELF = "SHELF", _("Shelf (Rafu)")
    KABATI = "KABATI", _("Cabinet (Kabati)")
    CLIPBOARD = "CLIPBOARD", _("Clipboard")
    DRAWER = "DRAWER", _("Drawer (Droo)")
    COLD_ROOM = "COLD_ROOM", _("Cold Room Rack")


class ItemDisposition(models.TextChoices):
    SOLD = "SOLD", _("Successfully Sold")
    RETURNED = "RETURNED", _("Returned by Customer")
    CHANGED = "CHANGED", _("Exchanged for Different Product")
    DAMAGED = "DAMAGED", _("Damaged/Defective (Pre-delivery)")
    REFUND_ISSUED = "REFUND_ISSUED", _("Item Refunded")


class PackageStatus(models.TextChoices):
    IN_STOCK = "IN_STOCK", _("Ipo Ghalani")
    SOLD = "SOLD", _("Imeuzwa")
    SPOILED = "SPOILED", _("Imeharibika/Imeoza")
    TRANSFERRED = "TRANSFERRED", _("Imehamishwa Banda/Ghala")


""" FARM PRODUCTION & HEALTH """


class SourceChoices(models.TextChoices):
    FARM_PRODUCED = "FARM_PRODUCED", _("Kiasili / Limeshindwa Shambani")
    COMMERCIAL = "COMMERCIAL", _("Kibiashara / Kununuliwa")


class ProductCategory(models.TextChoices):
    EGG = "EGG", _("Eggs")
    MEAT = "MEAT", _("Meat/Poultry")
    BY_PRODUCT = "BY_PRODUCT", _("By-Products (Manure/Feathers)")
    EQUIPMENT = "EQUIPMENT", _("Farm Equipment/Assets")


class BirdType(models.TextChoices):
    BROILER = "BROILER", _("Broiler")
    LAYER = "LAYER", _("Layer")
    KUCHI = "KUCHI", _("Kuchi")
    LOCAL = "LOCAL", _("Local")
    KUROILER = "KUROILER", _("Kuroiler")


class SpeciesType(models.TextChoices):
    CHICKEN = 'CHICKEN', 'Kuku'
    DUCK = 'DUCK', 'Bata'
    RABBIT = 'RABBIT', 'Sungura'
    FISH = 'FISH', 'Samaki'

class BreedType(models.TextChoices):
    # ------ MBEGU ZA KUKU (CHICKEN) ------
    KUCHI = 'KUCHI', 'Kuchi'
    SINGAMAGAZI = 'SINGAMAGAZI', 'Singamagazi'
    CHINGWEKWE = 'CHINGWEKWE', 'Chingwekwe'
    KISHINGO = 'KISHINGO', 'Kishingo'
    MBEYA = 'MBEYA', 'Mbeya'
    KIBUTU = 'KIBUTU', 'Kibutu'

    # ------ MBEGU ZA BATA (DUCK) ------
    MZINGA = 'MZINGA', 'Bata Mzinga'
    BUKINI = 'BUKINI', 'Bata Bukini'
    MAJI = 'MAJI', 'Bata Maji (Muscovy/Mallard)'

    # ------ MBEGU ZA SUNGURA (RABBIT) ------
    NZ_WHITE = 'NZ_WHITE', 'New Zealand White'
    CALIFORNIA = 'CALIFORNIA', 'California White'
    CHINCHILLA = 'CHINCHILLA', 'Chinchilla'
    FLEMISH = 'FLEMISH', 'Flemish Giant'
    S_LOCAL = 'S_LOCAL', 'Sungura wa Kienyeji (Local)'

    # ------ MBEGU ZA SAMAKI (FISH) ------
    PEREGE = 'PEREGE', 'Perege (Tilapia)'
    KAMBALE = 'KAMBALE', 'Kambale (Catfish)'


class FlockBatchStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    DEPLETED = "DEPLETED", _("Depleted")
    QUARANTINED = "QUARANTINED", _("Quarantined")
    PROCESSING = "PROCESSING", _("In Processing Plant")


class IncubatorMachineType(models.TextChoices):
    SETTER = "SETTER", _("Setter")
    HATCHER = "HATCHER", _("Hatcher")
    COMBINED = "COMBINED", _("Combined (Setter & Hatcher)")


class FarmBlockStatus(models.TextChoices):
    RESTING = "RESTING", _("Inapumzika")
    GRAZING = "GRAZING", _("Kuku wapo hapa")
    CROPPING = "CROPPING", _("Kuna Mazao")


class IncubationCycleStatus(models.TextChoices):
    SETTING = "SETTING", _("Setting")
    CANDLING = "CANDLING", _("Candling")
    HATCHED = "HATCHED", _("Hatched")
    FAILED = "FAILED", _("Failed")


class StockReadinessStatus(models.TextChoices):
    READY = "READY", _("Ready for Sale")
    NOT_READY = "NOT_READY", _("Not Ready / WIP")
    QUARANTINE = "QUARANTINE", _("Under Inspection")
    EXPIRED = "EXPIRED", _("Expired / Waste")


class HealthRecordType(models.TextChoices):
    VACCINATION = "VACCINATION", _("Vaccination")
    MEDICATION = "MEDICATION", _("Medication/Treatment")
    PROCEDURE = "PROCEDURE", _("General Procedure (e.g., De-beaking)")
    LAB_RESULT = "LAB_RESULT", _("Laboratory Test Result")


class DiseaseOutbreakStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active Outbreak")
    CONTAINED = "CONTAINED", _("Contained/Under Treatment")
    RESOLVED = "RESOLVED", _("Resolved/Closed")


class WasteDisposalMethod(models.TextChoices):
    INCINERATION = "INCINERATION", _("Incineration")
    COMPOSTING = "COMPOSTING", _("Composting")
    SALE = "SALE", _("Sale to Third Party")
    LANDFILL = "LANDFILL", _("Landfill")
    RECYCLE = "RECYCLE", _("Recycling")


class StorageUnitType(models.TextChoices):
    SHELF = "SHELF", _("Shelf (Rafu)")
    KABATI = "KABATI", _("Cabinet (Kabati)")
    CLIPBOARD = "CLIPBOARD", _("Clipboard")
    DRAWER = "DRAWER", _("Drawer (Droo)")
    COLD_ROOM = "COLD_ROOM", _("Cold Room Rack")


class ProductionStatus(models.TextChoices):
    PLANTED = "PLANTED", _("planted")
    GROWING = "GROWING", _("growing")
    HARVESTED = "HARVESTED", _("harvested")
    FAILED = "FAILED", _("failed")


class MeatCutType(models.TextChoices):
    SLICE = "SLICE", _("Slice / Steak (Lidandi / Shaba)")
    PART = "PART", _("Primal Part / Cut (Sehemu ya Mnyama - mf. Paja, Mbavu)")
    PIECE = "PIECE", _("Countable Piece (Idadi - mf. Soseji, Mishikaki)")
    WHOLE = "WHOLE", _("Whole Carcass / Bird (Mzoga Mzima / Kuku Mzima)")


class StorageState(models.TextChoices):
    FRESH = "FRESH", _("Fresh / Chilled")
    FROZEN = "FROZEN", _("Frozen")


class FatLevel(models.TextChoices):
    LEAN = "LEAN", _("Lean / Low Fat")
    MEDIUM = "MEDIUM", _("Medium Fat")
    HIGH = "HIGH", _("High Fat / Premium Marbled")


""" SALES, FINANCE & BOOKING """


class CurrencyCode(models.TextChoices):
    TZS = "TZS", _("Tanzanian Shilling")
    GBP = "GBP", _("British Pound")
    USD = "USD", _("US Dollar")
    KES = "KES", _("Kenyan Shilling")


class PaymentMethod(models.TextChoices):
    CASH = "CASH", _("Cash")
    CREDIT_CARD = "CREDIT_CARD", _("Credit Card")
    BANK_TRANSFER = "BANK_TRANSFER", _("Bank Transfer")
    MOBILE_MONEY = "MOBILE_MONEY", _("Mobile Money (M-Pesa/Tigo Pesa/Airtel Money)")
    ONLINE_WALLET = "ONLINE_WALLET", _("Online Wallet")


class SaleInvoiceStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    PARTIAL = "PARTIAL", _("Partial")
    PAID = "PAID", _("Paid")
    FAILED = "FAILED", _("Failed")
    REFUNDED = "REFUNDED", _("Refunded")


class CustomerType(models.TextChoices):
    RETAIL = "RETAIL", _("Retail")
    WHOLESALE = "WHOLESALE", _("Wholesale")
    DISTRIBUTOR = "DISTRIBUTOR", _("Distributor")


class EventBookingStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending/Inquiry")
    CONFIRMED = "CONFIRMED", _("Confirmed/Deposit Paid")
    CANCELLED = "CANCELLED", _("Cancelled")
    COMPLETED = "COMPLETED", _("Event Finished")


""" ASSETS & FACILITIES """


class AssetType(models.TextChoices):
    FARM = "FARM", _("Farm/Production Site")
    BUILDING = "BUILDING", _("Building/Structure")
    ZONE = "ZONE", _("Recreation/Common Zone")
    UNIT = "UNIT", _("Specific Rental/Housing Unit")


class RentalUnitType(models.TextChoices):
    SINGLE = "SINGLE", _("Single Room")
    BEDSITTER = "BEDSITTER", _("Bedsitter")
    APARTMENT = "APARTMENT", _("Full Apartment")
    SHOP = "SHOP", _("Commercial Shop Space")


""" UNITS OF MEASURE & GENERAL TASK STATUS """


class UnitOfMeasure(models.TextChoices):
    # Hapa tumeziunganisha zote kuwa kitu kimoja safi na chenye maana
    TRAY = "TRAY", _("Tray (Treya)")
    KG = "KG", _("Kilogram (Kilogramu)")
    LITER = "LITER", _("Liter (Lita)")
    PCS = "PCS", _("Pieces (Idadi/Vipande)")
    BAG = "BAG", _("Bag (Mfuko)")
    BOX = "BOX", _("Box (Boxi)")


class RateType(models.TextChoices):
    FLAT = "FLAT", _("Flat Rate")
    PER_KG = "PER_KG", _("Cost Per KG")


class TicketStatus(
    models.TextChoices
):  # Nimeipa jina la 'TicketStatus' au 'TaskStatus' ili iwe bayana kuliko 'STATUS_CHOICES' ya jumla
    OPEN = "OPEN", _("Open")
    IN_PROGRESS = "IN_PROGRESS", _("In Progress")
    CLOSED = "CLOSED", _("Resolved")


class TaskPriority(
    models.TextChoices
):  # Nimeipa jina la 'TaskPriority' kuleta maana halisi ya kiutendaji shambani
    LOW = "LOW", _("Low")
    NORMAL = "NORMAL", _("Normal")
    URGENT = "URGENT", _("Urgent/Safety")


""" MISCELLANEOUS / LEGACY """


class RecipientType(
    models.IntegerChoices
):  # Nimeipa jina 'RecipientType' au 'ChatType' kulingana na muktadha
    USER = 0, _("User")
    GROUP = 1, _("Group")
    BROADCAST = 2, _("Broadcast")
    AGENT = 3, _("Agent")
