import keyring
from keyring.errors import KeyringError, PasswordDeleteError
from dataclasses import dataclass


SUPPORTED_CREDENTIAL_ENGINES = ("mssql", "pg")
SERVICE_NAME_PREFIX = "sqlpinger"
DEFAULT_USERNAME_ACCOUNT = "__default_username__"


@dataclass(frozen=True)
class DefaultCredentials:
    username: str
    password: str


class CredentialStoreError(RuntimeError):
    """Raised when default credentials cannot be read or written."""


class DefaultCredentialStore:
    def __init__(self, keyring_backend=None):
        self.keyring = keyring_backend or keyring

    def set_default(self, engine: str, username: str, password: str) -> None:
        if not username:
            raise CredentialStoreError("Default credentials require a username")
        if not password:
            raise CredentialStoreError("Default credentials require a password")

        service_name = self._service_name(engine)
        old_username = self._get_password(service_name, DEFAULT_USERNAME_ACCOUNT)

        self._set_password(service_name, username, password)
        self._set_password(service_name, DEFAULT_USERNAME_ACCOUNT, username)

        if old_username and old_username != username:
            self._delete_password(service_name, old_username, ignore_missing=True)

    def get_default(self, engine: str) -> DefaultCredentials | None:
        service_name = self._service_name(engine)
        username = self._get_password(service_name, DEFAULT_USERNAME_ACCOUNT)
        if not username:
            return None

        password = self._get_password(service_name, username)
        if not password:
            return None

        return DefaultCredentials(username=username, password=password)

    def clear_default(self, engine: str) -> bool:
        service_name = self._service_name(engine)
        username = self._get_password(service_name, DEFAULT_USERNAME_ACCOUNT)

        removed = False
        if username:
            removed = self._delete_password(service_name, username, ignore_missing=True) or removed
        removed = self._delete_password(service_name, DEFAULT_USERNAME_ACCOUNT, ignore_missing=True) or removed
        return removed

    def _service_name(self, engine: str) -> str:
        if engine not in SUPPORTED_CREDENTIAL_ENGINES:
            engines = ", ".join(SUPPORTED_CREDENTIAL_ENGINES)
            raise CredentialStoreError(f"Unsupported credentials engine '{engine}'. Expected one of: {engines}")
        return f"{SERVICE_NAME_PREFIX}:{engine}"

    def _get_password(self, service_name: str, username: str) -> str | None:
        try:
            return self.keyring.get_password(service_name, username)
        except KeyringError as exc:
            raise CredentialStoreError(self._backend_error_message(exc)) from exc

    def _set_password(self, service_name: str, username: str, password: str) -> None:
        try:
            self.keyring.set_password(service_name, username, password)
        except KeyringError as exc:
            raise CredentialStoreError(self._backend_error_message(exc)) from exc

    def _delete_password(self, service_name: str, username: str, ignore_missing: bool) -> bool:
        try:
            self.keyring.delete_password(service_name, username)
            return True
        except PasswordDeleteError:
            if ignore_missing:
                return False
            raise
        except KeyringError as exc:
            raise CredentialStoreError(self._backend_error_message(exc)) from exc

    def _backend_error_message(self, exc: KeyringError) -> str:
        return (
            "Secure credential storage is unavailable. "
            "Install or enable an operating-system keyring backend and try again. "
            f"Details: {exc}"
        )
