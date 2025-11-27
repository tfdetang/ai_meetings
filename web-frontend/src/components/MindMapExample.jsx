/**
 * Example component demonstrating mind map transformation
 * This shows how to use the transformation utilities with React Flow
 * 
 * Note: This is an example component. React Flow needs to be installed first:
 * npm install reactflow
 */

import React, { useEffect, useState } from 'react';
import { transformMindMapToReactFlow } from '../utils/mindMapTransform';

// Example mind map data
const exampleMindMap = {
  id: 'mindmap-example',
  meeting_id: 'meeting-1',
  root_node: {
    id: 'root',
    content: 'Project Discussion',
    level: 0,
    parent_id: null,
    children_ids: ['node-1', 'node-2', 'node-3'],
    message_references: [],
    metadata: {}
  },
  nodes: {
    'root': {
      id: 'root',
      content: 'Project Discussion',
      level: 0,
      parent_id: null,
      children_ids: ['node-1', 'node-2', 'node-3'],
      message_references: [],
      metadata: {}
    },
    'node-1': {
      id: 'node-1',
      content: 'Technical Requirements',
      level: 1,
      parent_id: 'root',
      children_ids: ['node-1-1'],
      message_references: ['msg-1'],
      metadata: {}
    },
    'node-2': {
      id: 'node-2',
      content: 'Timeline',
      level: 1,
      parent_id: 'root',
      children_ids: [],
      message_references: ['msg-2'],
      metadata: {}
    },
    'node-3': {
      id: 'node-3',
      content: 'Resources',
      level: 1,
      parent_id: 'root',
      children_ids: [],
      message_references: ['msg-3'],
      metadata: {}
    },
    'node-1-1': {
      id: 'node-1-1',
      content: 'API Design',
      level: 2,
      parent_id: 'node-1',
      children_ids: [],
      message_references: ['msg-4'],
      metadata: {}
    }
  },
  created_at: '2024-01-01T00:00:00',
  created_by: 'user-1',
  version: 1
};

/**
 * Example component showing transformation output
 */
function MindMapExample() {
  const [transformedData, setTransformedData] = useState(null);

  useEffect(() => {
    // Transform the mind map data
    const result = transformMindMapToReactFlow(exampleMindMap);
    setTransformedData(result);
  }, []);

  if (!transformedData) {
    return <div>Loading...</div>;
  }

  return (
    <div style={{ padding: '20px' }}>
      <h2>Mind Map Transformation Example</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <h3>Transformation Results:</h3>
        <p>Total Nodes: {transformedData.nodes.length}</p>
        <p>Total Edges: {transformedData.edges.length}</p>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Nodes:</h3>
        <pre style={{ 
          background: '#f5f5f5', 
          padding: '10px', 
          borderRadius: '4px',
          overflow: 'auto',
          maxHeight: '300px'
        }}>
          {JSON.stringify(transformedData.nodes, null, 2)}
        </pre>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Edges:</h3>
        <pre style={{ 
          background: '#f5f5f5', 
          padding: '10px', 
          borderRadius: '4px',
          overflow: 'auto',
          maxHeight: '300px'
        }}>
          {JSON.stringify(transformedData.edges, null, 2)}
        </pre>
      </div>

      <div style={{ marginTop: '20px', padding: '10px', background: '#e6f7ff', borderRadius: '4px' }}>
        <h4>Next Steps:</h4>
        <ol>
          <li>Install React Flow: <code>npm install reactflow</code></li>
          <li>Import ReactFlow component</li>
          <li>Pass the transformed nodes and edges to ReactFlow</li>
          <li>Add interaction handlers (click, hover, etc.)</li>
        </ol>
      </div>
    </div>
  );
}

export default MindMapExample;

/**
 * Example of actual React Flow integration (requires reactflow package)
 * 
 * import ReactFlow, { Background, Controls } from 'reactflow';
 * import 'reactflow/dist/style.css';
 * 
 * function MindMapViewer({ mindMapData }) {
 *   const [nodes, setNodes] = useState([]);
 *   const [edges, setEdges] = useState([]);
 * 
 *   useEffect(() => {
 *     if (mindMapData) {
 *       const { nodes, edges } = transformMindMapToReactFlow(mindMapData);
 *       setNodes(nodes);
 *       setEdges(edges);
 *     }
 *   }, [mindMapData]);
 * 
 *   return (
 *     <div style={{ width: '100%', height: '600px' }}>
 *       <ReactFlow
 *         nodes={nodes}
 *         edges={edges}
 *         fitView
 *         attributionPosition="bottom-left"
 *       >
 *         <Background />
 *         <Controls />
 *       </ReactFlow>
 *     </div>
 *   );
 * }
 */
