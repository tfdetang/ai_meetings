# Mind Map Transformation - Quick Start Guide

## 5-Minute Integration Guide

### Step 1: Import the Utilities

```javascript
import { transformMindMapToReactFlow } from './utils/mindMapTransform';
```

### Step 2: Transform Your Data

```javascript
// Assuming you have mind map data from your backend
const { nodes, edges } = transformMindMapToReactFlow(mindMapData);
```

### Step 3: Use with React Flow

```javascript
import ReactFlow from 'reactflow';
import 'reactflow/dist/style.css';

function MindMapViewer({ mindMapData }) {
  const { nodes, edges } = transformMindMapToReactFlow(mindMapData);
  
  return (
    <div style={{ width: '100%', height: '600px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
      />
    </div>
  );
}
```

That's it! Your mind map is now rendered.

## Common Use Cases

### 1. Fetch and Display Mind Map

```javascript
import { useEffect, useState } from 'react';
import { transformMindMapToReactFlow } from './utils/mindMapTransform';

function MindMapContainer({ meetingId }) {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);

  useEffect(() => {
    async function loadMindMap() {
      const response = await fetch(`/api/meetings/${meetingId}/mind-map`);
      const mindMapData = await response.json();
      
      const { nodes, edges } = transformMindMapToReactFlow(mindMapData);
      setNodes(nodes);
      setEdges(edges);
    }
    
    loadMindMap();
  }, [meetingId]);

  return <ReactFlow nodes={nodes} edges={edges} fitView />;
}
```

### 2. Add Node Click Handler

```javascript
function MindMapViewer({ mindMapData }) {
  const { nodes, edges } = transformMindMapToReactFlow(mindMapData);
  
  const handleNodeClick = (event, node) => {
    console.log('Clicked node:', node.data.label);
    console.log('Message references:', node.data.messageReferences);
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

### 3. Show Node Details on Hover

```javascript
import { useState } from 'react';

function MindMapViewer({ mindMapData }) {
  const { nodes, edges } = transformMindMapToReactFlow(mindMapData);
  const [hoveredNode, setHoveredNode] = useState(null);

  return (
    <div style={{ position: 'relative', width: '100%', height: '600px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodeMouseEnter={(event, node) => setHoveredNode(node)}
        onNodeMouseLeave={() => setHoveredNode(null)}
        fitView
      />
      
      {hoveredNode && (
        <div style={{
          position: 'absolute',
          top: 10,
          right: 10,
          background: 'white',
          padding: '10px',
          borderRadius: '4px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
        }}>
          <h4>{hoveredNode.data.label}</h4>
          <p>Level: {hoveredNode.data.level}</p>
          <p>Messages: {hoveredNode.data.messageReferences.length}</p>
        </div>
      )}
    </div>
  );
}
```

### 4. Recalculate Layout After Changes

```javascript
import { recalculateLayout } from './utils/mindMapTransform';

function MindMapViewer({ mindMapData }) {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);

  useEffect(() => {
    const { nodes, edges } = transformMindMapToReactFlow(mindMapData);
    setNodes(nodes);
    setEdges(edges);
  }, [mindMapData]);

  const handleRefresh = () => {
    // Recalculate positions
    const updatedNodes = recalculateLayout(nodes, mindMapData);
    setNodes(updatedNodes);
  };

  return (
    <>
      <button onClick={handleRefresh}>Refresh Layout</button>
      <ReactFlow nodes={nodes} edges={edges} fitView />
    </>
  );
}
```

## API Quick Reference

### `transformMindMapToReactFlow(mindMap)`
**Input:** Backend MindMap object  
**Output:** `{ nodes: Array, edges: Array }`  
**Use:** One-step transformation

### `convertToReactFlowNodes(mindMap)`
**Input:** Backend MindMap object  
**Output:** Array of React Flow nodes  
**Use:** When you only need nodes

### `convertToReactFlowEdges(mindMap)`
**Input:** Backend MindMap object  
**Output:** Array of React Flow edges  
**Use:** When you only need edges

### `recalculateLayout(nodes, mindMap)`
**Input:** Current nodes array, MindMap object  
**Output:** Updated nodes array with new positions  
**Use:** After expand/collapse or other layout changes

## Troubleshooting

### Problem: Nodes overlap
**Solution:** Adjust spacing constants in the layout algorithm or use React Flow's auto-layout features.

### Problem: Mind map doesn't fit in view
**Solution:** Use the `fitView` prop on ReactFlow component.

### Problem: Can't see edges
**Solution:** Make sure you're importing React Flow's CSS: `import 'reactflow/dist/style.css'`

### Problem: Nodes don't update
**Solution:** Make sure you're using state management (useState) and updating when data changes.

## Best Practices

1. **Memoize transformations** to avoid unnecessary recalculations:
   ```javascript
   const { nodes, edges } = useMemo(
     () => transformMindMapToReactFlow(mindMapData),
     [mindMapData]
   );
   ```

2. **Handle loading states**:
   ```javascript
   if (!mindMapData) return <Spin />;
   ```

3. **Add error boundaries** for production:
   ```javascript
   <ErrorBoundary>
     <MindMapViewer mindMapData={data} />
   </ErrorBoundary>
   ```

4. **Use React Flow controls** for better UX:
   ```javascript
   import { Controls, Background } from 'reactflow';
   
   <ReactFlow nodes={nodes} edges={edges}>
     <Background />
     <Controls />
   </ReactFlow>
   ```

## Need More Help?

- See `README.md` for complete documentation
- Check `mindMapTransform.demo.js` for more examples
- Run `node mindMapTransform.verify.js` to test the utilities
- Look at `MindMapExample.jsx` for a complete component example
