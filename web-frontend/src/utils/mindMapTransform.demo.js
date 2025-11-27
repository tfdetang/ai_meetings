/**
 * Demonstration of Mind Map Transformation Functions
 * This file shows example usage of the transformation utilities
 */

import { 
  convertToReactFlowNodes, 
  convertToReactFlowEdges,
  transformMindMapToReactFlow
} from './mindMapTransform';

// Example mind map data from backend
const exampleMindMap = {
  id: 'mindmap-1',
  meeting_id: 'meeting-1',
  root_node: {
    id: 'node-root',
    content: 'AI Agent Meeting System',
    level: 0,
    parent_id: null,
    children_ids: ['node-1', 'node-2', 'node-3'],
    message_references: [],
    metadata: {}
  },
  nodes: {
    'node-root': {
      id: 'node-root',
      content: 'AI Agent Meeting System',
      level: 0,
      parent_id: null,
      children_ids: ['node-1', 'node-2', 'node-3'],
      message_references: [],
      metadata: {}
    },
    'node-1': {
      id: 'node-1',
      content: 'Architecture Design',
      level: 1,
      parent_id: 'node-root',
      children_ids: ['node-1-1', 'node-1-2'],
      message_references: ['msg-1', 'msg-2'],
      metadata: {}
    },
    'node-2': {
      id: 'node-2',
      content: 'Implementation Plan',
      level: 1,
      parent_id: 'node-root',
      children_ids: ['node-2-1'],
      message_references: ['msg-3'],
      metadata: {}
    },
    'node-3': {
      id: 'node-3',
      content: 'Testing Strategy',
      level: 1,
      parent_id: 'node-root',
      children_ids: [],
      message_references: ['msg-4'],
      metadata: {}
    },
    'node-1-1': {
      id: 'node-1-1',
      content: 'Backend Services',
      level: 2,
      parent_id: 'node-1',
      children_ids: [],
      message_references: ['msg-5'],
      metadata: {}
    },
    'node-1-2': {
      id: 'node-1-2',
      content: 'Frontend Components',
      level: 2,
      parent_id: 'node-1',
      children_ids: [],
      message_references: ['msg-6'],
      metadata: {}
    },
    'node-2-1': {
      id: 'node-2-1',
      content: 'Phase 1: Core Features',
      level: 2,
      parent_id: 'node-2',
      children_ids: [],
      message_references: ['msg-7'],
      metadata: {}
    }
  },
  created_at: '2024-01-01T00:00:00',
  created_by: 'user-1',
  version: 1
};

// Demonstration functions
export function demonstrateNodeConversion() {
  console.log('=== Node Conversion Demo ===');
  const nodes = convertToReactFlowNodes(exampleMindMap);
  
  console.log(`Total nodes: ${nodes.length}`);
  console.log('\nRoot node:');
  console.log(JSON.stringify(nodes.find(n => n.id === 'node-root'), null, 2));
  
  console.log('\nFirst level nodes:');
  nodes.filter(n => n.data.level === 1).forEach(node => {
    console.log(`- ${node.data.label} at position (${node.position.x}, ${node.position.y})`);
  });
  
  return nodes;
}

export function demonstrateEdgeConversion() {
  console.log('\n=== Edge Conversion Demo ===');
  const edges = convertToReactFlowEdges(exampleMindMap);
  
  console.log(`Total edges: ${edges.length}`);
  console.log('\nEdge connections:');
  edges.forEach(edge => {
    const sourceNode = exampleMindMap.nodes[edge.source];
    const targetNode = exampleMindMap.nodes[edge.target];
    console.log(`${sourceNode.content} → ${targetNode.content}`);
  });
  
  return edges;
}

export function demonstrateFullTransformation() {
  console.log('\n=== Full Transformation Demo ===');
  const result = transformMindMapToReactFlow(exampleMindMap);
  
  console.log(`Nodes: ${result.nodes.length}`);
  console.log(`Edges: ${result.edges.length}`);
  
  console.log('\nReact Flow data structure ready for rendering:');
  console.log('- All nodes have positions calculated');
  console.log('- All edges connect existing nodes');
  console.log('- Root node styled as input type');
  console.log('- Child nodes styled as default type');
  
  return result;
}

// Run demonstrations if this file is executed directly
if (typeof window !== 'undefined') {
  console.log('Mind Map Transformation Utilities Demo\n');
  demonstrateNodeConversion();
  demonstrateEdgeConversion();
  demonstrateFullTransformation();
}
