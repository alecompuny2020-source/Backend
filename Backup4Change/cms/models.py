from django.db import models
from django.utils.translation import gettext_lazy as _
from ..helpers import TYPE_CHOICES

# Create your models here.

class Jid(models.Model):
    """
    The central address book for the system.
    Unified ID for Users, Groups, and Automated Agents (IoT sensors).
    """

    user = models.TextField(_("User Identifier"))
    server = models.TextField(_("Server Domain"), default="wonderful.poultry")
    agent = models.IntegerField(_("Agent Type"), default=0)  # 0: Human, 1: System Bot
    device = models.IntegerField(_("Device ID"), default=0)
    type = models.IntegerField(_("JID Type"), choices=TYPE_CHOICES)
    raw_string = models.TextField(
        _("Full JID String"), unique=True
    )  # e.g. manager_01@wonderful.poultry

    class Meta:
        db_table = "jid"
        verbose_name = _("JID Entity")

    def __str__(self):
        return self.raw_string


class Chat(models.Model):
    """
    Container for conversations. Links a JID to a message thread.
    """

    jid_row = models.OneToOneField(Jid, on_delete=models.CASCADE, related_name="chat")
    subject = models.TextField(_("Chat Subject"), null=True, blank=True)
    created_timestamp = models.BigIntegerField(_("Created Unix TS"))
    unseen_message_count = models.IntegerField(_("Unseen Count"), default=0)
    last_message_row_id = models.IntegerField(_("Last Message ID"), null=True)
    archived = models.BooleanField(_("Is Archived"), default=False)

    class Meta:
        db_table = "chat"
        verbose_name = _("Chat Thread")


class Message(models.Model):
    """
    The core Message entity. Tracks every interaction across the farm ecosystem.
    """

    chat_row = models.ForeignKey(
        Chat, on_delete=models.CASCADE, related_name="messages"
    )
    from_me = models.IntegerField(
        _("Direction"), choices=[(1, "Outgoing"), (0, "Incoming")]
    )
    key_id = models.TextField(_("Unique Message Key"), db_index=True)
    sender_jid_row = models.ForeignKey(
        Jid, on_delete=models.SET_NULL, null=True, related_name="sent_messages"
    )

    status = models.IntegerField(
        _("Delivery Status"), default=0
    )  # 0: Sent, 1: Delivered, 2: Read
    timestamp = models.BigIntegerField(_("Timestamp (ms)"), db_index=True)

    # Message Types: 0: Text, 1: Image, 2: Video, 3: Audio, 4: Location, 5: Document
    message_type = models.IntegerField(_("Message Type"), default=0)
    text_data = models.TextField(_("Text Content"), null=True, blank=True)
    starred = models.IntegerField(_("Is Starred"), default=0)

    # Threading logic for replies
    quoted_row_id = models.IntegerField(_("Quoted Message ID"), null=True, blank=True)

    class Meta:
        db_table = "message"
        indexes = [
            models.Index(fields=["key_id"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"Msg {self.key_id[:8]} from {self.sender_jid}"


class MessageMedia(models.Model):
    """
    Metadata for attachments. Useful for flock health photos or receipt scans.
    """

    message_row = models.OneToOneField(
        Message, on_delete=models.CASCADE, primary_key=True, related_name="media"
    )
    file = models.FileField(_("File Storage"))
    file_size = models.BigIntegerField(_("File Size (Bytes)"))
    mime_type = models.TextField(_("MIME Type"))
    media_key = models.BinaryField(_("Encryption Key"), null=True)
    file_hash = models.TextField(_("File Hash (SHA256)"))

    # Physical specs
    media_duration = models.IntegerField(_("Duration (sec)"), null=True)
    width = models.IntegerField(_("Width"), null=True)
    height = models.IntegerField(_("Height"), null=True)

    class Meta:
        db_table = "message_media"


class GroupParticipantUser(models.Model):
    """
    Staff and Tenant group management.
    """

    group_jid_row = models.ForeignKey(
        Jid, on_delete=models.CASCADE, related_name="group_members"
    )
    user_jid_row = models.ForeignKey(Jid, on_delete=models.CASCADE)

    # Rank: 1: Member, 2: Admin, 3: Creator
    rank = models.IntegerField(_("Permission Rank"), default=1)
    pending = models.IntegerField(_("Pending Invite"), default=0)

    class Meta:
        db_table = "group_participant_user"
        unique_together = ("group_jid_row", "user_jid_row")


# class PayTransaction(models.Model):
#     """
#     Financial Communication: Links a message directly to a Payment event.
#     Crucial for Tenant rent payments or Mobile Money receipts.
#     """
#     message_row = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='payment_details')
#     external_id = models.TextField(_("External Provider ID"), unique=True) # e.g. M-Pesa Ref
#     timestamp = models.BigIntegerField(_("Transaction TS"))
#     status = models.IntegerField(_("Payment Status")) # 0: Pending, 1: Success, 2: Failed
#
#     amount_1000 = models.BigIntegerField(_("Amount (Minor Units)")) # TZS 5,000.00 stored as 5000000
#     currency_code = models.TextField(_("Currency Code"), default="TZS")
#
#     sender_jid_row = models.ForeignKey(Jid, on_delete=models.PROTECT, related_name='payments_sent')
#     receiver_jid_row = models.ForeignKey(Jid, on_delete=models.PROTECT, related_name='payments_received')
#
#     class Meta:
#         db_table = 'pay_transaction'
