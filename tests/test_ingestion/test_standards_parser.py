"""Tests for NC Standards parser"""


def test_nc_standards_parser_creation():
    """Test that NCStandardsParser can be created"""
    from backend.ingestion.nc_standards_formal_parser import NCStandardsParser

    parser = NCStandardsParser()
    assert parser is not None
    assert parser.parsed_standards == []
    assert parser.pdf_reader is not None


def test_extract_grade_level():
    """Test grade level extraction"""
    from backend.ingestion.nc_standards_formal_parser import NCStandardsParser

    parser = NCStandardsParser()

    assert parser._extract_grade_level("Kindergarten") == "K"
    assert parser._extract_grade_level("K") == "K"
    assert parser._extract_grade_level("Grade 5") == "5"
    assert parser._extract_grade_level("5th Grade") == "5"
    assert parser._extract_grade_level("Beginning") == "BE"
    assert parser._extract_grade_level("Intermediate") == "IN"
    assert parser._extract_grade_level("Advanced") == "AD"
    assert parser._extract_grade_level("Accomplished") == "AC"
    assert parser._extract_grade_level("Random text") is None


def test_extract_strand():
    """Test strand extraction"""
    from backend.ingestion.nc_standards_formal_parser import NCStandardsParser

    parser = NCStandardsParser()

    cn_result = parser._extract_strand("Connect")
    assert cn_result == ("CN", "Connect")

    cr_result = parser._extract_strand("Create")
    assert cr_result == ("CR", "Create")

    pr_result = parser._extract_strand("Present")
    assert pr_result == ("PR", "Present")

    re_result = parser._extract_strand("Respond")
    assert re_result == ("RE", "Respond")

    assert parser._extract_strand("Random text") is None


def test_extract_standard_id():
    """Test standard ID extraction"""
    from backend.ingestion.nc_standards_formal_parser import NCStandardsParser

    parser = NCStandardsParser()

    assert parser._extract_standard_id("K.CN.1") == "K.CN.1"
    assert parser._extract_standard_id("5.CR.2") == "5.CR.2"
    assert parser._extract_standard_id("BE.PR.1") == "BE.PR.1"
    assert parser._extract_standard_id("Random text") is None


def test_is_objective():
    """Test objective identification"""
    from backend.ingestion.nc_standards_formal_parser import NCStandardsParser

    parser = NCStandardsParser()

    # Bullet points
    assert parser._is_objective("• Demonstrate rhythm")
    assert parser._is_objective("- Perform melody")
    assert parser._is_objective("* Create harmony")

    # Numbered lists
    assert parser._is_objective("1. Identify notes")
    assert parser._is_objective("2) Analyze form")

    # Action verbs
    assert parser._is_objective("Demonstrate proper technique")
    assert parser._is_objective("Perform with expression")
    assert parser._is_objective("Create original composition")

    # Non-objectives
    assert not parser._is_objective("Standard K.CN.1")
    assert not parser._is_objective("Connect")
    assert not parser._is_objective("Random text")


def test_get_statistics_empty():
    """Test statistics on empty parser"""
    from backend.ingestion.nc_standards_formal_parser import NCStandardsParser

    parser = NCStandardsParser()
    stats = parser.get_statistics()

    assert stats == {}


def test_normalize_to_models_empty():
    """Test normalization with no parsed standards"""
    from backend.ingestion.nc_standards_formal_parser import NCStandardsParser

    parser = NCStandardsParser()
    standards, objectives = parser.normalize_to_models("test.pdf")

    assert standards == []
    assert objectives == []
