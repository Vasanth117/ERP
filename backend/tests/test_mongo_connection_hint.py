from pymongo.errors import ServerSelectionTimeoutError

from app.core.database import _mongo_connection_hint


def test_mongo_connection_hint_for_standalone_vs_replicaset_url() -> None:
    exc = ServerSelectionTimeoutError(
        'client is configured to connect to a replica set named "rs0" '
        "but this node belongs to a set named 'None'"
    )
    hint = _mongo_connection_hint(exc)
    assert hint is not None
    assert "MONGODB_URL=mongodb://127.0.0.1:27017/erp" in hint


def test_mongo_connection_hint_absent_for_other_errors() -> None:
    assert _mongo_connection_hint(ConnectionError("refused")) is None