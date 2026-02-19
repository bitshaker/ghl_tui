# GHL TUI

A comprehensive TUI and command-line interface for the GoHighLevel API v2 using Personal Integration Tokens for Auth.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ghl_tui.git
cd ghl_tui

# Install in development mode
pip install -e .
```

## Quick Start

1. **Get your API token** from GoHighLevel:
   - Log into GoHighLevel
   - Go to Settings > Integrations > Private Integrations
   - Click "Create App"
   - Name it (e.g., "GHL TUI")
   - Select required scopes (see below)
   - Copy the generated API key

2. **Configure the CLI**:
   ```bash
   # Set your API token
   ghl config set-token

   # Set your default location (sub-account) ID
   ghl config set-location YOUR_LOCATION_ID

   # Verify configuration
   ghl config show
   ```

3. **Start using the CLI**:
   ```bash
   # List contacts
   ghl contacts list

   # Search for a contact
   ghl contacts search "john"

   # Create a contact
   ghl contacts create --email "john@example.com" --first-name "John" --last-name "Doe"
   ```

## Required Scopes

When creating your Private Integration, select these scopes based on the features you need:

| Feature | Required Scopes |
|---------|----------------|
| Contacts | `contacts.readonly`, `contacts.write` |
| Calendars | `calendars.readonly`, `calendars.write` |
| Opportunities | `opportunities.readonly`, `opportunities.write` |
| Conversations | `conversations.readonly`, `conversations.write` |
| Workflows | `workflows.readonly` |
| Locations | `locations.readonly` |
| Tasks (location-level search, TUI Tasks tab) | `locations/tasks.readonly` |
| Tasks (toggle complete in TUI) | `locations/tasks.write` (if supported) |
| Users | `users.readonly` |

## Commands

### Configuration

```bash
ghl config set-token          # Set API token (interactive, secure)
ghl config set-location ID    # Set default location
ghl config set-format FORMAT  # Set output format (table/json/csv)
ghl config show               # Show current configuration
ghl config clear --all        # Clear all configuration
```

### Profiles (multiple GHL locations)

You can store multiple **profiles**, each with its own API token and location ID. The **active** profile is used for all commands and the TUI, and your last choice is remembered.

```bash
ghl config profiles add NAME              # Add profile (prompts for token & location)
ghl config profiles add work -t TOKEN -l LOCATION_ID   # Add with options
ghl config profiles list                  # List profiles (* = active)
ghl config profiles use NAME             # Switch to this profile (persisted)
ghl config profiles remove NAME          # Remove a profile
```

Example: add `work` and `personal`, then run `ghl config profiles use personal` — the next time you run `ghl` or `ghl tui`, that profile is used by default.

### Contacts

```bash
ghl contacts list                         # List contacts
ghl contacts list --limit 50              # List with custom limit
ghl contacts list --tag "VIP" --tag "Lead"        # Filter by tags (Search API)
ghl contacts list --assigned-to USER_ID           # Filter by assigned user
ghl contacts list -q "john" --tag "Lead"          # Query + tag filter
ghl contacts saved-searches               # List locally saved search filters
ghl contacts get CONTACT_ID               # Get contact details
ghl contacts create --email "a@b.com"     # Create contact
ghl contacts update CONTACT_ID --phone "+1234"    # Update contact
ghl contacts delete CONTACT_ID                    # Delete contact
ghl contacts search "query"               # Search contacts
ghl contacts tag CONTACT_ID --tag "VIP"           # Add tag to contact
ghl contacts untag CONTACT_ID --tag "VIP"         # Remove tag from contact
ghl contacts notes CONTACT_ID                     # List contact notes
ghl contacts add-note CONTACT_ID "Note text"      # Add note to contact
ghl contacts tasks CONTACT_ID                     # List contact tasks
```

Contact list can use the **Contacts Search API** when you pass `--tag` or `--assigned-to`: results are filtered by tags (AND) and/or assigned user. Saved searches are stored in `~/.ghl_tui/saved_searches.json`. In the TUI: **f** = Filter (tags, assigned user, text query; apply or save as search), **s** = Saved searches (pick a saved filter or "All contacts"), **e** = Edit (includes custom fields)—view and edit contact custom fields defined in your location.

### Tasks (location-level)

```bash
ghl tasks search                           # Search tasks (table)
ghl tasks search --json                    # Output as JSON
ghl tasks search --assignee USER_ID        # Filter by assignee
ghl tasks search --status pending         # Filter by status (pending | completed | all)
```

Requires `locations/tasks.readonly` scope. In the TUI: press **3** for the Tasks tab; filter by Assignee and Status, use saved filters (All Tasks, Due Today, Overdue, Upcoming), and press **Enter** to toggle task complete (may require `locations/tasks.write`).

### Custom fields (debug)

```bash
ghl custom-fields list                    # List custom field names, types, and parsed options
ghl custom-fields list --json             # Full field objects as JSON
ghl custom-fields list --raw              # Raw API response (for debugging dropdown option structure)
ghl custom-fields values --contact ID    # Custom values for a contact (--raw for raw response)
```

Use `list --raw` to inspect the exact API shape if a dropdown shows no options in the TUI; the structure can then be matched in the app.

### Calendars & Appointments

```bash
ghl calendars list                        # List calendars
ghl calendars get CALENDAR_ID             # Get calendar details
ghl calendars slots ID --start 2024-01-20 # Get available slots

ghl calendars appointments list           # List appointments
ghl calendars appointments get ID         # Get appointment details
ghl calendars appointments create \
  --calendar CAL_ID \
  --contact CONTACT_ID \
  --slot "2024-01-20T10:00:00Z"           # Create appointment
ghl calendars appointments update ID --title "New Title"
ghl calendars appointments delete ID      # Delete appointment
```

### Opportunities (Pipeline Deals)

```bash
ghl opportunities list                    # List opportunities
ghl opportunities list --pipeline ID      # Filter by pipeline
ghl opportunities list --status won       # Filter by status
ghl opportunities get OPP_ID              # Get opportunity details
ghl opportunities create \
  --contact CONTACT_ID \
  --pipeline PIPE_ID \
  --stage STAGE_ID \
  --name "Deal Name" \
  --value 1000                            # Create opportunity
ghl opportunities move OPP_ID --stage NEW_STAGE_ID
ghl opportunities won OPP_ID              # Mark as won
ghl opportunities lost OPP_ID             # Mark as lost
ghl opportunities delete OPP_ID           # Delete opportunity
```

### Conversations & Messages

```bash
ghl conversations list                    # List conversations
ghl conversations list --contact ID       # Filter by contact
ghl conversations get CONV_ID             # Get conversation details
ghl conversations messages CONV_ID        # List messages
ghl conversations search "query"          # Search conversations
ghl conversations send \
  --contact CONTACT_ID \
  --type sms \
  --message "Hello!"                      # Send SMS
ghl conversations send \
  --contact CONTACT_ID \
  --type email \
  --subject "Subject" \
  --message "Body"                        # Send email
```

### Workflows

```bash
ghl workflows list                        # List workflows
ghl workflows get WORKFLOW_ID             # Get workflow details
ghl workflows trigger ID --contact CID    # Trigger workflow for contact
```

### Pipelines

```bash
ghl pipelines list                        # List pipelines
ghl pipelines get PIPELINE_ID             # Get pipeline with stages
ghl pipelines stages PIPELINE_ID          # List stages in pipeline
```

### Locations (Sub-accounts)

```bash
ghl locations list                        # List locations
ghl locations get LOCATION_ID             # Get location details
ghl locations switch LOCATION_ID          # Switch default location
ghl locations current                     # Show current location
```

### Users

```bash
ghl users list                            # List users
ghl users get USER_ID                     # Get user details
ghl users me                              # Get current user
ghl users search "name"                   # Search users
```

### Tags

```bash
ghl tags list                             # List tags
ghl tags create "Tag Name"                # Create tag
ghl tags get TAG_ID                       # Get tag details
ghl tags delete TAG_ID                    # Delete tag
```

## Output Formats

All list commands support multiple output formats:

```bash
ghl contacts list               # Table format (default)
ghl contacts list --json        # JSON format
ghl contacts list --csv         # CSV format
ghl contacts list --quiet       # IDs only (for scripting)
```

Set default format:
```bash
ghl config set-format json
```

## Environment Variables

You can also configure the CLI using environment variables:

```bash
export GHL_API_TOKEN="your-api-token"
export GHL_LOCATION_ID="your-location-id"
```

Environment variables take precedence over stored configuration.

## Rate Limiting

The CLI automatically handles GoHighLevel's rate limits:
- 100 requests per 10 seconds
- 200,000 requests per day

When rate limited, the CLI will wait and retry automatically.

## Examples

### Create a contact and add to a pipeline

```bash
# Create contact
CONTACT_ID=$(ghl contacts create \
  --email "lead@example.com" \
  --first-name "New" \
  --last-name "Lead" \
  --quiet)

# Add tag
ghl contacts tag $CONTACT_ID --tag "Hot Lead"

# Create opportunity
ghl opportunities create \
  --contact $CONTACT_ID \
  --pipeline YOUR_PIPELINE_ID \
  --stage FIRST_STAGE_ID \
  --name "New Deal" \
  --value 5000

# Send welcome SMS
ghl conversations send \
  --contact $CONTACT_ID \
  --type sms \
  --message "Thanks for your interest!"
```

### Export contacts to CSV

```bash
ghl contacts list --limit 1000 --csv > contacts.csv
```

### Script to process all contacts

```bash
for contact_id in $(ghl contacts list --quiet); do
  echo "Processing $contact_id"
  ghl contacts get $contact_id --json | jq '.email'
done
```

## Development

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run linter
ruff check src/

# Run tests
pytest
```

## License

MIT
