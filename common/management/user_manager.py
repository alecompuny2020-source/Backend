from django.contrib.auth.models import BaseUserManager


class EnterpriseUserManager(BaseUserManager):
    def create_user(self, email=None, password=None, **extra_fields):
        if not email and not extra_fields.get("phone_number"):
            raise ValueError("Either email or phone number must be set")
        user = self.model(email=email or None, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)
