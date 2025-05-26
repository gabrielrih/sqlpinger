from unittest import TestCase


from sqlpinger.core.ping import SqlAvailabilityMonitor


class TestSqlAvailabilityMonitor(TestCase):
    def test_start_monitoring(self):
        pass

    def test_run_check_when_not_connection(self):
        pass

    def test_run_check_when_connection_already_exists(self):
        pass

    def test_connect(self):
        pass

    def test_is_downtime_when_it_is(self):
        pass

    def test_is_downtime_when_it_is_not(self):
        pass

    def test_recovery_from_downtime(self):
        pass

    def test_handle_exception_when_it_is_downtime(self):
        pass

    def test_handle_exception_when_it_is_not_downtime(self):
        pass

    def test_disconnect_when_the_connection_exists(self):
        pass

    def test_disconnect_when_the_connection_doesnt_exist(self):
        pass
