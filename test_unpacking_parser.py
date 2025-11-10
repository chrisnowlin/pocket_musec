"""
Test parsing unpacking documents
These documents have a different structure than the standards document
"""

import pdfplumber
import re
from collections import defaultdict

def extract_standards_from_unpacking(pdf_path: str):
    """Extract standard codes and context from unpacking documents"""
    
    results = {
        'standards': [],
        'objectives': [],
        'unpacking_pages': {}  # Maps objective codes to their unpacking content
    }
    
    standard_pattern = r'\b([K1-8AC]\.(?:CN|CR|PR|RE)\.\d+)\b'
    objective_pattern = r'\b([K1-8AC]\.(?:CN|CR|PR|RE)\.\d+\.\d+)\b'
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f'Processing {len(pdf.pages)} pages...\n')
        
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            
            if not text:
                continue
            
            # Find all standard codes on this page
            standards_found = set(re.findall(standard_pattern, text))
            objectives_found = set(re.findall(objective_pattern, text))
            
            # Determine if this is an unpacking page (has detailed content for one objective)
            lines = text.split('\n')
            
            # Check if page starts with an objective code
            if lines and re.match(objective_pattern, lines[0].strip()):
                objective_code = lines[0].strip().split()[0]
                
                # Extract the objective text (usually on the same line or next line)
                objective_text_lines = []
                for i, line in enumerate(lines[:5]):
                    if objective_code in line:
                        # Get text after the code
                        remaining = line.replace(objective_code, '', 1).strip()
                        if remaining:
                            objective_text_lines.append(remaining)
                        # Check next lines for continuation
                        for j in range(i+1, min(i+3, len(lines))):
                            next_line = lines[j].strip()
                            if next_line and not next_line.startswith('Glossary'):
                                objective_text_lines.append(next_line)
                            else:
                                break
                        break
                
                objective_text = ' '.join(objective_text_lines)
                
                # Find glossary section
                glossary_start = -1
                for i, line in enumerate(lines):
                    if line.strip() == 'Glossary':
                        glossary_start = i
                        break
                
                glossary_terms = []
                if glossary_start >= 0:
                    for i in range(glossary_start + 1, min(glossary_start + 20, len(lines))):
                        line = lines[i].strip()
                        if line.startswith('●') or line.startswith('-'):
                            # This is a glossary term
                            term = line.lstrip('●-').strip()
                            if term and len(term) > 3:
                                glossary_terms.append(term)
                        elif line and not line.startswith('●') and 'Alignment' in line:
                            break
                
                results['unpacking_pages'][objective_code] = {
                    'page': page_num,
                    'objective_text': objective_text,
                    'glossary_terms': glossary_terms,
                    'full_text': text
                }
            
            # Collect unique standards and objectives
            for std in standards_found:
                if std not in [s['code'] for s in results['standards']]:
                    results['standards'].append({'code': std, 'first_seen_page': page_num})
            
            for obj in objectives_found:
                if obj not in [o['code'] for o in results['objectives']]:
                    results['objectives'].append({'code': obj, 'first_seen_page': page_num})
    
    return results


def test_on_kindergarten():
    """Test on Kindergarten unpacking document"""
    
    pdf_path = 'NC Music Standards and Resources/Kindergarten GM Unpacking - Google Docs.pdf'
    
    print('='*80)
    print('KINDERGARTEN UNPACKING DOCUMENT PARSER TEST')
    print('='*80)
    
    results = extract_standards_from_unpacking(pdf_path)
    
    print(f'\n📊 SUMMARY:')
    print(f'  • Standards found: {len(results["standards"])}')
    print(f'  • Objectives found: {len(results["objectives"])}')
    print(f'  • Unpacking pages: {len(results["unpacking_pages"])}')
    
    print(f'\n📋 STANDARDS FOUND:')
    for std in sorted(results['standards'], key=lambda x: x['code']):
        print(f'  • {std["code"]} (page {std["first_seen_page"]})')
    
    print(f'\n📝 OBJECTIVES FOUND (first 10):')
    for obj in sorted(results['objectives'], key=lambda x: x['code'])[:10]:
        print(f'  • {obj["code"]} (page {obj["first_seen_page"]})')
    
    print(f'\n🔍 SAMPLE UNPACKING PAGE:')
    # Show first unpacking page
    if results['unpacking_pages']:
        first_obj = sorted(results['unpacking_pages'].keys())[0]
        unpacking = results['unpacking_pages'][first_obj]
        
        print(f'\nObjective: {first_obj}')
        print(f'Page: {unpacking["page"]}')
        print(f'Text: {unpacking["objective_text"][:150]}...')
        print(f'Glossary terms: {len(unpacking["glossary_terms"])}')
        if unpacking["glossary_terms"]:
            print(f'  Sample terms:')
            for term in unpacking["glossary_terms"][:3]:
                print(f'    - {term[:80]}...' if len(term) > 80 else f'    - {term}')
    
    # Distribution check
    print(f'\n📈 DISTRIBUTION CHECK:')
    strands = defaultdict(int)
    for obj in results['objectives']:
        strand = obj['code'].split('.')[1]
        strands[strand] += 1
    
    print('  Objectives by strand:')
    for strand in sorted(strands.keys()):
        print(f'    {strand}: {strands[strand]}')
    
    # Expected: K has 2 standards per strand × 4 strands = 8 standards
    # Each standard has 2-3 objectives typically
    print(f'\n✅ VALIDATION:')
    print(f'  Expected standards: 8 (K.CN.1, K.CN.2, K.CR.1, K.CR.2, K.PR.1, K.PR.2, K.RE.1, K.RE.2)')
    print(f'  Found standards: {len(results["standards"])}')
    
    expected_standards = ['K.CN.1', 'K.CN.2', 'K.CR.1', 'K.CR.2', 'K.PR.1', 'K.PR.2', 'K.RE.1', 'K.RE.2']
    found_codes = [s['code'] for s in results['standards']]
    
    for exp in expected_standards:
        status = '✓' if exp in found_codes else '✗'
        print(f'  {status} {exp}')
    
    return results


def compare_table_parser():
    """Compare table parser results on unpacking document"""
    
    print('\n' + '='*80)
    print('TESTING TABLE PARSER ON UNPACKING DOCUMENT')
    print('='*80)
    
    from backend.ingestion.standards_parser_table import NCStandardsParser
    
    pdf_path = 'NC Music Standards and Resources/Kindergarten GM Unpacking - Google Docs.pdf'
    
    print('\nRunning table parser...')
    parser = NCStandardsParser()
    
    try:
        parsed_standards = parser.parse_standards_document(pdf_path)
        
        print(f'\n📊 TABLE PARSER RESULTS:')
        print(f'  • Standards extracted: {len(parsed_standards)}')
        
        if parsed_standards:
            print(f'\n  Standards found:')
            for std in sorted(parsed_standards, key=lambda x: x.standard_id)[:10]:
                print(f'    • {std.standard_id}: {std.standard_text[:80]}...')
        else:
            print('  ⚠️  No standards extracted (expected - unpacking docs have different structure)')
    
    except Exception as e:
        print(f'  ⚠️  Table parser error: {e}')
        print('  (Expected - unpacking docs are not table-based)')


if __name__ == '__main__':
    results = test_on_kindergarten()
    compare_table_parser()
    
    print('\n' + '='*80)
    print('CONCLUSION')
    print('='*80)
    print("""
Unpacking documents have a very different structure:
  • Not table-based (table parser won't work well)
  • Standards codes embedded in narrative text
  • Each objective has a dedicated "unpacking" page with:
    - Objective text
    - Glossary terms
    - Vertical alignment notes
    - Teaching suggestions
    - Student actions

Recommendation:
  • Use specialized unpacking parser for these documents
  • Extract objective codes and their unpacking content
  • Could be valuable supplementary data for lesson generation
  • Not a replacement for the standards document
    """)
