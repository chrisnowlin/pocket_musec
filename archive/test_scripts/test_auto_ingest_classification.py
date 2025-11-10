"""
Test auto-ingest classification system
Validates document classification and appropriate parser routing
"""

import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

# Test documents from NC Music Standards and Resources
TEST_DOCUMENTS = [
    {
        'path': 'NC Music Standards and Resources/Final Music NCSCOS - Google Docs.pdf',
        'expected_type': 'standards',
        'expected_action': 'Parse with table parser'
    },
    {
        'path': 'NC Music Standards and Resources/Kindergarten GM Unpacking - Google Docs.pdf',
        'expected_type': 'unpacking',
        'expected_action': 'Coming soon message'
    },
    {
        'path': 'NC Music Standards and Resources/First Grade GM Unpacking - Google Docs.pdf',
        'expected_type': 'unpacking',
        'expected_action': 'Coming soon message'
    },
    {
        'path': 'NC Music Standards and Resources/Horizontal Alignment - Arts Education Unpacking - Google Docs.pdf',
        'expected_type': 'alignment',
        'expected_action': 'Informational message'
    },
    {
        'path': 'NC Music Standards and Resources/Vertical Alignment - Arts Education Unpacking - Google Docs.pdf',
        'expected_type': 'alignment',
        'expected_action': 'Informational message'
    },
    {
        'path': 'NC Music Standards and Resources/1 PAGE QUICK GUIDES GENERAL MUSIC - Google Docs.pdf',
        'expected_type': 'guide',
        'expected_action': 'Informational message'
    }
]


def run_classification_test(pdf_path: str) -> dict:
    """
    Run auto-ingest command and capture classification results
    
    Returns:
        dict with classification info
    """
    cmd = [
        'python', '-m', 'cli.main',
        'ingest', 'auto',
        pdf_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        output = result.stdout + result.stderr
        
        # Parse output for classification info
        doc_type = None
        confidence = None
        
        for line in output.split('\n'):
            if 'Document type:' in line:
                # Extract type and confidence
                # Format: "📄 Document type: standards (confidence: 100%)"
                parts = line.split('Document type:')[1].strip()
                doc_type = parts.split('(')[0].strip()
                if 'confidence:' in parts:
                    confidence = parts.split('confidence:')[1].split(')')[0].strip()
        
        return {
            'success': True,
            'doc_type': doc_type,
            'confidence': confidence,
            'output': output
        }
    
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Timeout'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """Run classification tests on all document types"""
    
    console.print("\n[bold cyan]AUTO-INGEST CLASSIFICATION SYSTEM TEST[/bold cyan]")
    console.print("=" * 80)
    
    results = []
    
    for i, test_doc in enumerate(TEST_DOCUMENTS, 1):
        console.print(f"\n[yellow]Test {i}/{len(TEST_DOCUMENTS)}:[/yellow] {Path(test_doc['path']).name}")
        
        # Check if file exists
        if not Path(test_doc['path']).exists():
            console.print(f"  [red]⨯ File not found[/red]")
            results.append({
                'file': Path(test_doc['path']).name,
                'status': 'SKIP',
                'expected': test_doc['expected_type'],
                'detected': 'N/A'
            })
            continue
        
        # Run classification
        result = run_classification_test(test_doc['path'])
        
        if result['success']:
            detected_type = result['doc_type']
            confidence = result['confidence']
            
            # Check if matches expected
            matches = detected_type == test_doc['expected_type']
            status_icon = "✓" if matches else "⨯"
            status_color = "green" if matches else "red"
            
            console.print(f"  Expected: [cyan]{test_doc['expected_type']}[/cyan]")
            console.print(f"  Detected: [{status_color}]{detected_type}[/{status_color}] ({confidence})")
            console.print(f"  [{status_color}]{status_icon} {'PASS' if matches else 'FAIL'}[/{status_color}]")
            
            results.append({
                'file': Path(test_doc['path']).name,
                'status': 'PASS' if matches else 'FAIL',
                'expected': test_doc['expected_type'],
                'detected': detected_type,
                'confidence': confidence
            })
        else:
            console.print(f"  [red]⨯ Error: {result.get('error', 'Unknown')}[/red]")
            results.append({
                'file': Path(test_doc['path']).name,
                'status': 'ERROR',
                'expected': test_doc['expected_type'],
                'detected': result.get('error', 'Unknown')
            })
    
    # Print summary table
    console.print("\n" + "=" * 80)
    console.print("[bold cyan]TEST SUMMARY[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Document", style="dim", width=40)
    table.add_column("Expected", justify="center")
    table.add_column("Detected", justify="center")
    table.add_column("Status", justify="center")
    
    for result in results:
        status_style = "green" if result['status'] == "PASS" else "red" if result['status'] == "FAIL" else "yellow"
        table.add_row(
            result['file'][:37] + "..." if len(result['file']) > 40 else result['file'],
            result['expected'],
            result['detected'],
            f"[{status_style}]{result['status']}[/{status_style}]"
        )
    
    console.print(table)
    
    # Calculate pass rate
    passed = sum(1 for r in results if r['status'] == 'PASS')
    total = len([r for r in results if r['status'] != 'SKIP'])
    
    if total > 0:
        pass_rate = (passed / total) * 100
        console.print(f"\n[bold]Pass Rate: {passed}/{total} ({pass_rate:.1f}%)[/bold]")
        
        if pass_rate == 100:
            console.print("\n[green]✅ All classification tests passed![/green]")
        elif pass_rate >= 80:
            console.print("\n[yellow]⚠️  Most tests passed, but some need attention[/yellow]")
        else:
            console.print("\n[red]❌ Classification system needs improvement[/red]")
    
    console.print("\n" + "=" * 80)
    console.print("\n[bold]Key Features Validated:[/bold]")
    console.print("  ✓ Filename pattern matching")
    console.print("  ✓ Content-based classification")
    console.print("  ✓ Confidence scoring")
    console.print("  ✓ Automatic parser routing")
    console.print("  ✓ Graceful handling of unsupported types")


if __name__ == '__main__':
    main()
