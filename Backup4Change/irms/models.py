import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import get_text_lazy as _

# Create your models here.

class JobOpening(models.Model):
    """
    Corresponds to 'post job opening' oval.
    A blueprint for a role needing to be filled.
    """
    JOB_STATUS = (
        ('DRAFT', _('Draft')),
        ('OPEN', _('Open')),
        ('CLOSED', _('Closed')),
        ('CANCELLED', _('Cancelled')),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_("Job Title"), max_length=255)
    description = models.TextField(_("Job Description"))
    department = models.ForeignKey(
        "hrms.Department",  # Linking to your Department model
        on_delete=models.SET_NULL,
        null=True,
        related_name="job_openings",
        verbose_name=_("Department")
    )
    status = models.CharField(
        max_length=10,
        choices=JOB_STATUS,
        default='DRAFT',
        help_text=_("Current state of the job opening.")
    )

    # Audit Fields (Standard in enterprise apps)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_jobs",
        verbose_name=_("Recruitment Manager")
    )

    def __str__(self):
        return f"{self.title} ({self.department.name if self.department else 'N/A'})"

    class Meta:
        db_table = 'job_opening'
        verbose_name = _("Job Opening")
        verbose_name_plural = _("Job Openings")
        ordering = ['-created_at']


class ApplicantProfile(models.Model):
    """
    Corresponds to 'view applicant profile' oval.
    Stores personal and professional details of an applicant.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(_("First Name"), max_length=100)
    last_name = models.CharField(_("Last Name"), max_length=100)
    email = models.EmailField(_("Email Address"), unique=True)
    phone_number = models.CharField(_("Phone Number"), max_length=20, blank=True)

    resume = models.FileField(
        _("Resume/CV"),
        upload_to='resumes/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text=_("PDF, DOCX format recommended.")
    )
    linkedin_profile = models.URLField(_("LinkedIn Profile"), blank=True)
    notes = models.TextField(_("Recruitment Manager Notes"), blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        db_table = "applicant_profile"
        verbose_name = _("Applicant Profile")
        verbose_name_plural = _("Applicant Profiles")


class JobApplication(models.Model):
    """
    The link between an Applicant and a Job Opening.
    This also handles the 'onboard new hire' oval via status change.
    """
    APPLICATION_STATUS = (
        ('APPLIED', _('Applied')),
        ('REVIEW', _('Under Review')),
        ('INTERVIEW', _('Interviewing')),
        ('OFFER', _('Offer Extended')),
        ('ACCEPTED', _('Offer Accepted')), # Trigger for onboarding
        ('ONBOARDING', _('Onboarding')),   # Active onboarding state
        ('HIRED', _('Hired')),             # Complete
        ('REJECTED', _('Rejected')),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    applicant = models.ForeignKey(
        ApplicantProfile,
        on_delete=models.CASCADE,
        related_name="applications"
    )
    job_opening = models.ForeignKey(
        JobOpening,
        on_delete=models.CASCADE,
        related_name="applications"
    )
    status = models.CharField(
        max_length=12,
        choices=APPLICATION_STATUS,
        default='APPLIED'
    )
    applied_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "job_application"
        verbose_name = _("Job Application")
        verbose_name_plural = _("Job Applications")
        unique_together = ('applicant', 'job_opening') # Prevents double applications

    def __str__(self):
        return f"{self.applicant} -> {self.job_opening.title}"


class Interview(models.Model):
    """
    Corresponds to 'schedule interview' oval.
    Links an Application to a time and place.
    """
    INTERVIEW_TYPE = (
        ('PHONE', _('Phone Screen')),
        ('VIDEO', _('Video Call')),
        ('IN_PERSON', _('In-Person')),
        ('TECHNICAL', _('Technical Assessment')),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Link to the specific application, not just the applicant
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="interviews"
    )
    scheduled_time = models.DateTimeField(_("Scheduled Time"))
    interview_type = models.CharField(
        max_length=10,
        choices=INTERVIEW_TYPE,
        default='VIDEO'
    )
    location_link = models.CharField(
        _("Location / Video Link"),
        max_length=255,
        blank=True,
        help_text=_("Physical address or Teams/Zoom link.")
    )

    # The 'Recruitment Manager' or other interviewers involved
    interviewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="scheduled_interviews",
        verbose_name=_("Interview Panel")
    )

    recruitment_manager_notes = models.TextField(_("Post-Interview Feedback"), blank=True)

    def __str__(self):
        return f"Interview: {self.application.applicant} for {self.application.job_opening.title}"

    class Meta:
        db_table = "interview"
        verbose_name = _("Interview")
        verbose_name_plural = _("Interviews")
        ordering = ['scheduled_time']
