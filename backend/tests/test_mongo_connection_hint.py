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


def test_mongo_connection_hint_for_atlas_timeout(monkeypatch) -> None:
    from app.core import config

    config.get_settings.cache_clear()
    monkeypatch.setenv(
        "MONGODB_URL",
        "mongodb+srv://user:secret@cluster0.eyfhgpd.mongodb.net/erp",
    )
    monkeypatch.setenv("MONGODB_DB_NAME", "erp")
    monkeypatch.setenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//")
    monkeypatch.setenv("JWT_SECRET", "dev-only-change-me")

    exc = ServerSelectionTimeoutError(
        "No replica set members found yet, Timeout: 5.0s, "
        "Topology Description: ReplicaSetNoPrimary"
    )
    hint = _mongo_connection_hint(exc)
    config.get_settings.cache_clear()
    assert hint is not None
    assert "MongoDB Atlas" in hint
    assert "secret" not in hint
    assert "127.0.0.1:27017/erp" in hint