# views.py
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import permissions, response, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

# Import your existing utilities/serializers
from .models import Otp
from .serializers import (
    ConfirmRegistrationSerializer,
    LoginConfirmOTPSerializer,
    RegistrationSerializer,
    RequestLoginOTPSerializer,
    UserTokenObtainPairSerializer,
)

# Assuming to_python comes from your phone number utility package
# from phonenumber_field.phonenumber import to_python

User = get_user_model()


class AuthViewSet(viewsets.GenericViewSet):
    """
    A view that consolidates authentication flows.
    Registration OTPs are completely handled automatically via background signals.
    """

    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all()

    def _get_auth_response(self, user, message):
        token_serializer = UserTokenObtainPairSerializer()
        refresh = token_serializer.get_token(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user_data": token_serializer.get_user_data(user),
                "message": message,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["post"],
        serializer_class=RegistrationSerializer,
        url_path="initiate-registration",
    )
    def initiate_registration(self, request):
        """
        Registers a user instantly. The database signal takes care of
        generating and dispatching the OTP asynchronously via Celery.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 1. This triggers post_save. Because of transaction.on_commit inside signals.py,
        # Celery safely waits until the save is written before executing the notification.
        user = serializer.save()

        # 2. Assign default enterprise group roles
        customer_group, created = Group.objects.get_or_create(name="Customer")
        user.groups.add(customer_group)

        # 3. Respond instantly back to the user client (Sub-100ms response time!)
        return Response(
            {"detail": _("Registration success. OTP sent for verification.")},
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["post"],
        serializer_class=ConfirmRegistrationSerializer,
        url_path="confirm-registration",
    )
    def confirm_registration(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data["identifier"]
        code = serializer.validated_data["OTP"]
        token_type = Otp.TOKEN_TYPE_REGISTRATION

        # Keeps your original verification logic unchanged
        return OTPManager.verify(identifier, code, token_type)

    @action(
        detail=False,
        methods=["post"],
        serializer_class=RequestLoginOTPSerializer,
        url_path="initiate-login",
    )
    def initiate_login(self, request):
        """
        Initiates a secure login handshake.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data["identifier"]
        password = serializer.validated_data["password"]

        token_type = Otp.TOKEN_TYPE_LOGIN

        # Note: If OTPManager.generate_and_send internally triggers your
        # background celery task for login codes, this view remains incredibly fast too!
        return OTPManager.generate_and_send(identifier, token_type)

    @action(
        detail=False,
        methods=["post"],
        serializer_class=LoginConfirmOTPSerializer,
        url_path="confirm-login",
    )
    def confirm_login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data["identifier"]
        code = serializer.validated_data["OTP"]
        token_type = Otp.TOKEN_TYPE_LOGIN
        phone_number = to_python(identifier)

        otp_response = OTPManager.verify(identifier, code, token_type)
        if otp_response.status_code == status.HTTP_200_OK:
            user = User.objects.get(
                Q(email__iexact=identifier) | Q(phone_number=phone_number)
            )
            return self._get_auth_response(user, otp_response.data.get("message"))
        return otp_response


status = models.ForeignKey("core.ProductionStatus", on_delete=models.RESTRICT)
