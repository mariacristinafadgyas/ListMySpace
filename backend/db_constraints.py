from enum import Enum


class RoleEnum(Enum):
    ADMIN = 'admin'
    OWNER = 'owner'
    CUSTOMER = 'customer'


class ActionEnum(Enum):
    RENT = 'Rent'
    BUY = 'Buy'


class CommercialCategoryEnum(Enum):
    OFFICE = 'Office'
    COMMERCIAL = 'Commercial'
    INDUSTRIAL = 'Industrial'
    INVESTMENT_LAND = 'Investment land'
    HOTEL_GUESTHOUSE = 'Hotel/Guesthouse'
    SPECIAL_PROPERTIES = 'Special properties'
    OTHER = 'Other'


class LandTypeEnum(Enum):
    CONSTRUCTIONS = 'Constructions'
    AGRICULTURAL = 'Agricultural'
    FOREST = 'Forest'
    ORCHARD = 'Orchard'
    MEADOW = 'Meadow'
    PASTURE = 'Pasture'
    FISHPOND = 'Fishpond'
    OTHER = 'Other'


class LandCategoryEnum(Enum):
    INTRAVILAN = 'Intravilan'
    EXTRAVILAN = 'Extravilan'
