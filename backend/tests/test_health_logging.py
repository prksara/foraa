import pytest
from services.health_log_parser import HealthLogParser

def test_health_log_parser_standard():
    parser = HealthLogParser()
    result = parser.parse("I weigh 150 lbs today")
    assert result is not None
    assert result.get("category") == "measurement"
    assert "weight" in (result.get("metric_type") or result.get("type", "")).lower()
    assert result.get("value") == 150
    assert "lb" in result.get("unit", "").lower()

def test_health_log_parser_blood_pressure():
    parser = HealthLogParser()
    result = parser.parse("My BP is 120 over 80")
    assert result is not None
    assert result.get("category") == "measurement"
    assert "blood_pressure" in (result.get("metric_type") or result.get("type", "")).lower()
    assert result.get("value") == 120
    assert result.get("secondary_value") == 80

def test_health_log_parser_sleep():
    parser = HealthLogParser()
    result = parser.parse("I slept for 7.5 hours last night")
    assert result is not None
    assert result.get("category") == "lifestyle"
    assert (result.get("metric_type") or result.get("type", "")).lower() == "sleep"
    assert result.get("value") == 7.5

def test_health_log_parser_fake_units():
    parser = HealthLogParser()
    result = parser.parse("My weight is 150 florgs")
    assert result is not None
    assert result.get("category") == "measurement"
    assert result.get("value") == 150
    assert result.get("unit") != ""

def test_health_log_parser_impossible_values():
    parser = HealthLogParser()
    result = parser.parse("My heart rate is -50 bpm")
    assert result is not None
    assert result.get("category") == "measurement"
    assert result.get("value") == -50
