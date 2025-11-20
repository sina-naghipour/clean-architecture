import schemathesis
import pytest

schema = schemathesis.from_file("openapi.yaml")

@schema.parametrize()
def test_api(case):
    response = case.call()
    case.validate_response(response)
