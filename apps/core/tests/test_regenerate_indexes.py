import logging

from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from apps.core import es_index

logger = logging.getLogger('fun_cms.core.regenerate_indexes')


class RegenerateIndexesTestCase(TestCase):
    """
    Test the command that regenerates the Elasticsearch indexes.
    """
    @mock.patch.object(es_index, 'regenerate_indexes')
    @mock.patch.object(logger, 'info')
    def test_regenerate_indexes(self, *args):
        """
        Delegate all logic to the es_index module, log time elapsed at the end
        """
        call_command('regenerate_indexes')
        es_index.regenerate_indexes.assert_called()
        self.assertEqual(logger.info.call_count, 2)
