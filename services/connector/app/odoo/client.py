import xmlrpc.client
from typing import Any


class OdooClient:
    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url.rstrip("/")
        self.db = db
        self.username = username
        self.password = password
        self._uid: int | None = None
        self._common: Any = None
        self._models: Any = None

    def _get_common(self):
        if self._common is None:
            self._common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        return self._common

    def _get_models(self):
        if self._models is None:
            self._models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
        return self._models

    def authenticate(self) -> int:
        common = self._get_common()
        self._uid = common.authenticate(self.db, self.username, self.password, {})
        if not self._uid:
            raise ConnectionError(f"Odoo authentication failed for {self.username}")
        return self._uid

    @property
    def uid(self) -> int:
        if self._uid is None:
            self.authenticate()
        return self._uid  # type: ignore

    def search_read(
        self, model: str, domain: list | None = None, fields: list[str] | None = None, limit: int | None = None
    ) -> list[dict]:
        models = self._get_models()
        kwargs: dict[str, Any] = {}
        if fields:
            kwargs["fields"] = fields
        if limit:
            kwargs["limit"] = limit
        return models.execute_kw(self.db, self.uid, self.password, model, "search_read", [domain or []], kwargs)

    def read(self, model: str, ids: list[int], fields: list[str] | None = None) -> list[dict]:
        models = self._get_models()
        kwargs: dict[str, Any] = {}
        if fields:
            kwargs["fields"] = fields
        return models.execute_kw(self.db, self.uid, self.password, model, "read", [ids], kwargs)
