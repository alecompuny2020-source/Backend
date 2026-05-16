from django.db import models
from django.db import models, transaction
from django.conf import settings
import uuid
from django.contrib.postgres.indexes import GinIndex
from django.db.models import Avg
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from common.choices import (
    BATCH_STATUS_CHOICES, BIRD_TYPE_CHOICES, CYCLE_STATUS,
    BIRD_TYPE_CHOICES, CURRENCY_CHOICES, HEALTH_RECORD_TYPE, OUTBREAK_STATUS
    )
from common.mixins import FarmAuditBaseModelMixin
# from ppms.models import ProcessingPlant


# Create your models here.
