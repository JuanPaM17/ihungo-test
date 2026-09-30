from aiocache import caches
import functools
import logging

logger = logging.getLogger(__name__)


def cached(ttl=86400, cache_name="default"):
    """
    Decorator to add caching functionality to asynchronous functions.

    Args:
    ttl (int): Cache time to live in seconds.
    cache_name (str): Name of the cache to use.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache = caches.get(cache_name)
            cache_key = f"{func.__name__}_{'_'.join(map(str, args))}_{'_'.join(f'{k}={v}' for k, v in kwargs.items())}"
            try:
                # Try to retrieve the result from cache
                cached_result = await cache.get(cache_key)
                if cached_result is not None:
                    # logger.info(f"Cache hit for key: {cache_key}")
                    return cached_result
            except Exception as e:
                logger.error(f"Error retrieving cache for key {cache_key}: {e}")

            try:
                # Execute the function and cache the result
                # logger.info(f"Cache miss for key: {cache_key}, executing function.")
                result = await func(*args, **kwargs)
                try:
                    await cache.set(cache_key, result, ttl=ttl)
                except Exception as e:
                    logger.error(f"Error setting cache for key {cache_key}: {e}")
                return result
            except Exception as e:
                logger.error(f"Error executing function {func.__name__}: {e}")
                raise  # Re-raise the exception for the caller to handle

        async def invalidate(*args, **kwargs):
            cache = caches.get(cache_name)

            try:
                tenant = args[0] if len(args) > 0 else None
                version = args[1] if len(args) > 1 else None

                if tenant is None:
                    tenant = kwargs.get("tenant_id") or kwargs.get("tenant")

                if version is None:
                    version = (
                        kwargs.get("version") or kwargs.get("v") or kwargs.get("ver")
                    )

                if version and tenant:
                    all_keys = cache._cache
                    version_keys = [
                        key
                        for key in all_keys
                        if str(version) in key and str(tenant) in key
                    ]

                    for key in version_keys:
                        try:
                            await cache.delete(key)
                            logger.info(
                                f"Cache invalidated for version {version} key: {key}"
                            )

                        except Exception as e:
                            logger.error(f"Error invalidating cache for key {key}: {e}")
                            continue

            except Exception as e:
                logger.error(f"Error invalidating cache: {e}")

        wrapper.invalidate = invalidate
        return wrapper

    return decorator
