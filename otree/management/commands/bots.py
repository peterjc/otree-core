import logging
from django.conf import settings, global_settings
from django.core.management.base import BaseCommand
from django.test.utils import (
    setup_databases,
    setup_test_environment,
    teardown_databases,
    teardown_test_environment,
)


from otree.bots.runner import run_all_bots_for_session_config

import otree.common

logger = logging.getLogger('otree')

from otree.constants import AUTO_NAME_BOTS_EXPORT_FOLDER

MSG_BOTS_HELP = 'Run oTree bots'


class Command(BaseCommand):
    help = MSG_BOTS_HELP

    def _get_action(self, parser, signature):
        option_strings = list(signature)
        for idx, action in enumerate(parser._actions):
            if action.option_strings == option_strings:
                return parser._actions[idx]

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument(
            'session_config_name',
            nargs='?',
            help='If omitted, all sessions in SESSION_CONFIGS are run',
        )

        parser.add_argument(
            'num_participants',
            type=int,
            nargs='?',
            help='Number of participants (if omitted, use num_demo_participants)',
        )

        # don't call it --data because then people might think that
        # that's the *input* data folder
        parser.add_argument(
            '--export',
            nargs='?',
            const=AUTO_NAME_BOTS_EXPORT_FOLDER,
            dest='export_path',
            help=(
                'Saves the data generated by the tests. '
                'Runs the "export data" command, '
                'outputting the CSV files to the specified directory, '
                'or an auto-generated one.'
            ),
        )
        parser.add_argument(
            '--save',
            nargs='?',
            const=AUTO_NAME_BOTS_EXPORT_FOLDER,
            dest='export_path',
            help=('Alias for --export.'),
        )

        v_action = self._get_action(parser, ("-v", "--verbosity"))
        v_action.default = '1'
        v_action.help = (
            'Verbosity level; 0=minimal output, 1=normal output,'
            '2=verbose output (DEFAULT), 3=very verbose output'
        )

    def prepare_global_state(self):
        '''
        separate function so it's easier to patch
        these are optimizations that are mostly redundant with what
        runtests.py does.
        '''

        # To make tests run faster, autorefresh should be set to True
        # http://whitenoise.evans.io/en/latest/django.html#whitenoise-makes-my-tests-run-slow
        settings.WHITENOISE_AUTOREFRESH = True

        # same hack as in resetdb code
        # because pytest.main() uses the serializer
        # it breaks if the app has migrations but they aren't up to date
        otree.common.patch_migrations_module()

        settings.STATICFILES_STORAGE = global_settings.STATICFILES_STORAGE

    def handle(
        self,
        *,
        verbosity,
        session_config_name,
        num_participants,
        export_path,
        **options
    ):
        self.prepare_global_state()

        setup_test_environment()
        old_config = setup_databases(
            interactive=False, verbosity=verbosity, aliases={'default'}
        )
        try:
            run_all_bots_for_session_config(
                session_config_name=session_config_name,
                num_participants=num_participants,
                export_path=export_path,
            )
        finally:
            teardown_databases(old_config, verbosity=verbosity)
            teardown_test_environment()
