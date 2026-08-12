from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from apps.tickets.models import Ticket, Comment, Category
from apps.projects.models import Project
from apps.notifications.models import Notification
from apps.accounts.models import User
from apps.accounts.permissions import IsAdminRole
from .serializers import (
    TicketListSerializer, TicketDetailSerializer, TicketCreateSerializer,
    CommentSerializer, CategorySerializer, ProjectSerializer,
    NotificationSerializer, UserSerializer,
)


class TicketViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminRole]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'category']
    search_fields = ['number', 'title', 'description']
    ordering_fields = ['created_at', 'priority', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        # Guard pour drf-spectacular (génération du schéma sans utilisateur)
        if getattr(self, 'swagger_fake_view', False):
            return Ticket.objects.none()
        from apps.tickets.views import get_tickets_for_user
        return get_tickets_for_user(self.request.user).select_related(
            'category', 'created_by', 'assigned_to', 'application'
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return TicketCreateSerializer
        if self.action in ['retrieve', 'update', 'partial_update']:
            return TicketDetailSerializer
        return TicketListSerializer

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        ticket = self.get_object()
        new_status = request.data.get('status')
        allowed = ticket.get_allowed_transitions(request.user)
        if new_status not in allowed:
            return Response({'error': 'Transition non autorisée.'}, status=status.HTTP_400_BAD_REQUEST)
        ticket.status = new_status
        if new_status == Ticket.STATUS_RESOLU:
            ticket.resolved_at = timezone.now()
        if new_status == Ticket.STATUS_CLOTURE:
            ticket.closed_at = timezone.now()
        ticket.save()
        return Response({'status': ticket.get_status_display()})

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        ticket = self.get_object()
        user_id = request.data.get('user_id')
        try:
            agent = User.objects.get(
                pk=user_id,
                role__in=[User.ROLE_ADMIN, User.ROLE_AGENT, User.ROLE_TECHNICIEN]
            )
            ticket.assigned_to = agent
            if ticket.status == Ticket.STATUS_NOUVEAU:
                ticket.status = Ticket.STATUS_AFFECTE
                ticket.assigned_at = timezone.now()
            ticket.save()
            return Response({'assigned_to': str(agent)})
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur invalide.'}, status=400)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        ticket = self.get_object()
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(ticket=ticket, author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=400)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAdminRole]


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAdminRole]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'success': True})


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_active=True).select_related('department')
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
