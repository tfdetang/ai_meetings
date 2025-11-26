# AI Agent Meeting CLI Usage Guide

## Installation

```bash
pip install -e .
```

## Quick Start

### 1. Create Agents

Create an agent using a role template:
```bash
python -m src.cli.main agent create \
  --name "Alice" \
  --provider openai \
  --model gpt-4 \
  --api-key YOUR_API_KEY \
  --template product_manager
```

Create an agent with custom role:
```bash
python -m src.cli.main agent create \
  --name "Bob" \
  --provider anthropic \
  --model claude-3-opus-20240229 \
  --api-key YOUR_API_KEY \
  --role-name "Engineer" \
  --role-description "A software engineer" \
  --role-prompt "You are a software engineer..."
```

### 2. List Available Templates

```bash
python -m src.cli.main agent templates
```

### 3. List Agents

```bash
python -m src.cli.main agent list
```

### 4. Show Agent Details

```bash
python -m src.cli.main agent show AGENT_ID
```

### 5. Test Agent Connection

```bash
python -m src.cli.main agent test AGENT_ID
```

### 6. Create a Meeting

```bash
python -m src.cli.main meeting create \
  --topic "Product Planning Discussion" \
  --agents "AGENT_ID_1,AGENT_ID_2,AGENT_ID_3" \
  --max-rounds 3 \
  --order sequential
```

### 7. Run a Meeting

Run for one round (all agents speak once):
```bash
python -m src.cli.main meeting run MEETING_ID --rounds 1
```

### 8. Send User Message

```bash
python -m src.cli.main meeting send MEETING_ID --message "What do you think about this feature?"
```

### 9. Request Specific Agent Response

```bash
python -m src.cli.main meeting request MEETING_ID AGENT_ID
```

### 10. View Meeting History

```bash
python -m src.cli.main meeting history MEETING_ID
```

### 11. Export Meeting

Export to Markdown:
```bash
python -m src.cli.main meeting export MEETING_ID --format markdown -o meeting.md
```

Export to JSON:
```bash
python -m src.cli.main meeting export MEETING_ID --format json -o meeting.json
```

### 12. Pause/Resume Meeting

```bash
python -m src.cli.main meeting pause MEETING_ID
python -m src.cli.main meeting start MEETING_ID
```

### 13. End Meeting

```bash
python -m src.cli.main meeting end MEETING_ID
```

### 14. List All Meetings

```bash
python -m src.cli.main meeting list
```

### 15. Delete Agent or Meeting

```bash
python -m src.cli.main agent delete AGENT_ID
python -m src.cli.main meeting delete MEETING_ID
```

## Command Reference

### Agent Commands

- `agent create` - Create a new agent
- `agent list` - List all agents
- `agent show AGENT_ID` - Show agent details
- `agent update AGENT_ID` - Update agent configuration
- `agent delete AGENT_ID` - Delete an agent
- `agent test AGENT_ID` - Test agent connection
- `agent templates` - List available role templates

### Meeting Commands

- `meeting create` - Create a new meeting
- `meeting list` - List all meetings
- `meeting show MEETING_ID` - Show meeting details
- `meeting start MEETING_ID` - Start/resume a meeting
- `meeting pause MEETING_ID` - Pause a meeting
- `meeting end MEETING_ID` - End a meeting
- `meeting delete MEETING_ID` - Delete a meeting
- `meeting send MEETING_ID` - Send a user message
- `meeting request MEETING_ID AGENT_ID` - Request agent response
- `meeting run MEETING_ID` - Run meeting for multiple rounds
- `meeting history MEETING_ID` - View complete meeting history
- `meeting export MEETING_ID` - Export meeting to file

## Examples

### Example 1: Quick Product Discussion

```bash
# Create agents
python -m src.cli.main agent create --name "PM" --provider openai --model gpt-4 --api-key $OPENAI_KEY --template product_manager
python -m src.cli.main agent create --name "Engineer" --provider openai --model gpt-4 --api-key $OPENAI_KEY --template software_engineer
python -m src.cli.main agent create --name "Designer" --provider openai --model gpt-4 --api-key $OPENAI_KEY --template ux_designer

# Get agent IDs
python -m src.cli.main agent list

# Create meeting
python -m src.cli.main meeting create --topic "New Feature Discussion" --agents "ID1,ID2,ID3" --max-rounds 2

# Run meeting
python -m src.cli.main meeting run MEETING_ID --rounds 2

# Export results
python -m src.cli.main meeting export MEETING_ID --format markdown -o discussion.md
```

### Example 2: Interactive Meeting

```bash
# Create meeting
python -m src.cli.main meeting create --topic "Architecture Review" --agents "ID1,ID2"

# Send initial message
python -m src.cli.main meeting send MEETING_ID --message "Let's discuss the database architecture"

# Request specific agent
python -m src.cli.main meeting request MEETING_ID AGENT_ID_1

# View history
python -m src.cli.main meeting history MEETING_ID

# Continue discussion
python -m src.cli.main meeting send MEETING_ID --message "What about scalability?"
python -m src.cli.main meeting request MEETING_ID AGENT_ID_2

# End meeting
python -m src.cli.main meeting end MEETING_ID
```

## Tips

1. **Use Templates**: Start with role templates for common roles, they have well-crafted prompts
2. **Test Connections**: Always test agent connections before creating meetings
3. **Export Regularly**: Export important meetings to preserve discussions
4. **Use Sequential Order**: For structured discussions, use sequential speaking order
5. **Set Max Rounds**: Prevent infinite discussions by setting max rounds
6. **View History**: Use `meeting history` to review full conversations with formatting
