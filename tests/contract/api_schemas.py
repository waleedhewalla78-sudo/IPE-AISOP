"""Schemathesis fuzz testing configuration for IPE platform API endpoints.

Usage:
    schemathesis run --base-url=http://localhost:8020 api_schemas.py

Or per-service:
    schemathesis run --base-url=http://localhost:8020 -a dpe api_schemas.py
    schemathesis run --base-url=http://localhost:8002 -a mat api_schemas.py
    schemathesis run --base-url=http://localhost:8003 -a cap api_schemas.py
"""

import schemathesis
from hypothesis import settings

dpe_schema = schemathesis.from_path("services/dpe-svc/openapi.json")
mat_schema = schemathesis.from_path("services/mat-svc/openapi.json")
cap_schema = schemathesis.from_path("services/cap-svc/openapi.json")
fea_schema = schemathesis.from_path("services/fea-svc/openapi.json")
res_schema = schemathesis.from_path("services/res-svc/openapi.json")
del_schema = schemathesis.from_path("services/del-svc/openapi.json")
nlp_schema = schemathesis.from_path("services/nlp-svc/openapi.json")
rec_schema = schemathesis.from_path("services/rec-svc/openapi.json")
sustain_schema = schemathesis.from_path("services/sustain-svc/openapi.json")
quality_schema = schemathesis.from_path("services/quality-svc/openapi.json")
scn_schema = schemathesis.from_path("services/scn-svc/openapi.json")
network_schema = schemathesis.from_path("services/network-svc/openapi.json")


@settings(max_examples=50)
@dpe_schema.parametrize()
def test_dpe_api(case):
    case.call_and_validate()


@settings(max_examples=50)
@mat_schema.parametrize()
def test_mat_api(case):
    case.call_and_validate()


@settings(max_examples=50)
@cap_schema.parametrize()
def test_cap_api(case):
    case.call_and_validate()


@settings(max_examples=50)
@fea_schema.parametrize()
def test_fea_api(case):
    case.call_and_validate()


@settings(max_examples=50)
@res_schema.parametrize()
def test_res_api(case):
    case.call_and_validate()


@settings(max_examples=50)
@del_schema.parametrize()
def test_del_api(case):
    case.call_and_validate()


@settings(max_examples=50)
@sustain_schema.parametrize()
def test_sustain_api(case):
    case.call_and_validate()


@settings(max_examples=50)
@quality_schema.parametrize()
def test_quality_api(case):
    case.call_and_validate()


@settings(max_examples=50)
@scn_schema.parametrize()
def test_scn_api(case):
    case.call_and_validate()


@settings(max_examples=50)
@network_schema.parametrize()
def test_network_api(case):
    case.call_and_validate()