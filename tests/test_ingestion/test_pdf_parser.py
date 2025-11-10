"""Tests for PDF parsing components"""

def test_pdf_reader_creation():
    """Test that a PDFReader can be created"""
    from backend.ingestion.pdf_parser import PDFReader
    
    reader = PDFReader()
    assert reader is not None
    assert reader.pages == []


def test_text_block_creation():
    """Test TextBlock dataclass"""
    from backend.ingestion.pdf_parser import TextBlock
    
    block = TextBlock(
        text="test",
        x0=0.0,
        y0=0.0,
        x1=10.0,
        y1=5.0,
        page_number=1
    )
    
    assert block.text == "test"
    assert block.page_number == 1
    assert block.x0 == 0.0
    assert block.y0 == 0.0


def test_parsed_page_creation():
    """Test ParsedPage dataclass"""
    from backend.ingestion.pdf_parser import ParsedPage, TextBlock
    
    blocks = [TextBlock("test", 0, 0, 10, 5, 1)]
    page = ParsedPage(
        page_number=1,
        width=612.0,
        height=792.0,
        text_blocks=blocks,
        raw_text="test page"
    )
    
    assert page.page_number == 1
    assert len(page.text_blocks) == 1
    assert page.raw_text == "test page"


def test_pdf_reader_file_not_found():
    """Test PDF reader with non-existent file"""
    from backend.ingestion.pdf_parser import PDFReader
    import pytest
    
    reader = PDFReader()
    
    with pytest.raises(FileNotFoundError):
        reader.read_pdf("nonexistent.pdf")


def test_pdf_reader_statistics_empty():
    """Test statistics on empty PDF reader"""
    from backend.ingestion.pdf_parser import PDFReader
    
    reader = PDFReader()
    stats = reader.get_statistics()
    
    assert stats == {}


def test_pdf_reader_get_page_text_empty():
    """Test getting text from empty PDF reader"""
    from backend.ingestion.pdf_parser import PDFReader
    
    reader = PDFReader()
    text = reader.get_page_text(1)
    
    assert text == ""


def test_pdf_reader_get_all_text_empty():
    """Test getting all text from empty PDF reader"""
    from backend.ingestion.pdf_parser import PDFReader
    
    reader = PDFReader()
    text = reader.get_all_text()
    
    assert text == ""