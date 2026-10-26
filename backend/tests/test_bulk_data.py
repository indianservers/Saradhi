import pytest

from backend.domain.rules import BusinessError
from backend.modules.bulk_data.service import (
    BRANCH_FIELDS,
    apply_mapping,
    parse_csv,
    validate_mapping,
)


def test_branch_csv_parser_accepts_utf8_bom_and_normalized_headers():
    headers, rows = parse_csv(
        b"\xef\xbb\xbfExternal Ref,Brand ID,City ID,Branch Name,Latitude,Longitude\n"
        b"store-1,brand,city,North Market,17.4,78.4\n"
    )
    assert headers == list(BRANCH_FIELDS)
    assert apply_mapping(rows[0], {field: field for field in BRANCH_FIELDS}) == {
        "external_ref": "store-1",
        "brand_id": "brand",
        "city_id": "city",
        "branch_name": "North Market",
        "latitude": "17.4",
        "longitude": "78.4",
    }


@pytest.mark.parametrize(
    "content,code",
    [
        (b"\xff", "bulk_csv_encoding"),
        (b"external_ref,external_ref\na,b\n", "bulk_csv_headers"),
        (
            b"external_ref,brand_id,city_id,branch_name,latitude,longitude,phone\na,b,c,d,1,2,1",
            "bulk_csv_columns",
        ),
        (
            b"external_ref,brand_id,city_id,branch_name,latitude,longitude\na,b,c,d,1,2,extra",
            "bulk_csv_shape",
        ),
        (b"\x00", "bulk_csv_encoding"),
    ],
)
def test_branch_csv_rejects_malformed_or_unnecessary_data(content, code):
    with pytest.raises(BusinessError) as error:
        parse_csv(content)
    assert error.value.code == code


def test_mapping_requires_all_fields_and_distinct_known_columns():
    headers = list(BRANCH_FIELDS)
    assert validate_mapping({field: field for field in BRANCH_FIELDS}, headers)
    with pytest.raises(BusinessError, match="required branch field"):
        validate_mapping({"branch_name": "branch_name"}, headers)
    with pytest.raises(BusinessError, match="unique CSV columns"):
        validate_mapping({field: "branch_name" for field in BRANCH_FIELDS}, headers)
