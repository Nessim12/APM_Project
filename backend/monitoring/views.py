from datetime import timedelta

from django.db.models import Avg, Max, Count, Q
from django.db.models.functions import TruncDate, TruncHour
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import VirtualMachine, VMMetric
from .serializers import VirtualMachineSerializer, VMMetricSerializer

CPU_ALERT_THRESHOLD = 70.0
RAM_ALERT_THRESHOLD = 70.0
DISK_ALERT_THRESHOLD = 90.0

class VMTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        
        try:
            # Format: "Token <uuid>"
            token = auth_header.split(' ')[1]
            vm = VirtualMachine.objects.get(token=token)
        except (IndexError, VirtualMachine.DoesNotExist):
            raise AuthenticationFailed('Invalid VM token.')
            
        # We return the vm as the "user" for this request
        return (vm, None)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def register_vm(request):
    """
    Registers a new VM or updates an existing one by hostname.
    Returns the VM token.
    """
    hostname = request.data.get('hostname')
    if not hostname:
        return Response({'error': 'hostname is required'}, status=status.HTTP_400_BAD_REQUEST)
        
    vm, created = VirtualMachine.objects.get_or_create(
        hostname=hostname,
        defaults={
            'ip_address': request.data.get('ip_address', '0.0.0.0'),
            'operating_system': request.data.get('operating_system', ''),
            'cpu_count': request.data.get('cpu_count', 1),
            'total_ram': request.data.get('total_ram', 0.0),
            'total_disk': request.data.get('total_disk', 0.0),
        }
    )
    
    if not created:
        vm.ip_address = request.data.get('ip_address', vm.ip_address)
        vm.operating_system = request.data.get('operating_system', vm.operating_system)
        vm.cpu_count = request.data.get('cpu_count', vm.cpu_count)
        vm.total_ram = request.data.get('total_ram', vm.total_ram)
        vm.total_disk = request.data.get('total_disk', vm.total_disk)
        vm.last_seen = timezone.now()
        vm.save()
        
    return Response({'token': vm.token, 'id': vm.id})

@api_view(['POST'])
@authentication_classes([VMTokenAuthentication])
def heartbeat(request):
    """
    Updates the VM's last_seen timestamp.
    """
    vm = request.user
    vm.last_seen = timezone.now()
    vm.save(update_fields=['last_seen'])
    return Response({'status': 'ok'})

@api_view(['POST'])
@authentication_classes([VMTokenAuthentication])
def receive_metrics(request):
    """
    Receives CPU/RAM/Disk metrics for a VM.
    """
    vm = request.user
    cpu_usage = request.data.get('cpu_usage', 0.0)
    ram_usage = request.data.get('ram_usage', 0.0)
    disk_usage = request.data.get('disk_usage', 0.0)
    
    VMMetric.objects.create(
        virtual_machine=vm,
        cpu_usage=cpu_usage,
        ram_usage=ram_usage,
        disk_usage=disk_usage
    )
    
    # Also update last_seen as this acts like a heartbeat
    vm.last_seen = timezone.now()
    vm.save(update_fields=['last_seen'])
    
    return Response({'status': 'ok'})

@api_view(['GET'])
@authentication_classes([]) # Or you could secure this for dashboard use
@permission_classes([])
def vm_list(request):
    """
    Returns all VMs with their latest metrics.
    """
    vms = VirtualMachine.objects.all().order_by('hostname')
    # Prefetch metrics for performance
    vms = vms.prefetch_related('metrics')
    serializer = VirtualMachineSerializer(vms, many=True)
    return Response(serializer.data)

def _parse_days(request, default=7, maximum=30):
    try:
        days = int(request.query_params.get('days', default))
    except (TypeError, ValueError):
        days = default
    return max(1, min(days, maximum))


def _alert_filter():
    return (
        Q(cpu_usage__gte=CPU_ALERT_THRESHOLD)
        | Q(ram_usage__gte=RAM_ALERT_THRESHOLD)
        | Q(disk_usage__gte=DISK_ALERT_THRESHOLD)
    )


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def vm_metrics_history(request, pk):
    """
    Returns metric history for a specific VM.
    """
    try:
        vm = VirtualMachine.objects.get(pk=pk)
    except VirtualMachine.DoesNotExist:
        return Response({'error': 'VM not found'}, status=status.HTTP_404_NOT_FOUND)

    days = _parse_days(request, default=7)
    since = timezone.now() - timedelta(days=days)
    metrics = vm.metrics.filter(timestamp__gte=since).order_by('timestamp')[:500]
    serializer = VMMetricSerializer(metrics, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def metrics_summary(request):
    """
    Fleet-wide aggregated metrics: daily averages, spikes, and log alerts.
    """
    days = _parse_days(request, default=7)
    since = timezone.now() - timedelta(days=days)
    qs = VMMetric.objects.filter(timestamp__gte=since)

    fleet_stats = qs.aggregate(
        avg_cpu=Avg('cpu_usage'),
        avg_ram=Avg('ram_usage'),
        avg_disk=Avg('disk_usage'),
        max_cpu=Max('cpu_usage'),
        max_ram=Max('ram_usage'),
        max_disk=Max('disk_usage'),
    )

    daily = (
        qs.annotate(day=TruncDate('timestamp'))
        .values('day')
        .annotate(
            avg_cpu=Avg('cpu_usage'),
            avg_ram=Avg('ram_usage'),
            avg_disk=Avg('disk_usage'),
            max_cpu=Max('cpu_usage'),
            max_ram=Max('ram_usage'),
            max_disk=Max('disk_usage'),
            log_alerts=Count('id', filter=_alert_filter()),
        )
        .order_by('day')
    )

    daily_data = [
        {
            'date': row['day'].isoformat() if row['day'] else None,
            'avg_cpu': round(row['avg_cpu'] or 0, 1),
            'avg_ram': round(row['avg_ram'] or 0, 1),
            'avg_disk': round(row['avg_disk'] or 0, 1),
            'max_cpu': round(row['max_cpu'] or 0, 1),
            'max_ram': round(row['max_ram'] or 0, 1),
            'max_disk': round(row['max_disk'] or 0, 1),
            'log_alerts': row['log_alerts'],
        }
        for row in daily
    ]

    hourly = (
        qs.annotate(hour=TruncHour('timestamp'))
        .values('hour')
        .annotate(
            avg_cpu=Avg('cpu_usage'),
            avg_ram=Avg('ram_usage'),
            avg_disk=Avg('disk_usage'),
        )
        .order_by('hour')
    )

    hourly_data = [
        {
            'hour': row['hour'].strftime('%Y-%m-%d %H:%M') if row['hour'] else None,
            'avg_cpu': round(row['avg_cpu'] or 0, 1),
            'avg_ram': round(row['avg_ram'] or 0, 1),
            'avg_disk': round(row['avg_disk'] or 0, 1),
        }
        for row in hourly
    ]

    total_alerts = qs.filter(_alert_filter()).count()
    avg_alerts_per_day = round(total_alerts / days, 1) if days else 0

    return Response({
        'period_days': days,
        'fleet': {
            'avg_cpu': round(fleet_stats['avg_cpu'] or 0, 1),
            'avg_ram': round(fleet_stats['avg_ram'] or 0, 1),
            'avg_disk': round(fleet_stats['avg_disk'] or 0, 1),
            'max_cpu': round(fleet_stats['max_cpu'] or 0, 1),
            'max_ram': round(fleet_stats['max_ram'] or 0, 1),
            'max_disk': round(fleet_stats['max_disk'] or 0, 1),
            'total_log_alerts': total_alerts,
            'avg_log_alerts_per_day': avg_alerts_per_day,
        },
        'daily': daily_data,
        'hourly': hourly_data,
    })


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def vm_metrics_summary(request, pk):
    """
    Per-VM aggregated metrics for charts.
    """
    try:
        vm = VirtualMachine.objects.get(pk=pk)
    except VirtualMachine.DoesNotExist:
        return Response({'error': 'VM not found'}, status=status.HTTP_404_NOT_FOUND)

    days = _parse_days(request, default=7)
    since = timezone.now() - timedelta(days=days)
    qs = vm.metrics.filter(timestamp__gte=since)

    vm_stats = qs.aggregate(
        avg_cpu=Avg('cpu_usage'),
        avg_ram=Avg('ram_usage'),
        avg_disk=Avg('disk_usage'),
        max_cpu=Max('cpu_usage'),
        max_ram=Max('ram_usage'),
        max_disk=Max('disk_usage'),
    )

    total_alerts = qs.filter(_alert_filter()).count()
    avg_alerts_per_day = round(total_alerts / days, 1) if days else 0

    daily = (
        qs.annotate(day=TruncDate('timestamp'))
        .values('day')
        .annotate(
            avg_cpu=Avg('cpu_usage'),
            avg_ram=Avg('ram_usage'),
            avg_disk=Avg('disk_usage'),
            max_cpu=Max('cpu_usage'),
            max_ram=Max('ram_usage'),
            log_alerts=Count('id', filter=_alert_filter()),
        )
        .order_by('day')
    )

    hourly = (
        qs.annotate(hour=TruncHour('timestamp'))
        .values('hour')
        .annotate(
            avg_cpu=Avg('cpu_usage'),
            avg_ram=Avg('ram_usage'),
        )
        .order_by('hour')
    )

    return Response({
        'vm_id': vm.id,
        'hostname': vm.hostname,
        'period_days': days,
        'stats': {
            'avg_cpu': round(vm_stats['avg_cpu'] or 0, 1),
            'avg_ram': round(vm_stats['avg_ram'] or 0, 1),
            'avg_disk': round(vm_stats['avg_disk'] or 0, 1),
            'max_cpu': round(vm_stats['max_cpu'] or 0, 1),
            'max_ram': round(vm_stats['max_ram'] or 0, 1),
            'max_disk': round(vm_stats['max_disk'] or 0, 1),
            'total_log_alerts': total_alerts,
            'avg_log_alerts_per_day': avg_alerts_per_day,
        },
        'daily': [
            {
                'date': row['day'].isoformat() if row['day'] else None,
                'avg_cpu': round(row['avg_cpu'] or 0, 1),
                'avg_ram': round(row['avg_ram'] or 0, 1),
                'avg_disk': round(row['avg_disk'] or 0, 1),
                'max_cpu': round(row['max_cpu'] or 0, 1),
                'max_ram': round(row['max_ram'] or 0, 1),
                'log_alerts': row['log_alerts'],
            }
            for row in daily
        ],
        'hourly': [
            {
                'hour': row['hour'].strftime('%Y-%m-%d %H:%M') if row['hour'] else None,
                'avg_cpu': round(row['avg_cpu'] or 0, 1),
                'avg_ram': round(row['avg_ram'] or 0, 1),
            }
            for row in hourly
        ],
    })
