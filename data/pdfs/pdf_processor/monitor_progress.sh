#!/bin/bash
# Monitor batch processing progress

echo "=== Batch Processing Monitor ==="
echo ""

# Check if process is running
if pgrep -f "batch_process_slow.py" > /dev/null; then
    echo "✅ Batch processor is RUNNING"
    echo "   PID: $(pgrep -f batch_process_slow.py)"
else
    echo "❌ Batch processor is NOT running"
fi

echo ""
echo "📊 Recent Progress (last 20 lines):"
echo "-----------------------------------"
tail -20 /Users/cnowlin/Developer/pocket_musec/data/pdfs/pdf_processor/batch_processing.log

echo ""
echo "📈 Success Rate:"
echo "-----------------------------------"
grep -c "✅ Pages" /Users/cnowlin/Developer/pocket_musec/data/pdfs/pdf_processor/batch_processing.log | xargs -I {} echo "   Successful batches: {}"
grep -c "❌ Pages" /Users/cnowlin/Developer/pocket_musec/data/pdfs/pdf_processor/batch_processing.log | xargs -I {} echo "   Failed batches: {}"

echo ""
echo "To view live updates:"
echo "  tail -f /Users/cnowlin/Developer/pocket_musec/data/pdfs/pdf_processor/batch_processing.log"
