from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from products.models import Product
from orders.models import Order
import uuid

User = get_user_model()

class Review(models.Model):
    """Product reviews and ratings"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending Moderation'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged'),
    )
    
    review_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='customer_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_reviews')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Rating (1-5 stars)
    overall_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Detailed ratings
    quality_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    value_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    freshness_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    packaging_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    
    # Review content
    title = models.CharField(max_length=200)
    comment = models.TextField()
    
    # Verification
    verified_purchase = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Engagement
    helpful_votes = models.PositiveIntegerField(default=0)
    total_votes = models.PositiveIntegerField(default=0)
    
    # Media attachments
    images = models.JSONField(default=list, blank=True)  # Store image URLs
    
    # Moderation
    moderated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='moderated_reviews'
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderation_notes = models.TextField(blank=True)
    
    # Response from seller
    seller_response = models.TextField(blank=True)
    seller_response_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'reviewer']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'status']),
            models.Index(fields=['reviewer', 'created_at']),
            models.Index(fields=['overall_rating', 'status']),
        ]
    
    def __str__(self):
        return f"Review for {self.product.name} by {self.reviewer.username}"
    
    @property
    def helpfulness_ratio(self):
        if self.total_votes > 0:
            return (self.helpful_votes / self.total_votes) * 100
        return 0

class ReviewVote(models.Model):
    """Track helpful/unhelpful votes on reviews"""
    
    VOTE_TYPES = (
        ('helpful', 'Helpful'),
        ('unhelpful', 'Unhelpful'),
    )
    
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='votes')
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_votes')
    vote_type = models.CharField(max_length=10, choices=VOTE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['review', 'voter']
        indexes = [
            models.Index(fields=['review', 'vote_type']),
        ]
    
    def __str__(self):
        return f"{self.voter.username} voted {self.vote_type} on review {self.review.review_id}"

class ReviewReport(models.Model):
    """Reports for inappropriate reviews"""
    
    REPORT_REASONS = (
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('fake', 'Fake Review'),
        ('offensive', 'Offensive Language'),
        ('irrelevant', 'Irrelevant'),
        ('personal_info', 'Contains Personal Information'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    )
    
    report_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_reports')
    
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Moderation
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_reports'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['review', 'status']),
        ]
    
    def __str__(self):
        return f"Report {self.report_id} - {self.reason}"

class ReviewQuestion(models.Model):
    """Questions about products from potential buyers"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('answered', 'Answered'),
        ('closed', 'Closed'),
    )
    
    question_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='questions')
    asker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asked_questions')
    
    question = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Engagement
    helpful_votes = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'status']),
            models.Index(fields=['asker', 'created_at']),
        ]
    
    def __str__(self):
        return f"Question about {self.product.name}"

class ReviewAnswer(models.Model):
    """Answers to product questions"""
    
    answer_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    question = models.ForeignKey(ReviewQuestion, on_delete=models.CASCADE, related_name='answers')
    answerer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='provided_answers')
    
    answer = models.TextField()
    is_seller_answer = models.BooleanField(default=False)  # True if answered by product seller
    verified_purchase = models.BooleanField(default=False)  # True if answerer bought the product
    
    # Engagement
    helpful_votes = models.PositiveIntegerField(default=0)
    total_votes = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-helpful_votes', '-created_at']
        indexes = [
            models.Index(fields=['question', 'is_seller_answer']),
            models.Index(fields=['answerer', 'created_at']),
        ]
    
    def __str__(self):
        return f"Answer to question {self.question.question_id}"
    
    @property
    def helpfulness_ratio(self):
        if self.total_votes > 0:
            return (self.helpful_votes / self.total_votes) * 100
        return 0

class ReviewTemplate(models.Model):
    """Templates for review moderation responses"""
    
    TEMPLATE_TYPES = (
        ('approval', 'Approval Message'),
        ('rejection', 'Rejection Message'),
        ('warning', 'Warning Message'),
        ('request_modification', 'Request Modification'),
    )
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['template_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"

class ReviewAnalytics(models.Model):
    """Daily review analytics"""
    
    date = models.DateField(unique=True)
    
    # Review metrics
    total_reviews = models.PositiveIntegerField(default=0)
    approved_reviews = models.PositiveIntegerField(default=0)
    rejected_reviews = models.PositiveIntegerField(default=0)
    pending_reviews = models.PositiveIntegerField(default=0)
    
    # Rating distribution
    five_star_reviews = models.PositiveIntegerField(default=0)
    four_star_reviews = models.PositiveIntegerField(default=0)
    three_star_reviews = models.PositiveIntegerField(default=0)
    two_star_reviews = models.PositiveIntegerField(default=0)
    one_star_reviews = models.PositiveIntegerField(default=0)
    
    # Engagement metrics
    total_votes = models.PositiveIntegerField(default=0)
    helpful_votes = models.PositiveIntegerField(default=0)
    
    # Q&A metrics
    questions_asked = models.PositiveIntegerField(default=0)
    questions_answered = models.PositiveIntegerField(default=0)
    
    # Moderation metrics
    reports_received = models.PositiveIntegerField(default=0)
    reports_resolved = models.PositiveIntegerField(default=0)
    
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Review Analytics - {self.date}"

class ReviewIncentive(models.Model):
    """Incentives for encouraging reviews"""
    
    INCENTIVE_TYPES = (
        ('discount', 'Discount Coupon'),
        ('points', 'Loyalty Points'),
        ('free_shipping', 'Free Shipping'),
        ('cashback', 'Cashback'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('expired', 'Expired'),
    )
    
    name = models.CharField(max_length=100)
    incentive_type = models.CharField(max_length=20, choices=INCENTIVE_TYPES)
    
    # Conditions
    minimum_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=1
    )
    minimum_comment_length = models.PositiveIntegerField(default=50)
    requires_image = models.BooleanField(default=False)
    requires_verified_purchase = models.BooleanField(default=True)
    
    # Reward details
    reward_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_rewards_per_user = models.PositiveIntegerField(default=1)
    total_rewards_available = models.PositiveIntegerField(null=True, blank=True)
    rewards_claimed = models.PositiveIntegerField(default=0)
    
    # Validity
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Targeting
    target_categories = models.ManyToManyField('products.Category', blank=True)
    target_user_segments = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.incentive_type}"
    
    @property
    def is_active(self):
        from django.utils import timezone
        now = timezone.now()
        return (self.status == 'active' and 
                self.start_date <= now <= self.end_date and
                (not self.total_rewards_available or 
                 self.rewards_claimed < self.total_rewards_available))

class ReviewReward(models.Model):
    """Track rewards given for reviews"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('redeemed', 'Redeemed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    
    reward_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name='reward')
    incentive = models.ForeignKey(ReviewIncentive, on_delete=models.CASCADE, related_name='rewards')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_rewards')
    
    reward_value = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Redemption details
    coupon_code = models.CharField(max_length=50, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['incentive', 'status']),
        ]
    
    def __str__(self):
        return f"Reward {self.reward_id} - {self.incentive.name}"
