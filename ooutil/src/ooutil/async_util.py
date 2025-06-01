import asyncio


async def asyncio_wait_for_timeout(coro, timeout=5, default_val=None):
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        print(f'WARNING: {coro} timeout')

    return default_val
