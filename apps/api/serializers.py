from rest_framework import serializers
from apps.accounts.models import User, Department
from apps.tickets.models import Ticket, Comment, Attachment, Category, Application, TicketHistory
from apps.projects.models import Project, Sprint, UserStory
from apps.notifications.models import Notification


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'description', 'is_it_department']


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name',
                  'role', 'department', 'department_name']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'type', 'name', 'description', 'icon', 'color']


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'author', 'author_name', 'content', 'is_internal', 'created_at']
        read_only_fields = ['author', 'created_at']

    def get_author_name(self, obj):
        return obj.author.get_full_name() if obj.author else ''


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'filename', 'file', 'file_size', 'created_at']
        read_only_fields = ['filename', 'file_size', 'created_at']


class TicketHistorySerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = TicketHistory
        fields = ['id', 'user_name', 'action', 'field_name', 'old_value', 'new_value', 'created_at']

    def get_user_name(self, obj):
        return obj.user.get_full_name() if obj.user else 'Système'


class TicketListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'number', 'title',
            'category', 'category_name',
            'priority', 'priority_display',
            'status', 'status_display',
            'created_by', 'created_by_name',
            'assigned_to', 'assigned_to_name',
            'created_at',
            'sla_response_deadline', 'sla_resolution_deadline',
            'sla_response_exceeded', 'sla_resolution_exceeded',
            'resolved_out_of_sla',
            'is_overdue',
        ]

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else ''

    def get_assigned_to_name(self, obj):
        return obj.assigned_to.get_full_name() if obj.assigned_to else ''


class TicketDetailSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    history = TicketHistorySerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    processing_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'number', 'title', 'description',
            'category', 'sub_category', 'application', 'department',
            'priority', 'priority_display',
            'status', 'status_display',
            'created_by', 'assigned_to',
            'created_at', 'updated_at', 'assigned_at', 'resolved_at', 'closed_at',
            'sla_response_deadline', 'sla_resolution_deadline',
            'sla_response_exceeded', 'sla_resolution_exceeded',
            'resolved_out_of_sla',
            'is_overdue', 'processing_time',
            'rejection_reason',
            'comments', 'attachments', 'history',
        ]
        read_only_fields = ['number', 'created_at', 'updated_at']


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'sub_category',
                  'application', 'department', 'priority', 'target_department']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        return super().create(validated_data)


class ProjectSerializer(serializers.ModelSerializer):
    completion_percent = serializers.IntegerField(read_only=True)
    manager_name = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'code', 'description', 'status',
                  'manager', 'manager_name', 'start_date', 'end_date',
                  'completion_percent', 'created_at']

    def get_manager_name(self, obj):
        return obj.manager.get_full_name() if obj.manager else ''


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'type', 'event',
                  'is_read', 'ticket', 'url', 'created_at']
