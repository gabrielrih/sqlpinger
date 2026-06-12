from unittest import TestCase
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from sqlpinger.cli import cli
from sqlpinger.core.credentials import DefaultCredentials


class TestCliHelp(TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_root_help_lists_both_subcommands(self):
        result = self.runner.invoke(cli, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('credentials', result.output)
        self.assertIn('mssql', result.output)
        self.assertIn('pg', result.output)

    def test_mssql_help_includes_driver_excludes_port(self):
        result = self.runner.invoke(cli, ['mssql', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('--driver', result.output)
        self.assertIn('--once', result.output)
        self.assertNotIn('--port', result.output)
        self.assertNotIn('--sslmode', result.output)

    def test_pg_help_includes_port_and_sslmode_excludes_driver(self):
        result = self.runner.invoke(cli, ['pg', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('--port', result.output)
        self.assertIn('--sslmode', result.output)
        self.assertIn('--once', result.output)
        self.assertNotIn('--driver', result.output)


class TestCliValidation(TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_pg_rejects_windows_auth(self):
        result = self.runner.invoke(cli, [
            'pg',
            '--server', 'host',
            '--database', 'db',
            '--auth', 'windows',
            '--username', 'u',
            '--password', 'p',
        ])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("'windows'", result.output)

    def test_pg_rejects_unknown_driver_option(self):
        result = self.runner.invoke(cli, [
            'pg',
            '--server', 'host',
            '--database', 'db',
            '--driver', 'foo',
            '--username', 'u',
            '--password', 'p',
        ])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('no such option', result.output.lower())

    def test_mssql_rejects_unknown_port_option(self):
        result = self.runner.invoke(cli, [
            'mssql',
            '--server', 'host',
            '--database', 'db',
            '--port', '5432',
            '--username', 'u',
            '--password', 'p',
        ])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('no such option', result.output.lower())


class TestCredentialsCommands(TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch('sqlpinger.credentials_cli.DefaultCredentialStore')
    def test_credentials_set_saves_default_credentials(self, mock_store_cls):
        mock_store = MagicMock()
        mock_store_cls.return_value = mock_store

        result = self.runner.invoke(cli, [
            'credentials',
            'set',
            '--engine', 'mssql',
            '--username', 'default_user',
        ], input='secret\n')

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_store.set_default.assert_called_once_with('mssql', 'default_user', 'secret')
        self.assertIn('Default credentials configured for mssql user "default_user".', result.output)
        self.assertNotIn('secret', result.output)

    @patch('sqlpinger.credentials_cli.DefaultCredentialStore')
    def test_credentials_status_shows_configured_engine_without_password(self, mock_store_cls):
        mock_store = MagicMock()
        mock_store.get_default.return_value = DefaultCredentials(username='default_user', password='secret')
        mock_store_cls.return_value = mock_store

        result = self.runner.invoke(cli, [
            'credentials',
            'status',
            '--engine', 'pg',
        ])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_store.get_default.assert_called_once_with('pg')
        self.assertIn('pg: configured for user "default_user"', result.output)
        self.assertNotIn('secret', result.output)

    @patch('sqlpinger.credentials_cli.DefaultCredentialStore')
    def test_credentials_status_shows_missing_defaults(self, mock_store_cls):
        mock_store = MagicMock()
        mock_store.get_default.return_value = None
        mock_store_cls.return_value = mock_store

        result = self.runner.invoke(cli, [
            'credentials',
            'status',
            '--engine', 'mssql',
        ])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn('mssql: not configured', result.output)

    @patch('sqlpinger.credentials_cli.DefaultCredentialStore')
    def test_credentials_clear_removes_default_credentials(self, mock_store_cls):
        mock_store = MagicMock()
        mock_store.clear_default.return_value = True
        mock_store_cls.return_value = mock_store

        result = self.runner.invoke(cli, [
            'credentials',
            'clear',
            '--engine', 'pg',
        ])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_store.clear_default.assert_called_once_with('pg')
        self.assertIn('Default credentials cleared for pg.', result.output)


class TestCliWiring(TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch('sqlpinger.cli.AvailabilityMonitor')
    @patch('sqlpinger.cli.SqlServerEngine')
    @patch('sqlpinger.cli.SqlServerAuthStrategyFactory')
    def test_mssql_wires_sqlserver_components(self, mock_factory, mock_engine_cls, mock_monitor_cls):
        mock_auth_strategy = MagicMock()
        mock_factory.create.return_value = mock_auth_strategy
        mock_engine = MagicMock()
        mock_engine_cls.return_value = mock_engine
        mock_monitor = MagicMock()
        mock_monitor_cls.return_value = mock_monitor

        result = self.runner.invoke(cli, [
            'mssql',
            '--server', 'host',
            '--database', 'db',
            '--auth', 'sql',
            '--username', 'u',
            '--password', 'p',
            '--interval', '7',
            '--driver', 'My ODBC Driver',
        ])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_factory.create.assert_called_once_with(
            auth='sql',
            driver='My ODBC Driver',
            timeout_in_seconds=7,
            username='u',
            password='p',
        )
        mock_engine_cls.assert_called_once_with()
        mock_monitor_cls.assert_called_once_with('host', 'db', 7, mock_auth_strategy, mock_engine)
        mock_monitor.start_monitoring.assert_called_once_with()
        mock_monitor.run_once.assert_not_called()

    @patch('sqlpinger.cli.AvailabilityMonitor')
    @patch('sqlpinger.cli.PostgresEngine')
    @patch('sqlpinger.cli.PostgresAuthStrategyFactory')
    def test_pg_wires_postgres_components(self, mock_factory, mock_engine_cls, mock_monitor_cls):
        mock_auth_strategy = MagicMock()
        mock_factory.create.return_value = mock_auth_strategy
        mock_engine = MagicMock()
        mock_engine_cls.return_value = mock_engine
        mock_monitor = MagicMock()
        mock_monitor_cls.return_value = mock_monitor

        result = self.runner.invoke(cli, [
            'pg',
            '--server', 'pghost',
            '--database', 'pgdb',
            '--auth', 'sql',
            '--username', 'u',
            '--password', 'p',
            '--interval', '4',
            '--port', '6543',
            '--sslmode', 'verify-full',
        ])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_factory.create.assert_called_once_with(
            auth='sql',
            timeout_in_seconds=4,
            username='u',
            password='p',
            port=6543,
            sslmode='verify-full',
        )
        mock_engine_cls.assert_called_once_with()
        mock_monitor_cls.assert_called_once_with('pghost', 'pgdb', 4, mock_auth_strategy, mock_engine)
        mock_monitor.start_monitoring.assert_called_once_with()
        mock_monitor.run_once.assert_not_called()

    def test_mssql_uses_default_credentials_when_username_is_missing(self):
        with patch('sqlpinger.credentials_cli.DefaultCredentialStore') as mock_store_cls, \
             patch('sqlpinger.credentials_cli.Logger') as mock_logger_cls, \
             patch('sqlpinger.cli.SqlServerAuthStrategyFactory') as mock_factory, \
             patch('sqlpinger.cli.SqlServerEngine') as mock_engine_cls, \
             patch('sqlpinger.cli.AvailabilityMonitor') as mock_monitor_cls:
            mock_store = MagicMock()
            mock_store.get_default.return_value = DefaultCredentials(username='default_user', password='secret')
            mock_store_cls.return_value = mock_store
            mock_logger = MagicMock()
            mock_logger_cls.get_logger.return_value = mock_logger
            mock_auth_strategy = MagicMock()
            mock_factory.create.return_value = mock_auth_strategy
            mock_engine = MagicMock()
            mock_engine_cls.return_value = mock_engine
            mock_monitor = MagicMock()
            mock_monitor_cls.return_value = mock_monitor

            result = self.runner.invoke(cli, [
                'mssql',
                '--server', 'host',
                '--database', 'db',
                '--auth', 'sql',
            ])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_store.get_default.assert_called_once_with('mssql')
        mock_logger.info.assert_called_once_with(
            'Using saved default credentials for mssql with user "default_user".'
        )
        mock_factory.create.assert_called_once_with(
            auth='sql',
            driver='ODBC Driver 18 for SQL Server',
            timeout_in_seconds=5,
            username='default_user',
            password='secret',
        )
        mock_monitor.start_monitoring.assert_called_once_with()

    def test_pg_uses_default_credentials_when_username_is_missing(self):
        with patch('sqlpinger.credentials_cli.DefaultCredentialStore') as mock_store_cls, \
             patch('sqlpinger.credentials_cli.Logger') as mock_logger_cls, \
             patch('sqlpinger.cli.PostgresAuthStrategyFactory') as mock_factory, \
             patch('sqlpinger.cli.PostgresEngine') as mock_engine_cls, \
             patch('sqlpinger.cli.AvailabilityMonitor') as mock_monitor_cls:
            mock_store = MagicMock()
            mock_store.get_default.return_value = DefaultCredentials(username='pg_user', password='pg_secret')
            mock_store_cls.return_value = mock_store
            mock_logger = MagicMock()
            mock_logger_cls.get_logger.return_value = mock_logger
            mock_auth_strategy = MagicMock()
            mock_factory.create.return_value = mock_auth_strategy
            mock_engine = MagicMock()
            mock_engine_cls.return_value = mock_engine
            mock_monitor = MagicMock()
            mock_monitor_cls.return_value = mock_monitor

            result = self.runner.invoke(cli, [
                'pg',
                '--server', 'pghost',
                '--database', 'pgdb',
                '--auth', 'sql',
            ])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_store.get_default.assert_called_once_with('pg')
        mock_logger.info.assert_called_once_with(
            'Using saved default credentials for pg with user "pg_user".'
        )
        mock_factory.create.assert_called_once_with(
            auth='sql',
            timeout_in_seconds=5,
            username='pg_user',
            password='pg_secret',
            port=5432,
            sslmode='require',
        )
        mock_monitor.start_monitoring.assert_called_once_with()

    def test_explicit_username_prompts_for_password_without_default_credentials(self):
        with patch('sqlpinger.credentials_cli.DefaultCredentialStore') as mock_store_cls, \
             patch('sqlpinger.cli.PostgresAuthStrategyFactory') as mock_factory, \
             patch('sqlpinger.cli.PostgresEngine') as mock_engine_cls, \
             patch('sqlpinger.cli.AvailabilityMonitor') as mock_monitor_cls:
            mock_auth_strategy = MagicMock()
            mock_factory.create.return_value = mock_auth_strategy
            mock_engine = MagicMock()
            mock_engine_cls.return_value = mock_engine
            mock_monitor = MagicMock()
            mock_monitor_cls.return_value = mock_monitor

            result = self.runner.invoke(cli, [
                'pg',
                '--server', 'pghost',
                '--database', 'pgdb',
                '--auth', 'sql',
                '--username', 'explicit_user',
            ], input='typed_secret\n')

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_store_cls.assert_not_called()
        mock_factory.create.assert_called_once_with(
            auth='sql',
            timeout_in_seconds=5,
            username='explicit_user',
            password='typed_secret',
            port=5432,
            sslmode='require',
        )

    def test_sql_auth_without_username_fails_when_default_credentials_are_missing(self):
        with patch('sqlpinger.credentials_cli.DefaultCredentialStore') as mock_store_cls, \
             patch('sqlpinger.cli.SqlServerAuthStrategyFactory') as mock_factory:
            mock_store = MagicMock()
            mock_store.get_default.return_value = None
            mock_store_cls.return_value = mock_store

            result = self.runner.invoke(cli, [
                'mssql',
                '--server', 'host',
                '--database', 'db',
                '--auth', 'sql',
            ])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('sqlpinger credentials set --engine mssql --username <user>', result.output)
        mock_factory.create.assert_not_called()

    def test_password_without_username_fails_before_auth_factory(self):
        with patch('sqlpinger.credentials_cli.DefaultCredentialStore') as mock_store_cls, \
             patch('sqlpinger.cli.PostgresAuthStrategyFactory') as mock_factory:
            result = self.runner.invoke(cli, [
                'pg',
                '--server', 'pghost',
                '--database', 'pgdb',
                '--auth', 'sql',
                '--password', 'secret',
            ])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('The --password option requires --username', result.output)
        mock_store_cls.assert_not_called()
        mock_factory.create.assert_not_called()

    @patch('sqlpinger.cli.AvailabilityMonitor')
    @patch('sqlpinger.cli.SqlServerEngine')
    @patch('sqlpinger.cli.SqlServerAuthStrategyFactory')
    def test_mssql_once_runs_one_healthcheck_and_exits_successfully(
        self,
        mock_factory,
        mock_engine_cls,
        mock_monitor_cls,
    ):
        mock_auth_strategy = MagicMock()
        mock_factory.create.return_value = mock_auth_strategy
        mock_engine = MagicMock()
        mock_engine_cls.return_value = mock_engine
        mock_monitor = MagicMock()
        mock_monitor.run_once.return_value = True
        mock_monitor_cls.return_value = mock_monitor

        result = self.runner.invoke(cli, [
            'mssql',
            '--server', 'host',
            '--database', 'db',
            '--auth', 'sql',
            '--username', 'u',
            '--password', 'p',
            '--interval', '99',
            '--once',
        ])

        self.assertEqual(result.exit_code, 0, msg=result.output)
        mock_factory.create.assert_called_once_with(
            auth='sql',
            driver='ODBC Driver 18 for SQL Server',
            timeout_in_seconds=5,
            username='u',
            password='p',
        )
        mock_monitor_cls.assert_called_once_with('host', 'db', 5, mock_auth_strategy, mock_engine)
        mock_monitor.run_once.assert_called_once_with()
        mock_monitor.start_monitoring.assert_not_called()

    @patch('sqlpinger.cli.AvailabilityMonitor')
    @patch('sqlpinger.cli.PostgresEngine')
    @patch('sqlpinger.cli.PostgresAuthStrategyFactory')
    def test_pg_once_runs_one_healthcheck_and_exits_with_error_on_failure(
        self,
        mock_factory,
        mock_engine_cls,
        mock_monitor_cls,
    ):
        mock_auth_strategy = MagicMock()
        mock_factory.create.return_value = mock_auth_strategy
        mock_engine = MagicMock()
        mock_engine_cls.return_value = mock_engine
        mock_monitor = MagicMock()
        mock_monitor.run_once.return_value = False
        mock_monitor_cls.return_value = mock_monitor

        result = self.runner.invoke(cli, [
            'pg',
            '--server', 'pghost',
            '--database', 'pgdb',
            '--auth', 'sql',
            '--username', 'u',
            '--password', 'p',
            '--interval', '99',
            '--once',
        ])

        self.assertEqual(result.exit_code, 1, msg=result.output)
        self.assertIsInstance(result.exception, SystemExit)
        self.assertNotIsInstance(result.exception, AttributeError)
        self.assertNotIn('traceback', result.output.lower())
        mock_factory.create.assert_called_once_with(
            auth='sql',
            timeout_in_seconds=5,
            username='u',
            password='p',
            port=5432,
            sslmode='require',
        )
        mock_monitor_cls.assert_called_once_with('pghost', 'pgdb', 5, mock_auth_strategy, mock_engine)
        mock_monitor.run_once.assert_called_once_with()
        mock_monitor.start_monitoring.assert_not_called()
