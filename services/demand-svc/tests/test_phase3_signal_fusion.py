import pytest

from app.core.signal_fusion import DemandSignalFusion


@pytest.mark.asyncio
async def test_signal_fusion_weights():
    fusion = DemandSignalFusion()
    result = await fusion.fuse_signals(
        None,
        "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
        "FG-DT100",
        28,
        {
            "statistical_qty": 20,
            "statistical_confidence": 0.8,
            "open_orders_qty": 10,
            "crm_pipeline_qty": 8,
            "customer_pattern_qty": 5,
            "seasonal_factor": 0.9,
            "seasonal_description": "Eid period",
        },
    )
    assert result["fused_qty"] > 0
    assert result["confidence_label"] in ("high", "medium", "low")
    assert len(result["signals"]) >= 2
    assert "Fused from" in result["explanation"]
