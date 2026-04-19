from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from django.db import transaction
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from phonenumber_field.phonenumber import to_python
from rest_framework.decorators import action
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from core.models import User, Otp
from common.managers import EnterpriseOTPandLinkManager as OTPManager
from core.serializers import (RegistrationSerializer, ConfirmRegistrationSerializer,
RequestLoginOTPSerializer, LoginConfirmOTPSerializer, UserTokenObtainPairSerializer,
RequestOTPSerializer, ConfirmPasswordResetSerializer, ConfirmForgotPasswordSerializer)


class AuthViewSet(viewsets.GenericViewSet):

    """ A view that Consolidated authentication flows (registration, login, password reset, and forgot password)"""

    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all()

    def _get_auth_response(self, user, message):
        # Issue tokens using your custom Base64-encoding serializer
        token_serializer = UserTokenObtainPairSerializer()
        refresh = token_serializer.get_token(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user_data": token_serializer.get_user_data(user),
            "message": message # Keeps the manager's success message
        }, status=status.HTTP_200_OK)

    def _handle_otp_request(self, request, token_type):
        """Generic method for requesting various OTP types."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data["identifier"]
        return OTPManager.generate_and_send(identifier, token_type )

    @action(detail=False, methods=["post"], serializer_class=RegistrationSerializer)
    def initiate_registration(self, request):
        """Attains self user registration"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()

            customer_group, created = Group.objects.filter(
                Q(name="Customer"),
            ).get_or_create(name="Customer")
            user.groups.add(customer_group)

        return Response(_("Registration success. OTP sent for verification."))

    @action(detail = False, methods=['post'], serializer_class = ConfirmRegistrationSerializer)
    def confirm_registration(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 'identifier' is used instead of 'email or phone number since identifier may carry one of the two'
        identifier = serializer.validated_data["identifier"]
        code = serializer.validated_data["OTP"]
        token_type = Otp.TOKEN_TYPE_REGISTRATION
        return OTPManager.verify(identifier, code, token_type)

    @action(detail = False, methods=['post'], serializer_class = RequestLoginOTPSerializer)
    def initiate_login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data["identifier"]
        password = serializer.validated_data["password"]
        phone_number = to_python(identifier)

        token_type = Otp.TOKEN_TYPE_LOGIN
        return OTPManager.generate_and_send(identifier, token_type )

    @action(detail = False, methods=['post'], serializer_class = LoginConfirmOTPSerializer)
    def confirm_login(self, request):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception = True)

        identifier = serializer.validated_data["identifier"]
        code = serializer.validated_data["OTP"]
        token_type = Otp.TOKEN_TYPE_LOGIN
        phone_number = to_python(identifier)

        otp_response = OTPManager.verify(identifier, code, token_type)
        if otp_response.status_code == status.HTTP_200_OK:
            user = User.objects.get(
                Q(email__iexact = identifier) | Q(phone_number = phone_number)
            )
            return self._get_auth_response(user, otp_response.data.get("message"))
        return otp_response

    @action(detail=False, methods=["post"], serializer_class=RequestOTPSerializer)
    def request_registration_otp(self, request):
        return self._handle_otp_request(request, Otp.TOKEN_TYPE_REGISTRATION)

    @action(detail=False, methods=["post"], serializer_class=RequestOTPSerializer)
    def request_login_otp(self, request):
        return self._handle_otp_request(request, Otp.TOKEN_TYPE_LOGIN)

    @action(detail=False, methods=["post"], serializer_class=RequestOTPSerializer,
            permission_classes=[permissions.IsAuthenticated])
    def request_password_reset_otp(self, request):
        return self._handle_otp_request(request, Otp.TOKEN_TYPE_PASSWORD_RESET)

    @action(detail=False, methods=["post"], serializer_class=ConfirmPasswordResetSerializer,
            permission_classes=[permissions.IsAuthenticated])
    def confirm_password_reset(self, request):
        """Password reset method that verify OTP for password reset and set a new Password"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(_("Password reset successful."))

    @action(detail=False, methods=["post"], serializer_class=RequestOTPSerializer,
            permission_classes=[permissions.AllowAny])
    def initiate_forgot_password(self, request):
        return self._handle_otp_request(request, Otp.TOKEN_TYPE_PASSWORD_RESET)

    @action(detail = False, serializer_class = ConfirmForgotPasswordSerializer, methods = ['post'])
    def confirm_forgot_password(self, request):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception = True)

        uidbase64 = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            uid = force_str(urlsafe_base64_decode(uidbase64))
            user = User.objects.get(Q(pk=uid))
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):

            user.set_password(new_password)
            user.save()

            return Response(
                {"detail": "Your password was updated. You can now sign in."},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "Invalid or Expired link. Please request a new one."},
            status = status.HTTP_400_BAD_REQUEST,
        )
