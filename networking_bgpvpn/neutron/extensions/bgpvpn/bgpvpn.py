# Copyright (c) 2015 Orange.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import abc

import six

import logging

from networking_bgpvpn.neutron.extensions import bgpvpn as bgpvpn_ext
from neutron.api import extensions
from neutron.api.v2 import attributes as attr
from neutron.api.v2 import resource_helper
from neutron.plugins.common import constants
from neutron.services.service_base import ServicePluginBase


LOG = logging.getLogger(__name__)

BGPVPN_L3 = 'l3'
BGPVPN_L2 = 'l2'
BGPVPN_TYPES = [BGPVPN_L3, BGPVPN_L2]


# Regular expression to validate Route Target list format
# ["<asn1>:<nn1>","<asn2>:<nn2>", ...] with asn and nn in range 0-65535
RT_REGEX = ('^((?:0|[1-9]\d{0,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]'
            '\d|6553[0-5]):(?:0|[1-9]\d{0,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d'
            '{2}|655[0-2]\d|6553[0-5]))$')

extensions.append_api_extensions_path(bgpvpn_ext.__path__)
constants.BGPVPN = "BGPVPN"
constants.ALLOWED_SERVICES.append(constants.BGPVPN)
constants.COMMON_PREFIXES["BGPVPN"] = "/bgpvpn"


def _validate_rt_list(data, valid_values=None):
    if not isinstance(data, list):
        msg = _("'%s' is not a list") % data
        LOG.debug(msg)
        return msg

    for item in data:
        msg = attr._validate_regex(item, RT_REGEX)
        if msg:
            LOG.debug(msg)
            return msg

    if len(set(data)) != len(data):
        msg = _("Duplicate items in the list: '%s'") % ', '.join(data)
        LOG.debug(msg)
        return msg


def _validate_rt_list_or_none(data, valid_values=None):
    if not data:
        return _validate_rt_list(data, valid_values=valid_values)

validators = {'type:route_target_list': _validate_rt_list,
              'type:route_target_list_or_none': _validate_rt_list_or_none}
attr.validators.update(validators)

RESOURCE_ATTRIBUTE_MAP = {
    'bgpvpn_connections': {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
               'primary_key': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:string': None},
                      'required_by_policy': True,
                      'is_visible': True},
        'network_id': {'allow_post': True, 'allow_put': True,
                       'default': None,
                       'validate': {'type:uuid_or_none': None},
                       'is_visible': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'default': '',
                 'validate': {'type:string': None},
                 'is_visible': True},
        'type': {'allow_post': True, 'allow_put': False,
                 'default': BGPVPN_L3,
                 'validate': {'type:values': BGPVPN_TYPES},
                 'is_visible': True},
        'route_targets': {'allow_post': True, 'allow_put': True,
                          'default': [],
                          'convert_to': attr.convert_to_list,
                          'validate': {'type:route_target_list': None},
                          'is_visible': True},
        'import_targets': {'allow_post': True, 'allow_put': True,
                           'default': None,
                           'convert_to': attr.convert_to_list,
                           'validate': {'type:route_target_list_or_none':
                                        None},
                           'is_visible': True},
        'export_targets': {'allow_post': True, 'allow_put': True,
                           'default': None,
                           'convert_to': attr.convert_to_list,
                           'validate': {'type:route_target_list_or_none':
                                        None},
                           'is_visible': True},
        'auto_aggregate': {'allow_post': True, 'allow_put': True,
                           'default': True,
                           'validate': {'type:boolean': None},
                           'convert_to': attr.convert_to_boolean,
                           'is_visible': True},
    },
}


class Bgpvpn(extensions.ExtensionDescriptor):

    @classmethod
    def get_name(cls):
        return "BGPVPN Connection extension"

    @classmethod
    def get_alias(cls):
        return "bgpvpn"

    @classmethod
    def get_description(cls):
        return "Extension for BGPVPN Connection service"

    @classmethod
    def get_namespace(cls):
        return "http://wiki.openstack.org/Neutron/bgpvpn/API_1.0"

    @classmethod
    def get_updated(cls):
        return "2014-06-10T17:00:00-00:00"

    @classmethod
    def get_resources(cls):
        plural_mappings = resource_helper.build_plural_mappings(
            {}, RESOURCE_ATTRIBUTE_MAP)
        plural_mappings['route_targets'] = 'route_target'
        plural_mappings['import_targets'] = 'import_target'
        plural_mappings['export_targets'] = 'export_target'
        attr.PLURALS.update(plural_mappings)
        return resource_helper.build_resource_info(plural_mappings,
                                                   RESOURCE_ATTRIBUTE_MAP,
                                                   constants.BGPVPN,
                                                   register_quota=True,
                                                   translate_name=True)

    @classmethod
    def get_plugin_interface(cls):
        return BGPVPNPluginBase

    def update_attributes_map(self, attributes):
        super(Bgpvpn, self).update_attributes_map(
            attributes, extension_attrs_map=RESOURCE_ATTRIBUTE_MAP)

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}


@six.add_metaclass(abc.ABCMeta)
class BGPVPNPluginBase(ServicePluginBase):

    def get_plugin_name(self):
        return constants.BGPVPN

    def get_plugin_type(self):
        return constants.BGPVPN

    def get_plugin_description(self):
        return 'BGP VPN service plugin'

    @abc.abstractmethod
    def create_bgpvpn_connection(self, context, bgpvpn_connection):
        pass

    @abc.abstractmethod
    def get_bgpvpn_connections(self, context, filters=None, fields=None):
        pass

    @abc.abstractmethod
    def get_bgpvpn_connection(self, context, id, fields=None):
        pass

    @abc.abstractmethod
    def update_bgpvpn_connection(self, context, id, bgpvpn_connection):
        pass

    @abc.abstractmethod
    def delete_bgpvpn_connection(self, context, id):
        pass
