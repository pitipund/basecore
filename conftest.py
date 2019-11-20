from django_redis import get_redis_connection


def pytest_runtest_setup(item):
    redis = get_redis_connection('default')
    redis.flushdb()
