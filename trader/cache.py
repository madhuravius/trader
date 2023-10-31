import hashlib
import json
import pickle
from datetime import datetime, timedelta
from threading import Thread
from time import sleep
from typing import Any, Dict, Optional

import httpx
from loguru import logger
from sqlmodel import Session, delete, select

from trader.dao.dao import DAO
from trader.dao.requests import CachedRequest
from trader.util.singleton import Singleton

DEFAULT_TIMEOUT_TO_PRUNE_EXPIRATIONS = 30
DEFAULT_CACHE_TIMEOUT = 60 * 60 * 24 * 3  # 3 days


class Cache(metaclass=Singleton):
    """
    This class is a utility to cache requests. This is because we are only allowed
    2 RPS per token. It's better to have long lived caches of things that don't change
    very often.
    """

    dao: DAO

    def __init__(self):
        self.dao = DAO()
        thread = Thread(target=self.run_loop)
        thread.setDaemon(True)
        thread.start()

    def generate_cached_request_id(
        self, method: str, url: str, serialized_data: str, params: str
    ) -> str:
        return hashlib.md5(
            bytes(f"{method}-{url}-{serialized_data}-{params}", "UTF-8")
        ).hexdigest()

    def get_kv_cache(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = {},
        params: Optional[Dict[str, Any]] = {},
    ) -> Optional[httpx.Response]:
        id = self.generate_cached_request_id(
            method=method,
            url=url,
            serialized_data=json.dumps(data, sort_keys=True),
            params=json.dumps(params, sort_keys=True),
        )
        logger.debug(
            f"Getting KV populated with value - {method}: {url} {params} ({id})"
        )
        try:
            with Session(self.dao.engine) as session:
                expression = select(CachedRequest).where(CachedRequest.id == id)
                results = session.exec(expression)
                cached_response = results.first()
                if not cached_response:
                    logger.debug(f"Cache miss - {method}: {url} ({id})")
                    return None

                logger.debug(f"Cache hit, returning value for - {method}: {url} ({id})")
                return pickle.loads(cached_response.response)
        except Exception as e:
            logger.exception(e)
            return None

    def set_kv_cache(
        self,
        method: str,
        url: str,
        response: httpx.Response,
        data: Optional[Dict[str, Any]] = {},
        params: Optional[Dict[str, Any]] = {},
        cache_timeout: float = DEFAULT_CACHE_TIMEOUT,
    ):
        id = self.generate_cached_request_id(
            method=method,
            url=url,
            serialized_data=json.dumps(data, sort_keys=True),
            params=json.dumps(params, sort_keys=True),
        )
        logger.debug(f"Setting KV populated with value - {method}: {url} ({id})")
        try:
            cached_request = CachedRequest(
                id=id,
                method=method,
                url=url,
                data=json.dumps(data, sort_keys=True),
                params=json.dumps(data, sort_keys=True),
                expiration=(datetime.now() + timedelta(cache_timeout)).timestamp(),
                response=pickle.dumps(response),
            )
            with Session(self.dao.engine) as session:
                session.add(cached_request)
                session.commit()
        except Exception as e:
            logger.exception(e)

    def expire_cache_records(self):
        with Session(self.dao.engine) as session:
            logger.debug("Pruning expired cache records")
            expression = delete(CachedRequest).where(
                CachedRequest.expiration <= datetime.now().timestamp()
            )
            session.exec(expression)  # type: ignore - This is done because sqlalchemy stubs are a bit off for deletes
            session.commit()

    def run_loop(self):
        while True:
            self.expire_cache_records()
            sleep(DEFAULT_TIMEOUT_TO_PRUNE_EXPIRATIONS)
