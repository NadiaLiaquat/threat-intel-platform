from tip_backend.models import Indicator
from tip_backend.processing import dedupe, score


def test_dedupe_merges_sources_and_keeps_widest_time_range():
    a = Indicator(indicator="1.2.3.4", type="ip", first_seen="2026-01-02T00:00:00Z", last_seen="2026-01-02T00:00:00Z", sources=["feodotracker"])
    b = Indicator(indicator="1.2.3.4", type="ip", first_seen="2026-01-01T00:00:00Z", last_seen="2026-01-05T00:00:00Z", sources=["threatfox"], malware_family="Emotet")

    [merged] = dedupe([a, b])
    assert set(merged.sources) == {"feodotracker", "threatfox"}
    assert merged.first_seen == "2026-01-01T00:00:00Z"
    assert merged.last_seen == "2026-01-05T00:00:00Z"
    assert merged.malware_family == "Emotet"


def test_dedupe_keeps_different_types_separate():
    domain = Indicator(indicator="x.com", type="domain", first_seen="t", last_seen="t")
    url = Indicator(indicator="x.com", type="url", first_seen="t", last_seen="t")
    assert len(dedupe([domain, url])) == 2


def test_score_rewards_multi_source_corroboration():
    single = Indicator(indicator="a", type="domain", first_seen="t", last_seen="t", sources=["urlhaus"])
    corroborated = Indicator(indicator="b", type="domain", first_seen="t", last_seen="t", sources=["urlhaus", "threatfox"])
    score([single, corroborated])
    assert corroborated.confidence > single.confidence


def test_score_severity_reflects_threat_type():
    c2 = Indicator(indicator="a", type="ip", first_seen="t", last_seen="t", threat_type="c2")
    unknown = Indicator(indicator="b", type="ip", first_seen="t", last_seen="t")
    score([c2, unknown])
    assert c2.severity > unknown.severity
