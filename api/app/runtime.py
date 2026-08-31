import asyncio


def create_selector_event_loop() -> asyncio.AbstractEventLoop:
    return asyncio.SelectorEventLoop()
