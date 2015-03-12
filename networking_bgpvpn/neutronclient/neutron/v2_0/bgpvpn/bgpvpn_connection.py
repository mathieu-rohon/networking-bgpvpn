import logging
from neutronclient.common import extension
from neutronclient.neutron import v2_0 as neutronv20
from neutronclient.i18n import _


class BGPVPNConnection(extension.NeutronClientExtension):
    resource = 'bgpvpn_connection'
    resource_plural = '%ss' % resource
    object_path = '/%s' % resource_plural
    resource_path = '/%s/%%s' % resource_plural
    versions = ['2.0']


class BGPVPNConnectionList(extension.ClientExtensionList,
                           BGPVPNConnection):
    """List BGP VPN connections that belongs to a given tenant."""

    shell_command = 'bgpvpn-connection-list'
    list_columns = [
        'id', 'name', 'type', 'route_targets', 'import_targets',
        'export_targets', 'network_id', 'auto_aggregate', 'tenant_id']
    pagination_support = True
    sorting_support = True
