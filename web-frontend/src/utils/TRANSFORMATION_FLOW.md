# Mind Map Transformation Flow

## Visual Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Backend MindMap Data                         │
│                                                                  │
│  {                                                               │
│    id: "mindmap-1",                                             │
│    nodes: {                                                      │
│      "root": { content: "Meeting", level: 0, ... },            │
│      "node-1": { content: "Topic 1", level: 1, ... },          │
│      "node-2": { content: "Topic 2", level: 1, ... }           │
│    }                                                             │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                              ↓ transformMindMapToReactFlow()
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Step 1: Calculate Positions                    │
│                                                                  │
│  calculateNodePositions(mindMap)                                │
│                                                                  │
│  Algorithm:                                                      │
│  1. Start at root (0, 0)                                        │
│  2. Place children at next level (x + 300)                     │
│  3. Distribute siblings vertically (y ± 100)                   │
│  4. Recurse for all children                                    │
│                                                                  │
│  Result: { "root": {x:0, y:0}, "node-1": {x:300, y:-50}, ... } │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                              ↓
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Step 2: Convert to Nodes                       │
│                                                                  │
│  convertToReactFlowNodes(mindMap)                               │
│                                                                  │
│  For each node:                                                  │
│  - Get calculated position                                       │
│  - Set type (root = 'input', others = 'default')               │
│  - Apply styling based on level                                 │
│  - Preserve data (label, references, metadata)                  │
│                                                                  │
│  Result: [                                                       │
│    {                                                             │
│      id: "root",                                                │
│      type: "input",                                             │
│      position: { x: 0, y: 0 },                                 │
│      data: { label: "Meeting", ... },                          │
│      style: { background: "#1890ff", ... }                     │
│    },                                                            │
│    ...                                                           │
│  ]                                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                              ↓
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Step 3: Convert to Edges                       │
│                                                                  │
│  convertToReactFlowEdges(mindMap)                               │
│                                                                  │
│  For each node with children:                                    │
│  - Create edge from parent to each child                        │
│  - Set edge type to 'smoothstep'                               │
│  - Add arrow markers                                            │
│  - Apply consistent styling                                     │
│                                                                  │
│  Result: [                                                       │
│    {                                                             │
│      id: "e-root-node-1",                                       │
│      source: "root",                                            │
│      target: "node-1",                                          │
│      type: "smoothstep",                                        │
│      markerEnd: { type: "arrowclosed" }                        │
│    },                                                            │
│    ...                                                           │
│  ]                                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                              ↓
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    React Flow Compatible Data                    │
│                                                                  │
│  {                                                               │
│    nodes: [ ... ],  // Ready for rendering                     │
│    edges: [ ... ]   // Ready for rendering                     │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                              ↓
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      ReactFlow Component                         │
│                                                                  │
│  <ReactFlow nodes={nodes} edges={edges} />                     │
│                                                                  │
│  Renders:                                                        │
│                                                                  │
│         ┌─────────────┐                                         │
│         │   Meeting   │  (Root - Blue)                         │
│         └──────┬──────┘                                         │
│                │                                                 │
│       ┌────────┴────────┐                                       │
│       │                 │                                       │
│  ┌────▼────┐      ┌────▼────┐                                 │
│  │ Topic 1 │      │ Topic 2 │  (Children - White)             │
│  └─────────┘      └─────────┘                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Layout Algorithm Details

### Horizontal Positioning (X-axis)

```
Level 0:  x = 0 * 300 = 0
Level 1:  x = 1 * 300 = 300
Level 2:  x = 2 * 300 = 600
Level 3:  x = 3 * 300 = 900
...
```

### Vertical Positioning (Y-axis)

For a parent with 3 children:

```
Parent Y = 0

Child count = 3
Total height = (3 - 1) * 100 = 200
Start Y = 0 - 200/2 = -100

Child 0: y = -100 + 0 * 100 = -100
Child 1: y = -100 + 1 * 100 = 0
Child 2: y = -100 + 2 * 100 = 100
```

Visual representation:

```
                Parent (0, 0)
                     |
        ┌────────────┼────────────┐
        │            │            │
   Child 0      Child 1      Child 2
  (300,-100)   (300, 0)    (300,100)
```

## Data Structure Transformation

### Input: Backend MindMapNode

```javascript
{
  id: "node-1",
  content: "Technical Architecture",
  level: 1,
  parent_id: "root",
  children_ids: ["node-1-1", "node-1-2"],
  message_references: ["msg-1", "msg-2"],
  metadata: { importance: "high" }
}
```

### Output: React Flow Node

```javascript
{
  id: "node-1",
  type: "default",
  data: {
    label: "Technical Architecture",
    level: 1,
    messageReferences: ["msg-1", "msg-2"],
    metadata: { importance: "high" },
    originalNode: { /* full node data */ }
  },
  position: { x: 300, y: -50 },
  style: {
    background: "#fff",
    color: "#000",
    border: "1px solid #d9d9d9",
    borderRadius: "8px",
    padding: "10px",
    minWidth: "150px",
    fontSize: "14px",
    fontWeight: "normal"
  }
}
```

## Edge Creation Logic

### Input: Parent-Child Relationship

```javascript
Parent Node: {
  id: "root",
  children_ids: ["node-1", "node-2", "node-3"]
}
```

### Output: React Flow Edges

```javascript
[
  {
    id: "e-root-node-1",
    source: "root",
    target: "node-1",
    type: "smoothstep",
    style: { stroke: "#b1b1b7", strokeWidth: 2 },
    markerEnd: { type: "arrowclosed", color: "#b1b1b7" }
  },
  {
    id: "e-root-node-2",
    source: "root",
    target: "node-2",
    type: "smoothstep",
    style: { stroke: "#b1b1b7", strokeWidth: 2 },
    markerEnd: { type: "arrowclosed", color: "#b1b1b7" }
  },
  {
    id: "e-root-node-3",
    source: "root",
    target: "node-3",
    type: "smoothstep",
    style: { stroke: "#b1b1b7", strokeWidth: 2 },
    markerEnd: { type: "arrowclosed", color: "#b1b1b7" }
  }
]
```

## Styling Rules

### Node Styling by Level

| Level | Background | Text Color | Border | Font Size | Font Weight |
|-------|-----------|------------|--------|-----------|-------------|
| 0 (Root) | #1890ff (Blue) | #fff (White) | 2px solid #1890ff | 16px | bold |
| 1+ (Children) | #fff (White) | #000 (Black) | 1px solid #d9d9d9 | 14px | normal |

### Edge Styling

- **Type**: smoothstep (curved edges)
- **Color**: #b1b1b7 (Gray)
- **Width**: 2px
- **Marker**: Arrow at end
- **Animation**: None (can be enabled)

## Performance Characteristics

### Time Complexity

- **calculateNodePositions**: O(n) - visits each node once
- **convertToReactFlowNodes**: O(n) - processes each node once
- **convertToReactFlowEdges**: O(e) - processes each edge once
- **Total**: O(n + e) where n = nodes, e = edges

### Space Complexity

- **Position storage**: O(n) - one position per node
- **Node array**: O(n) - one React Flow node per backend node
- **Edge array**: O(e) - one React Flow edge per relationship
- **Total**: O(n + e)

## Example Transformation

### Input

```javascript
{
  nodes: {
    "root": { level: 0, children_ids: ["a", "b"] },
    "a": { level: 1, children_ids: ["a1"] },
    "b": { level: 1, children_ids: [] },
    "a1": { level: 2, children_ids: [] }
  }
}
```

### Output

```javascript
{
  nodes: [
    { id: "root", position: { x: 0, y: 0 } },
    { id: "a", position: { x: 300, y: -50 } },
    { id: "b", position: { x: 300, y: 50 } },
    { id: "a1", position: { x: 600, y: -50 } }
  ],
  edges: [
    { source: "root", target: "a" },
    { source: "root", target: "b" },
    { source: "a", target: "a1" }
  ]
}
```

### Visual Result

```
     root (0,0)
        |
    ┌───┴───┐
    |       |
   a       b
(300,-50) (300,50)
   |
  a1
(600,-50)
```
