# Remove Ingestion Pipeline

## Problem Statement
The ingestion pipeline has been underperforming and is causing more issues than benefits. The current system includes complex parsers, document classification, and the PocketFlow abstraction layer for ingestion, but these components are not providing sufficient value to justify their maintenance overhead and complexity.

## Proposed Solution
Remove the entire ingestion pipeline from the backend while preserving the frontend UI elements. The buttons and interface components will remain but will simply not perform any functionality when clicked. This includes:

- Removing all ingestion-related backend code (parsers, agents, nodes, API routes)
- Removing the PocketFlow ingestion abstraction components
- Keeping frontend UI components intact but non-functional

## What Changes
- **Backend**: Complete removal of `/backend/ingestion/` directory, PocketFlow ingestion components, and ingestion API routes
- **Frontend**: Update error handling to gracefully display "feature unavailable" instead of crashing
- **Dependencies**: Remove PDF parsing and vision API libraries from backend requirements
- **Documentation**: Update API docs and user-facing documentation to reflect removal

## Scope
### In Scope
- Complete removal of `/backend/ingestion/` directory and all its parsers
- Removal of `/backend/pocketflow/ingestion_agent.py` and `/backend/pocketflow/ingestion_nodes.py`
- Removal of `/backend/api/routes/ingestion.py` API endpoints
- Removal of ingestion-related imports and dependencies
- Frontend UI elements remain but become non-functional

### Out of Scope
- Frontend UI component removal (buttons stay but don't work)
- Database schema changes (existing ingested data remains)
- File storage system (this is separate from ingestion)
- Other backend functionality (lesson generation, standards retrieval, etc.)

## Rationale
- **Performance**: The ingestion pipeline is underperforming and causing reliability issues
- **Maintenance**: Complex parser logic requires significant maintenance effort
- **User Experience**: Removing functionality is better than providing broken or unreliable ingestion
- **Simplicity**: Reduces codebase complexity and attack surface
- **Future**: Can be rebuilt more simply if needed later

## Why
The ingestion pipeline has proven to be unreliable and overly complex for the value it provides. The parsers frequently fail on various document layouts, the PocketFlow abstraction adds unnecessary complexity, and the maintenance overhead outweighs the benefits. By removing this functionality while preserving the UI, we maintain the user experience while eliminating a source of instability and technical debt.

## Impact Assessment
- **Backend**: Significant reduction in code complexity and dependencies
- **Frontend**: UI remains unchanged but ingestion features become non-functional
- **Users**: Can no longer upload new documents, but existing functionality remains
- **Data**: Previously ingested standards and documents remain accessible