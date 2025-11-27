# MindMapViewer Component

## Overview

The `MindMapViewer` component provides an interactive visualization of meeting mind maps using React Flow. It supports expand/collapse, search, zoom controls, and message reference navigation.

## Features

### ✅ Implemented (Task 33)

1. **React Flow Integration** (Task 33.1)
   - Installed and configured `reactflow` package
   - Set up basic React Flow canvas with Background, Controls, and MiniMap
   - Configured ReactFlowProvider for context management

2. **Data Transformation** (Task 33.2)
   - Convert backend MindMap data to React Flow nodes and edges
   - Tree layout algorithm for automatic node positioning
   - Support for filtering nodes based on expanded state
   - Search functionality with ancestor path expansion
   - Helper functions: `filterByExpandedState`, `getAncestorPath`, `searchNodes`

3. **Expand/Collapse Functionality** (Task 33.4)
   - Click nodes to expand/collapse children
   - Visual indicators (▶/▼) for expandable nodes
   - "Expand All" and "Collapse All" buttons
   - State management with `expandedNodes` Set
   - Dynamic visibility calculation

4. **Node Hover Details** (Task 33.6)
   - Tooltip displays on node hover
   - Shows node content, level, metadata
   - Lists message references with clickable tags
   - Shows children count and expansion state
   - Positioned near the hovered node

5. **Message Reference Navigation** (Task 33.8)
   - Click message reference tags to navigate
   - Callback prop `onMessageRefClick` for parent integration
   - Created `messageNavigation.js` utility with:
     - `scrollToMessage()` - Scroll to specific message
     - `highlightMessage()` - Temporarily highlight message
     - `navigateToMessage()` - Complete navigation with feedback

6. **View Transformation** (Task 33.10)
   - Zoom in/out controls using React Flow instance
   - Fit view button to center and scale the map
   - Drag to pan the canvas
   - Built-in React Flow zoom and pan gestures
   - MiniMap for overview navigation

## Usage

### Basic Usage

```jsx
import MindMapViewer from './components/MindMapViewer';

function MyComponent() {
  const [mindMapData, setMindMapData] = useState(null);

  const handleMessageRefClick = (messageId) => {
    // Navigate to the message in your meeting view
    scrollToMessage(messageId);
  };

  const handleExport = (format) => {
    // Call backend API to export mind map
    exportMindMap(meetingId, format);
  };

  return (
    <div style={{ width: '100%', height: '600px' }}>
      <MindMapViewer
        mindMapData={mindMapData}
        onMessageRefClick={handleMessageRefClick}
        onExport={handleExport}
      />
    </div>
  );
}
```

### Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `mindMapData` | Object | Yes | Mind map data from backend (see data structure below) |
| `onMessageRefClick` | Function | No | Callback when message reference is clicked. Receives `messageId` |
| `onExport` | Function | No | Callback for export action. Receives `format` ('png', 'svg', 'json', 'markdown') |

### Mind Map Data Structure

```javascript
{
  id: 'mindmap-1',
  meeting_id: 'meeting-1',
  root_node: {
    id: 'root',
    content: 'Meeting Topic',
    level: 0,
    parent_id: null,
    children_ids: ['node-1', 'node-2'],
    message_references: [],
    metadata: {}
  },
  nodes: {
    'root': { /* root node */ },
    'node-1': {
      id: 'node-1',
      content: 'First Branch',
      level: 1,
      parent_id: 'root',
      children_ids: ['node-1-1'],
      message_references: ['msg-1', 'msg-2'],
      metadata: { category: 'technical' }
    },
    // ... more nodes
  },
  created_at: '2024-01-01T00:00:00',
  created_by: 'user-1',
  version: 1
}
```

## User Interactions

### Keyboard & Mouse

- **Click node**: Expand/collapse children
- **Hover node**: Show tooltip with details
- **Drag canvas**: Pan the view
- **Mouse wheel**: Zoom in/out
- **Click message tag**: Navigate to message (if callback provided)

### Toolbar Controls

- **Search**: Find nodes by content (highlights and expands path)
- **Zoom In/Out**: Adjust zoom level
- **Expand All**: Show all nodes
- **Collapse All**: Show only root node
- **Fit View**: Center and scale to fit all visible nodes
- **Export**: Export mind map (if callback provided)

## Styling

The component uses inline styles and Ant Design components. Node styles are based on:

- **Root node**: Blue background, white text, bold
- **Branch nodes**: White background, black text
- **Highlighted nodes**: Green border and shadow (from search)
- **Expandable nodes**: Show ▶ (collapsed) or ▼ (expanded)

## Integration with Meeting Room

To integrate the mind map viewer into a meeting room page:

1. **Fetch mind map data** from backend API
2. **Pass message navigation callback** to scroll to messages
3. **Implement export handler** to call backend export API
4. **Add to meeting UI** as a modal, drawer, or separate page

Example integration:

```jsx
import { Modal } from 'antd';
import MindMapViewer from './components/MindMapViewer';
import { scrollToMessage } from './utils/messageNavigation';

function MeetingRoom({ meeting }) {
  const [mindMapVisible, setMindMapVisible] = useState(false);
  const [mindMapData, setMindMapData] = useState(null);

  const loadMindMap = async () => {
    const response = await fetch(`/api/meetings/${meeting.id}/mind-map`);
    const data = await response.json();
    setMindMapData(data);
    setMindMapVisible(true);
  };

  const handleMessageRefClick = (messageId) => {
    setMindMapVisible(false);
    scrollToMessage(messageId, {
      smooth: true,
      highlight: true,
      highlightDuration: 3000
    });
  };

  return (
    <>
      <Button onClick={loadMindMap}>View Mind Map</Button>
      
      <Modal
        title="Meeting Mind Map"
        open={mindMapVisible}
        onCancel={() => setMindMapVisible(false)}
        width="90%"
        style={{ top: 20 }}
        bodyStyle={{ height: 'calc(100vh - 200px)' }}
      >
        <MindMapViewer
          mindMapData={mindMapData}
          onMessageRefClick={handleMessageRefClick}
        />
      </Modal>
    </>
  );
}
```

## Demo

A demo page is available at `src/pages/MindMapDemo.jsx` with sample data demonstrating all features.

## Dependencies

- `reactflow` - Mind map visualization
- `antd` - UI components (Button, Input, Tag, etc.)
- `@ant-design/icons` - Icons for toolbar

## Files

- `src/components/MindMapViewer.jsx` - Main component
- `src/utils/mindMapTransform.js` - Data transformation utilities
- `src/utils/messageNavigation.js` - Message navigation utilities
- `src/pages/MindMapDemo.jsx` - Demo page

## Future Enhancements (Not in Task 33)

- Custom node components with richer styling
- Drag-and-drop to reorganize nodes
- Edit node content inline
- Add/remove nodes manually
- Export to additional formats (PDF, FreeMind)
- Collaborative editing with real-time updates
- Keyboard shortcuts for navigation
- Accessibility improvements (ARIA labels, keyboard navigation)

## Testing

Property-based tests are marked as optional (tasks 33.3, 33.5, 33.7, 33.9, 33.11) and are not implemented in this task execution.

## Requirements Validation

This implementation satisfies the following requirements from the design document:

- **Requirement 23.1**: Interactive visualization with React Flow ✅
- **Requirement 23.2**: Node expand/collapse functionality ✅
- **Requirement 23.3**: Node hover details display ✅
- **Requirement 23.4**: Message reference jump functionality ✅
- **Requirement 23.5**: View transformation (zoom, pan, fit) ✅
- **Requirement 23.6**: Search functionality ✅
