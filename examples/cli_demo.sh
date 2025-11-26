#!/bin/bash
# Demo script for AI Agent Meeting CLI

echo "=== AI Agent Meeting CLI Demo ==="
echo ""

# Set data directory for demo
DATA_DIR="demo_data"

echo "1. Listing available role templates..."
python -m src.cli.main --data-path $DATA_DIR agent templates
echo ""

echo "2. Creating agents..."
echo "   Creating Product Manager agent..."
python -m src.cli.main --data-path $DATA_DIR agent create \
  --name "Alice" \
  --provider openai \
  --model gpt-4 \
  --api-key "demo-key-pm" \
  --template product_manager

echo ""
echo "   Creating Software Engineer agent..."
python -m src.cli.main --data-path $DATA_DIR agent create \
  --name "Bob" \
  --provider openai \
  --model gpt-4 \
  --api-key "demo-key-eng" \
  --template software_engineer

echo ""
echo "   Creating UX Designer agent..."
python -m src.cli.main --data-path $DATA_DIR agent create \
  --name "Carol" \
  --provider openai \
  --model gpt-4 \
  --api-key "demo-key-ux" \
  --template ux_designer

echo ""
echo "3. Listing all agents..."
python -m src.cli.main --data-path $DATA_DIR agent list

echo ""
echo "4. Getting agent IDs for meeting..."
# In a real script, you would parse the output to get agent IDs
# For demo purposes, we'll show the command structure

echo ""
echo "5. Creating a meeting..."
echo "   (In practice, you would use actual agent IDs from step 3)"
echo "   Command: python -m src.cli.main meeting create \\"
echo "     --topic 'New Feature Planning' \\"
echo "     --agents 'AGENT_ID_1,AGENT_ID_2,AGENT_ID_3' \\"
echo "     --max-rounds 2 \\"
echo "     --order sequential"

echo ""
echo "6. Running a meeting..."
echo "   Command: python -m src.cli.main meeting run MEETING_ID --rounds 1"

echo ""
echo "7. Sending a user message..."
echo "   Command: python -m src.cli.main meeting send MEETING_ID \\"
echo "     --message 'What are your thoughts on this?'"

echo ""
echo "8. Viewing meeting history..."
echo "   Command: python -m src.cli.main meeting history MEETING_ID"

echo ""
echo "9. Exporting meeting..."
echo "   Command: python -m src.cli.main meeting export MEETING_ID \\"
echo "     --format markdown -o meeting_report.md"

echo ""
echo "10. Listing all meetings..."
python -m src.cli.main --data-path $DATA_DIR meeting list

echo ""
echo "=== Demo Complete ==="
echo ""
echo "To clean up demo data:"
echo "  rm -rf $DATA_DIR"
