import asyncio
import json

import pytest

from app.api.v1.copilot import _sse_stream


async def _mock_agent_streaming(events: list[str]):
    """Yield a list of SSE event strings as an async generator."""
    for event in events:
        yield event


@pytest.mark.asyncio
async def test_sse_stream_yields_all_events():
    events = [
        f"data: {json.dumps({'type': 'tool_call', 'tool': 'test'})}\n\n",
        f"data: {json.dumps({'type': 'response', 'content': 'hello'})}\n\n",
        f"data: {json.dumps({'type': 'done'})}\n\n",
    ]
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.api.v1.copilot._TIMEOUT_SECONDS", 30)
        mp.setattr("app.api.v1.copilot._HEARTBEAT_INTERVAL", 9999)
        mp.setattr(
            "app.api.v1.copilot.run_agent_streaming",
            lambda msg, tid: _mock_agent_streaming(events),
        )
        collected = [chunk async for chunk in _sse_stream("hi", "t1")]

    data_events = [e for e in collected if e.startswith("data:")]
    assert len(data_events) == 3


@pytest.mark.asyncio
async def test_sse_timeout_returns_partial_status():
    async def _slow_stream(msg, tid):
        yield f"data: {json.dumps({'type': 'thinking', 'content': 'partial...'})}\n\n"
        await asyncio.sleep(35)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.api.v1.copilot._TIMEOUT_SECONDS", 2)
        mp.setattr("app.api.v1.copilot._HEARTBEAT_INTERVAL", 9999)
        mp.setattr("app.api.v1.copilot.run_agent_streaming", _slow_stream)
        collected = [chunk async for chunk in _sse_stream("hi", "t1")]

    partial_events = [
        e for e in collected
        if "status" in e and "timeout" in e
    ]
    assert len(partial_events) >= 1
    parsed = json.loads(partial_events[0].split("data: ", 1)[1])
    assert parsed["status"] == "timeout"


@pytest.mark.asyncio
async def test_sse_error_recovery_mid_stream():
    async def _failing_stream(msg, tid):
        yield f"data: {json.dumps({'type': 'tool_call', 'tool': 'x'})}\n\n"
        raise RuntimeError("Anthropic API error after partial response")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.api.v1.copilot._TIMEOUT_SECONDS", 30)
        mp.setattr("app.api.v1.copilot._HEARTBEAT_INTERVAL", 9999)
        mp.setattr("app.api.v1.copilot.run_agent_streaming", _failing_stream)
        collected = [chunk async for chunk in _sse_stream("hi", "t1")]

    error_events = [e for e in collected if e.startswith("event: error")]
    assert len(error_events) == 1
    error_data = json.loads(error_events[0].split("data: ", 1)[1])
    assert "Anthropic API error" in error_data["error"]


@pytest.mark.asyncio
async def test_sse_heartbeat_ping():
    async def _slow_first_then_done(msg, tid):
        await asyncio.sleep(0.3)
        yield f"data: {json.dumps({'type': 'response', 'content': 'hi'})}\n\n"

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.api.v1.copilot._TIMEOUT_SECONDS", 30)
        mp.setattr("app.api.v1.copilot._HEARTBEAT_INTERVAL", 0.1)
        mp.setattr("app.api.v1.copilot.run_agent_streaming", _slow_first_then_done)
        collected = [chunk async for chunk in _sse_stream("hi", "t1")]

    ping_events = [e for e in collected if e.startswith("event: ping")]
    assert len(ping_events) >= 1


@pytest.mark.asyncio
async def test_sse_backpressure_drops_oldest():
    async def _burst_producer(msg, tid):
        for i in range(30):
            yield f"data: {json.dumps({'type': 'chunk', 'i': i})}\n\n"

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.api.v1.copilot._MAX_BUFFER_SIZE", 3)
        mp.setattr("app.api.v1.copilot._TIMEOUT_SECONDS", 30)
        mp.setattr("app.api.v1.copilot._HEARTBEAT_INTERVAL", 9999)
        mp.setattr("app.api.v1.copilot.run_agent_streaming", _burst_producer)

        gen = _sse_stream("hi", "t1")
        collected = []
        read_count = 0
        async for chunk in gen:
            collected.append(chunk)
            read_count += 1
            await asyncio.sleep(0.05)

    dropped_events = [e for e in collected if e.startswith("event: dropped")]
    assert len(dropped_events) >= 1


@pytest.mark.asyncio
async def test_sse_client_disconnect_cleanup():
    cancelled = False

    async def _long_stream(msg, tid):
        nonlocal cancelled
        try:
            yield f"data: {json.dumps({'type': 'thinking'})}\n\n"
            await asyncio.sleep(60)
            yield f"data: {json.dumps({'type': 'response', 'content': 'never'})}\n\n"
        except asyncio.CancelledError:
            cancelled = True
            raise

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.api.v1.copilot._TIMEOUT_SECONDS", 30)
        mp.setattr("app.api.v1.copilot._HEARTBEAT_INTERVAL", 9999)
        mp.setattr("app.api.v1.copilot.run_agent_streaming", _long_stream)

        gen = _sse_stream("hi", "t1")
        first = await gen.__anext__()
        assert "thinking" in first
        await gen.aclose()

    assert cancelled is True


@pytest.mark.asyncio
async def test_sse_stream_completes_before_timeout():
    async def _fast_stream(msg, tid):
        for i in range(5):
            yield f"data: {json.dumps({'type': 'chunk', 'i': i})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("app.api.v1.copilot._TIMEOUT_SECONDS", 30)
        mp.setattr("app.api.v1.copilot._HEARTBEAT_INTERVAL", 9999)
        mp.setattr("app.api.v1.copilot.run_agent_streaming", _fast_stream)
        collected = [chunk async for chunk in _sse_stream("hi", "t1")]

    data_events = [e for e in collected if e.startswith("data:")]
    assert len(data_events) == 6

    timeout_events = [
        e for e in collected
        if "status" in e and "timeout" in e
    ]
    assert len(timeout_events) == 0