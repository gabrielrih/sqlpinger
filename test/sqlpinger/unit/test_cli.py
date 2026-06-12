from unittest import TestCase
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from sqlpinger.cli import cli


class TestCliHelp(TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_root_help_lists_both_subcommands(self):
        result = self.runner.invoke(cli, ['--help'])
        self.assertEqual(result.exit_code, 0)
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
