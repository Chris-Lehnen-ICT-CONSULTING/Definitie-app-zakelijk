def test_bwb_sru_endpoint_has_x_connection_and_version():
    from services.web_lookup.sru_service import SRUService

    svc = SRUService()
    cfg = svc.endpoints.get("wetgeving_nl")
    assert cfg is not None
    assert cfg.base_url.startswith("https://zoekservice.overheid.nl/sru/Search")
    assert cfg.sru_version.startswith("2")
    assert cfg.extra_params.get("x-connection") == "BWB"

