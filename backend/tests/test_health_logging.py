import pytest
import asyncio
from services.health_log_parser import HealthLogParser

@pytest.mark.asyncio
async def test_health_log_parser_standard():
    parser = HealthLogParser()
    result = await parser.parse("I weigh 150 lbs today")
    assert result["type"] == "measurement"
    assert "weight" in result["metric_type"].lower()
    assert result["value"] == 150
    assert "lb" in result["unit"].lower()

@pytest.mark.asyncio
async def test_health_log_parser_blood_pressure():
    parser = HealthLogParser()
    result = await parser.parse("My BP is 120 over 80")
    assert result["type"] == "measurement"
    assert "blood_pressure" in result["metric_type"].lower()
    assert result["value"] == 120
    assert result["secondary_value"] == 80

@pytest.mark.asyncio
async def test_health_log_parser_sleep():
    parser = HealthLogParser()
    result = await parser.parse("I slept for 7.5 hours last night")
    assert result["type"] == "lifestyle"
    assert result["category"] == "sleep"
    assert "7.5" in result["summary"]

@pytest.mark.asyncio
async def test_health_log_parser_fake_units():
    parser = HealthLogParser()
    result = await parser.parse("My weight is 150 florgs")
    # The parser might still extract it, but it should either map unit to unknown or keep florgs.
    # The Pydantic model at runtime would fail validation if we strict checked it, but currently we just accept string units.
    assert result["type"] == "measurement"
    assert result["value"] == 150
    assert result["unit"] != ""

@pytest.mark.asyncio
async def test_health_log_parser_impossible_values():
    parser = HealthLogParser()
    result = await parser.parse("My heart rate is -50 bpm")
    # LLM should extract it
    assert result["type"] == "measurement"
    assert result["value"] == -50
    # The Pydantic validation (check_value_bounds) inside api/health.py will catch this.
