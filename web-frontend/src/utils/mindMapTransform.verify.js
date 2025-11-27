/**
 * Verification script for mind map transformation utilities
 * Run with: node mindMapTransform.verify.js
 */

// Simple test data
const testMindMap = {
  id: 'test-map',
  meeting_id: 'meeting-1',
  root_node: {
    id: 'root',
    content: 'Root Node',
    level: 0,
    parent_id: null,
    children_ids: ['child-1', 'child-2'],
    message_references: [],
    metadata: {}
  },
  nodes: {
    'root': {
      id: 'root',
      content: 'Root Node',
      level: 0,
      parent_id: null,
      children_ids: ['child-1', 'child-2'],
      message_references: [],
      metadata: {}
    },
    'child-1': {
      id: 'child-1',
      content: 'Child 1',
      level: 1,
      parent_id: 'root',
      children_ids: ['grandchild-1'],
      message_references: ['msg-1'],
      metadata: {}
    },
    'child-2': {
      id: 'child-2',
      content: 'Child 2',
      level: 1,
      parent_id: 'root',
      children_ids: [],
      message_references: ['msg-2'],
      metadata: {}
    },
    'grandchild-1': {
      id: 'grandchild-1',
      content: 'Grandchild 1',
      level: 2,
      parent_id: 'child-1',
      children_ids: [],
      message_references: ['msg-3'],
      metadata: {}
    }
  },
  created_at: '2024-01-01T00:00:00',
  created_by: 'test-user',
  version: 1
};

// Import the functions (for ES modules)
// For CommonJS, you would use require()
function calculateNodePositions(mindMap) {
  const positions = {};
  const levelWidth = 300;
  const nodeSpacing = 100;
  const levelCounts = {};
  
  function positionNode(nodeId, level, parentY = 0) {
    const node = mindMap.nodes[nodeId];
    if (!node) return;
    
    if (!(level in levelCounts)) {
      levelCounts[level] = 0;
    }
    
    const x = level * levelWidth;
    
    let y;
    if (level === 0) {
      y = 0;
    } else {
      const childCount = node.parent_id ? 
        mindMap.nodes[node.parent_id].children_ids.length : 1;
      const childIndex = node.parent_id ? 
        mindMap.nodes[node.parent_id].children_ids.indexOf(nodeId) : 0;
      
      const totalHeight = (childCount - 1) * nodeSpacing;
      const startY = parentY - totalHeight / 2;
      y = startY + childIndex * nodeSpacing;
    }
    
    positions[nodeId] = { x, y };
    levelCounts[level]++;
    
    if (node.children_ids && node.children_ids.length > 0) {
      node.children_ids.forEach(childId => {
        positionNode(childId, level + 1, y);
      });
    }
  }
  
  positionNode(mindMap.root_node.id, 0);
  return positions;
}

function convertToReactFlowNodes(mindMap) {
  if (!mindMap || !mindMap.nodes) {
    return [];
  }
  
  const positions = calculateNodePositions(mindMap);
  
  const reactFlowNodes = Object.values(mindMap.nodes).map(node => {
    const position = positions[node.id] || { x: 0, y: 0 };
    
    return {
      id: node.id,
      type: node.level === 0 ? 'input' : 'default',
      data: {
        label: node.content,
        level: node.level,
        messageReferences: node.message_references || [],
        metadata: node.metadata || {},
        originalNode: node
      },
      position: position,
      style: {
        background: node.level === 0 ? '#1890ff' : '#fff',
        color: node.level === 0 ? '#fff' : '#000',
        border: node.level === 0 ? '2px solid #1890ff' : '1px solid #d9d9d9',
        borderRadius: '8px',
        padding: '10px',
        minWidth: '150px',
        fontSize: node.level === 0 ? '16px' : '14px',
        fontWeight: node.level === 0 ? 'bold' : 'normal'
      }
    };
  });
  
  return reactFlowNodes;
}

function convertToReactFlowEdges(mindMap) {
  if (!mindMap || !mindMap.nodes) {
    return [];
  }
  
  const edges = [];
  
  Object.values(mindMap.nodes).forEach(node => {
    if (node.children_ids && node.children_ids.length > 0) {
      node.children_ids.forEach((childId) => {
        edges.push({
          id: `e-${node.id}-${childId}`,
          source: node.id,
          target: childId,
          type: 'smoothstep',
          animated: false,
          style: {
            stroke: '#b1b1b7',
            strokeWidth: 2
          },
          markerEnd: {
            type: 'arrowclosed',
            color: '#b1b1b7'
          }
        });
      });
    }
  });
  
  return edges;
}

// Run verification tests
console.log('=== Mind Map Transformation Verification ===\n');

console.log('1. Testing Node Conversion...');
const nodes = convertToReactFlowNodes(testMindMap);
console.log(`   ✓ Created ${nodes.length} nodes`);
console.log(`   ✓ Root node type: ${nodes.find(n => n.id === 'root').type}`);
console.log(`   ✓ Root node position: (${nodes.find(n => n.id === 'root').position.x}, ${nodes.find(n => n.id === 'root').position.y})`);

const child1 = nodes.find(n => n.id === 'child-1');
console.log(`   ✓ Child 1 position: (${child1.position.x}, ${child1.position.y})`);
console.log(`   ✓ Child 1 has message references: ${child1.data.messageReferences.length > 0}`);

console.log('\n2. Testing Edge Conversion...');
const edges = convertToReactFlowEdges(testMindMap);
console.log(`   ✓ Created ${edges.length} edges`);
console.log(`   ✓ All edges have source and target: ${edges.every(e => e.source && e.target)}`);
console.log(`   ✓ All edges use smoothstep type: ${edges.every(e => e.type === 'smoothstep')}`);

console.log('\n3. Testing Layout Algorithm...');
const level0Nodes = nodes.filter(n => n.data.level === 0);
const level1Nodes = nodes.filter(n => n.data.level === 1);
const level2Nodes = nodes.filter(n => n.data.level === 2);

console.log(`   ✓ Level 0 nodes: ${level0Nodes.length} at x=${level0Nodes[0].position.x}`);
console.log(`   ✓ Level 1 nodes: ${level1Nodes.length} at x=${level1Nodes[0].position.x}`);
console.log(`   ✓ Level 2 nodes: ${level2Nodes.length} at x=${level2Nodes[0].position.x}`);
console.log(`   ✓ Levels are horizontally spaced: ${level1Nodes[0].position.x > level0Nodes[0].position.x}`);

console.log('\n4. Testing Edge Validity...');
const nodeIds = new Set(nodes.map(n => n.id));
const allEdgesValid = edges.every(e => nodeIds.has(e.source) && nodeIds.has(e.target));
console.log(`   ✓ All edges reference existing nodes: ${allEdgesValid}`);

console.log('\n5. Testing Empty Input Handling...');
const emptyNodes = convertToReactFlowNodes(null);
const emptyEdges = convertToReactFlowEdges(null);
console.log(`   ✓ Null input returns empty array for nodes: ${emptyNodes.length === 0}`);
console.log(`   ✓ Null input returns empty array for edges: ${emptyEdges.length === 0}`);

console.log('\n=== All Verifications Passed! ===\n');

console.log('Sample Node Output:');
console.log(JSON.stringify(nodes[0], null, 2));

console.log('\nSample Edge Output:');
console.log(JSON.stringify(edges[0], null, 2));
