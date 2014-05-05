# -*- coding: utf-8 -*-
from StringIO import StringIO
import yaml

from django.core.serializers.pyyaml import Serializer as YamlSerializer
from django.core.serializers.python import Deserializer as PythonDeserializer
from django.utils.encoding import smart_unicode

class Serializer (YamlSerializer):
    """
    Serialize database objects as nested dicts, indexed first by
    model name, then by primary key.
    """
    def start_serialization(self):
        self._current = None
        self.objects = {}

    # noinspection PyProtectedMember,PyProtectedMember
    def end_object(self, obj):
        model = smart_unicode(obj._meta)
        pk = obj._get_pk_val()

        if model not in self.objects:
            self.objects[model] = {}

        self.objects[model][pk] = self._current
        self._current = None


def Deserializer(stream_or_string, **options):
    """
    Deserialize a stream or string of YAML data,
    as written by the Serializer above.
    """
    if isinstance(stream_or_string, basestring):
        stream = StringIO(stream_or_string)
    else:
        stream = stream_or_string

    # Reconstruct the flat object list as PythonDeserializer expects
    # NOTE: This could choke on large data sets, since it
    # constructs the flattened data list in memory
    data = []
    for model, objects in yaml.load(stream).iteritems():
        # Add the model name back into each object dict
        for pk, fields in objects.iteritems():
            data.append({'model': model, 'pk': pk, 'fields': fields})

    # Deserialize the flattened data
    for obj in PythonDeserializer(data, **options):
        yield obj