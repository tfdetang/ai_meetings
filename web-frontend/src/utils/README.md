# Mind Map Transformation Utilities

This module provides utilities for transforming backend MindMap data into React Flow compatible format.

## Overview

The transformation utilities convert the hierarchical mind map structure from the backend into nodes and edges that can be rendered by React Flow. The module includes:

1. **Node Conversion**: Transforms MindMapNode objects into React Flow nodes with calculated positions
2. **Edge Conversion**: Creates React Flow edges from parent-child relationships
3. **Layout Algorithm**: Implements a tree layout algorithm for positioning nodes

## Data Structures

### Backend MindMap Structure

```javascript
{
  id: string,
  meeting_id: string,
  root_node: MindMapNode,
  nodes: {
    [nodeId]: MindMapNode
  },
  created_at: string,
  created_by: string,
  version: number
}
```

### MindMapNode Structure

```javascript
{
  id: string,
  content: string,
  level: number,              // 0 for root, 1+ for children
  parent_id: string | null,
  children_ids: string[],
  message_references: string[],
  metadata: object
}
```

### React Flow Node Structure

```javascript
{
  id: string,
  type: 'input' | 'default',
  data: {
    label: string,
    level: number,
    messageReferences: string[],
    metadata: object,
    originalNode: MindMapNode
  },
  position: { x: number, y: number },
  style: object
}
```

### React Flow Edge Structure

```javascript
{
  id: string,
  source: string,
  target: string,
  type: 'smoothstep',
  animated: boolean,
  style: object,
  markerEnd: object
}
```

## API Reference

### `convertToReactFlowNodes(mindMap)`

Converts MindMap data to React Flow nodes with calculated positions.

**Parameters:**
- `mindMap` (Object): The mind map data from backend

**Returns:**
- Array of React Flow node objects

**Example:**
```javascript
import { convertToReactFlowNodes } from './utils/mindMapTransform';

const nodes = convertToReactFlowNodes(mindMapData);
// nodes = [{ id: 'node-1', position: { x: 0, y: 0 }, ... }, ...]
```

### `convertToReactFlowEdges(mindMap)`

Converts node relationships to React Flow edges.

**Parameters:**
- `mindMap` (Object): The mind map data from backend

**Returns:**
- Array of React Flow edge objects

**Example:**
```javascript
import { convertToReactFlowEdges } from './utils/mindMapTransform';

const edges = convertToReactFlowEdges(mindMapData);
// edges = [{ id: 'e-node1-node2', source: 'node1', target: 'node2', ... }, ...]
```

### `transformMindMapToReactFlow(mindMap)`

Convenience function that combines node and edge conversion.

**Parameters:**
- `mindMap` (Object): The mind map data from backend

**Returns:**
- Object with `nodes` and `edges` arrays

**Example:**
```javascript
import { transformMindMapToReactFlow } from './utils/mindMapTransform';

const { nodes, edges } = transformMindMapToReactFlow(mindMapData);
```

### `recalculateLayout(nodes, mindMap)`

Recalculates positions for existing React Flow nodes. Useful after expand/collapse operations.

**Parameters:**
- `nodes` (Array): Current React Flow nodes
- `mindMap` (Object): The mind map data from backend

**Returns:**
- Array of updated nodes with new positions

**Example:**
```javascript
import { recalculateLayout } from './utils/mindMapTransform';

const updatedNodes = recalculateLayout(currentNodes, mindMapData);
```

## Layout Algorithm

The tree layout algorithm positions nodes using the following rules:

1. **Horizontal Spacing**: Nodes at different levels are spaced 300px apart horizontally
2. **Vertical Spacing**: Sibling nodes are spaced 100px apart vertically
3. **Root Positioning**: The root node is centered at (0, 0)
4. **Child Distribution**: Children are distributed evenly around their parent's Y position

### Layout Example

```
Level 0:        [Root]
                  |
Level 1:    [A]  [B]  [C]
            |         |
Level 2:  [A1][A2]  [C1]
```

Positions:
- Root: (0, 0)
- A: (300, -100)
- B: (300, 0)
- C: (300, 100)
- A1: (600, -150)
- A2: (600, -50)
- C1: (600, 100)

## Styling

### Node Styling

- **Root Node**: Blue background (#1890ff), white text, bold, larger font (16px)
- **Child Nodes**: White background, black text, normal weight, smaller font (14px)
- **All Nodes**: Rounded corners (8px), padding (10px), minimum width (150px)

### Edge Styling

- **Type**: Smooth step edges for better visualization
- **Color**: Gray (#b1b1b7)
- **Width**: 2px
- **Markers**: Arrow markers at the end of each edge

## Usage in React Components

### Basic Usage

```javascript
import React, { useEffect, useState } from 'react';
import ReactFlow from 'reactflow';
import { transformMindMapToReactFlow } from '../utils/mindMapTransform';

function MindMapViewer({ mindMapData }) {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);

  useEffect(() => {
    if (mindMapData) {
      const { nodes, edges } = transformMindMapToReactFlow(mindMapData);
      setNodes(nodes);
      setEdges(edges);
    }
  }, [mindMapData]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      fitView
    />
  );
}
```

### With Expand/Collapse

```javascript
import React, { useEffect, useState } from 'react';
import ReactFlow from 'reactflow';
import { 
  transformMindMapToReactFlow,
  recalculateLayout 
} from '../utils/mindMapTransform';

function MindMapViewer({ mindMapData }) {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [expandedNodes, setExpandedNodes] = useState(new Set());

  useEffect(() => {
    if (mindMapData) {
      const { nodes, edges } = transformMindMapToReactFlow(mindMapData);
      setNodes(nodes);
      setEdges(edges);
    }
  }, [mindMapData]);

  const handleNodeClick = (event, node) => {
    // Toggle expand/collapse
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(node.id)) {
      newExpanded.delete(node.id);
    } else {
      newExpanded.add(node.id);
    }
    setExpandedNodes(newExpanded);

    // Recalculate layout
    const updatedNodes = recalculateLayout(nodes, mindMapData);
    setNodes(updatedNodes);
  };

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodeClick={handleNodeClick}
      fitView
    />
  );
}
```

## Testing

The module includes comprehensive tests covering:

- Node conversion with correct data structure
- Edge creation for all relationships
- Position calculation for tree layout
- Handling of empty/null data
- Root node special styling
- Sibling node distribution

Run tests with:
```bash
npm test mindMapTransform.test.js
```

## Performance Considerations

- **Node Count**: The layout algorithm is O(n) where n is the number of nodes
- **Memory**: Stores position data for all nodes in memory
- **Re-rendering**: Use React.memo or useMemo to prevent unnecessary recalculations

## Future Enhancements

Potential improvements for future versions:

1. **Dynamic Spacing**: Adjust spacing based on node content length
2. **Collision Detection**: Prevent node overlap in dense graphs
3. **Alternative Layouts**: Support for radial, force-directed, or custom layouts
4. **Animation**: Smooth transitions when recalculating positions
5. **Zoom Levels**: Adjust detail level based on zoom
