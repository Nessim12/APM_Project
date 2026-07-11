from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone
from .models import VirtualMachine, VMMetric
from .serializers import VirtualMachineSerializer, VMMetricSerializer

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
        
    # Get last 50 metrics to avoid huge payloads
    metrics = vm.metrics.all()[:50]
    serializer = VMMetricSerializer(metrics, many=True)
    return Response(serializer.data)
