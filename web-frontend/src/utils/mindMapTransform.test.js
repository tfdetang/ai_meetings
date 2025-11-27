/**
 * Tests for Mind Map Transformation Utilities
 */

import { 
  convertToReactFlowNodes, 
  convertToReactFlowEdges,
  transformMindMapToReactFlow,
  recalculateLayout
} from './mindMapTransform';

describe('Mind Map Transformation', () => {
  // Sample mind map data matching backend structure
  const sampleMindMap = {
    id: 'mindmap-1',
    meeting_id: 'meeting-1',
    root_node: {
      id: 'node-root',
      content: 'Project Planning Meeting',
      level: 0,
      parent_id: null,
      children_ids: ['node-1', 'node-2', 'node-3'],
      message_references: [],
      metadata: {}
    },
    nodes: {
      'node-root': {
        id: 'node-root',
        content: 'Project Planning Meeting',
        level: 0,
        parent_id: null,
        children_ids: ['node-1', 'node-2', 'node-3'],
        message_references: [],
        metadata: {}
      },
      'node-1': {
        id: 'node-1',
        content: 'Technical Architecture',
        level: 1,
        parent_id: 'node-root',
        children_ids: ['node-1-1', 'node-1-2'],
        message_references: ['msg-1', 'msg-2'],
        metadata: {}
      },
      'node-2': {
        id: 'node-2',
        content: 'Timeline and Milestones',
        level: 1,
        parent_id: 'node-root',
        children_ids: [],
        message_references: ['msg-3'],
        metadata: {}
      },
      'node-3': {
        id: 'node-3',
        content: 'Resource Allocation',
        level: 1,
        parent_id: 'node-root',
        children_ids: ['node-3-1'],
        message_references: ['msg-4', 'msg-5'],
        metadata: {}
      },
      'node-1-1': {
        id: 'node-1-1',
        content: 'Backend Services',
        level: 2,
        parent_id: 'node-1',
        children_ids: [],
        message_references: ['msg-6'],
        metadata: {}
      },
      'node-1-2': {
        id: 'node-1-2',
        content: 'Frontend Components',
        level: 2,
        parent_id: 'node-1',
        children_ids: [],
        message_references: ['msg-7'],
        metadata: {}
      },
      'node-3-1': {
        id: 'node-3-1',
        content: 'Team Assignments',
        level: 2,
        parent_id: 'node-3',
        children_ids: [],
        message_references: ['msg-8'],
        metadata: {}
      }
    },
    created_at: '2024-01-01T00:00:00',
    created_by: 'user-1',
    version: 1
  };

  describe('convertToReactFlowNodes', () => {
    test('should convert all nodes to React Flow format', () => {
      const nodes = convertToReactFlowNodes(sampleMindMap);
      
      expect(nodes).toHaveLength(7);
      expect(nodes.every(node => node.id && node.position && node.data)).toBe(true);
    });

    test('should set root node as input type', () => {
      const nodes = convertToReactFlowNodes(sampleMindMap);
      const rootNode = nodes.find(n => n.id === 'node-root');
      
      expect(rootNode.type).toBe('input');
    });

    test('should set non-root nodes as default type', () => {
      const nodes = convertToReactFlowNodes(sampleMindMap);
      const childNodes = nodes.filter(n => n.id !== 'node-root');
      
      expect(childNodes.every(n => n.type === 'default')).toBe(true);
    });

    test('should include node data in data property', () => {
      const nodes = convertToReactFlowNodes(sampleMindMap);
      const node1 = nodes.find(n => n.id === 'node-1');
      
      expect(node1.data.label).toBe('Technical Architecture');
      expect(node1.data.level).toBe(1);
      expect(node1.data.messageReferences).toEqual(['msg-1', 'msg-2']);
    });

    test('should calculate positions for all nodes', () => {
      const nodes = convertToReactFlowNodes(sampleMindMap);
      
      expect(nodes.every(node => 
        typeof node.position.x === 'number' && 
        typeof node.position.y === 'number'
      )).toBe(true);
    });

    test('should position root node at level 0', () => {
      const nodes = convertToReactFlowNodes(sampleMindMap);
      const rootNode = nodes.find(n => n.id === 'node-root');
      
      expect(rootNode.position.x).toBe(0);
    });

    test('should handle empty mind map', () => {
      const nodes = convertToReactFlowNodes(null);
      expect(nodes).toEqual([]);
    });
  });

  describe('convertToReactFlowEdges', () => {
    test('should create edges for all parent-child relationships', () => {
      const edges = convertToReactFlowEdges(sampleMindMap);
      
      // Root has 3 children, node-1 has 2 children, node-3 has 1 child = 6 edges
      expect(edges).toHaveLength(6);
    });

    test('should create edges with correct source and target', () => {
      const edges = convertToReactFlowEdges(sampleMindMap);
      const rootEdges = edges.filter(e => e.source === 'node-root');
      
      expect(rootEdges).toHaveLength(3);
      expect(rootEdges.map(e => e.target).sort()).toEqual(['node-1', 'node-2', 'node-3']);
    });

    test('should use smoothstep edge type', () => {
      const edges = convertToReactFlowEdges(sampleMindMap);
      
      expect(edges.every(e => e.type === 'smoothstep')).toBe(true);
    });

    test('should include arrow markers', () => {
      const edges = convertToReactFlowEdges(sampleMindMap);
      
      expect(edges.every(e => e.markerEnd && e.markerEnd.type === 'arrowclosed')).toBe(true);
    });

    test('should handle nodes with no children', () => {
      const edges = convertToReactFlowEdges(sampleMindMap);
      const leafNodeEdges = edges.filter(e => e.source === 'node-2');
      
      expect(leafNodeEdges).toHaveLength(0);
    });

    test('should handle empty mind map', () => {
      const edges = convertToReactFlowEdges(null);
      expect(edges).toEqual([]);
    });
  });

  describe('transformMindMapToReactFlow', () => {
    test('should return both nodes and edges', () => {
      const result = transformMindMapToReactFlow(sampleMindMap);
      
      expect(result).toHaveProperty('nodes');
      expect(result).toHaveProperty('edges');
      expect(Array.isArray(result.nodes)).toBe(true);
      expect(Array.isArray(result.edges)).toBe(true);
    });

    test('should have matching node and edge counts', () => {
      const result = transformMindMapToReactFlow(sampleMindMap);
      
      expect(result.nodes).toHaveLength(7);
      expect(result.edges).toHaveLength(6);
    });

    test('should create valid React Flow data structure', () => {
      const result = transformMindMapToReactFlow(sampleMindMap);
      
      // Verify all edges reference existing nodes
      const nodeIds = new Set(result.nodes.map(n => n.id));
      const allEdgesValid = result.edges.every(e => 
        nodeIds.has(e.source) && nodeIds.has(e.target)
      );
      
      expect(allEdgesValid).toBe(true);
    });
  });

  describe('recalculateLayout', () => {
    test('should update node positions', () => {
      const initialNodes = convertToReactFlowNodes(sampleMindMap);
      const updatedNodes = recalculateLayout(initialNodes, sampleMindMap);
      
      expect(updatedNodes).toHaveLength(initialNodes.length);
      expect(updatedNodes.every(n => n.position)).toBe(true);
    });

    test('should preserve node data', () => {
      const initialNodes = convertToReactFlowNodes(sampleMindMap);
      const updatedNodes = recalculateLayout(initialNodes, sampleMindMap);
      
      const initialNode1 = initialNodes.find(n => n.id === 'node-1');
      const updatedNode1 = updatedNodes.find(n => n.id === 'node-1');
      
      expect(updatedNode1.data).toEqual(initialNode1.data);
    });
  });

  describe('Tree Layout Algorithm', () => {
    test('should position nodes at different levels horizontally', () => {
      const nodes = convertToReactFlowNodes(sampleMindMap);
      
      const level0Nodes = nodes.filter(n => n.data.level === 0);
      const level1Nodes = nodes.filter(n => n.data.level === 1);
      const level2Nodes = nodes.filter(n => n.data.level === 2);
      
      // All nodes at same level should have same X coordinate
      const level0X = level0Nodes[0].position.x;
      const level1X = level1Nodes[0].position.x;
      const level2X = level2Nodes[0].position.x;
      
      expect(level0Nodes.every(n => n.position.x === level0X)).toBe(true);
      expect(level1Nodes.every(n => n.position.x === level1X)).toBe(true);
      expect(level2Nodes.every(n => n.position.x === level2X)).toBe(true);
      
      // Each level should be further right
      expect(level1X).toBeGreaterThan(level0X);
      expect(level2X).toBeGreaterThan(level1X);
    });

    test('should distribute sibling nodes vertically', () => {
      const nodes = convertToReactFlowNodes(sampleMindMap);
      
      // Get the three children of root
      const rootChildren = nodes.filter(n => 
        ['node-1', 'node-2', 'node-3'].includes(n.id)
      );
      
      // They should have different Y positions
      const yPositions = rootChildren.map(n => n.position.y);
      const uniqueYPositions = new Set(yPositions);
      
      expect(uniqueYPositions.size).toBe(3);
    });
  });
});
