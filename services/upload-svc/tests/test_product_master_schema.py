"""Product master rich-column schema + legacy aliases."""

from app.core.validator import FILE_SCHEMAS, UploadValidator


def test_product_master_required_fields():
    req = FILE_SCHEMAS["product_master"]["required"]
    for col in (
        "product_code",
        "product_group",
        "product_type",
        "short_name",
        "full_name",
        "uom",
        "main_storage_location",
    ):
        assert col in req


def test_validate_rich_product_csv():
    content = (
        b"product_code,product_group,product_type,short_name,full_name,uom,main_storage_location\n"
        b"FG-DT100,DT,finished,DT100,Distribution Transformer 100kVA,EA,WH-FG\n"
    )
    result = UploadValidator().validate("product_master", content, "products.csv")
    assert result.stage_1_structure["status"] == "pass"
    assert result.accepted == 1
    assert result.rejected == 0


def test_legacy_name_type_aliases():
    """Old thin templates (name/type) still map via column_aliases."""
    content = (
        b"product_code,product_group,name,type,uom,main_storage_location\n"
        b"FG-DT100,DT,DT100,finished,EA,WH-FG\n"
    )
    result = UploadValidator().validate("product_master", content, "legacy.csv")
    assert result.stage_1_structure["status"] == "pass"
    assert result.accepted == 1
