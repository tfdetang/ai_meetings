/**
 * Mind Map Data Transformation Utilities
 * Converts backend MindMap data to React Flow format
 */

/**
 * Calculate node positions using a tree layout algorithm
 * Uses a hierarchical layout with horizontal spacing between siblings
 * and vertical spacing between levels
 * 
 * @param {Object} mindMap - The mind map data from backend
 * @returns {Object} - Map of node_id to {x, y} positions
 */
function calculateNodePositions(mindMap) {
  const positions = {};
  const levelWidth = 350; // Horizontal spacing between levels
  const nodeSpacing = 120; // Vertical spacing between nodes at same level
  
  /**
   * Calculate the height (vertical space) needed for a subtree
   * @param {string} nodeId - The node ID
   * @returns {number} - Height needed for this subtree
   */
  function calculateSubtreeHeight(nodeId) {
    const node = mindMap.nodes[nodeId];
    if (!node || !node.children_ids || node.children_ids.length === 0) {
      return nodeSpacing; // Leaf node takes one unit of space
    }
    
    // Sum up heights of all children
    let totalHeight = 0;
    node.children_ids.forEach(childId => {
      totalHeight += calculateSubtreeHeight(childId);
    });
    
    return Math.max(totalHeight, nodeSpacing);
  }
  
  /**
   * Recursively calculate positions for a node and its children
   * @param {string} nodeId - The node ID to position
   * @param {number} level - The depth level (0 for root)
   * @param {number} startY - The starting Y position for this subtree
   * @returns {number} - The center Y position of this node
   */
  function positionNode(nodeId, level, startY) {
    const node = mindMap.nodes[nodeId];
    if (!node) return startY;
    
    // Calculate X position based on level
    const x = level * levelWidth;
    
    // If node has children, position them first and center this node among them
    if (node.children_ids && node.children_ids.length > 0) {
      let currentY = startY;
      const childYPositions = [];
      
      // Position each child
      node.children_ids.forEach(childId => {
        const childHeight = calculateSubtreeHeight(childId);
        const childCenterY = positionNode(childId, level + 1, currentY);
        childYPositions.push(childCenterY);
        currentY += childHeight;
      });
      
      // Center this node among its children
      const firstChildY = childYPositions[0];
      const lastChildY = childYPositions[childYPositions.length - 1];
      const y = (firstChildY + lastChildY) / 2;
      
      positions[nodeId] = { x, y };
      return y;
    } else {
      // Leaf node - position at the center of its allocated space
      const y = startY + nodeSpacing / 2;
      positions[nodeId] = { x, y };
      return y;
    }
  }
  
  // Calculate total height needed
  const totalHeight = calculateSubtreeHeight(mindMap.root_node.id);
  
  // Start positioning from root node at top-left (0, 0)
  // This ensures the mind map starts from the left side
  positionNode(mindMap.root_node.id, 0, 0);
  
  return positions;
}

/**
 * Convert MindMap data to React Flow nodes
 * 
 * @param {Object} mindMap - The mind map data from backend
 * @returns {Array} - Array of React Flow node objects
 */
export function convertToReactFlowNodes(mindMap) {
  if (!mindMap || !mindMap.nodes) {
    return [];
  }
  
  // Calculate positions for all nodes
  const positions = calculateNodePositions(mindMap);
  
  // Convert each node to React Flow format
  const reactFlowNodes = Object.values(mindMap.nodes).map(node => {
    const position = positions[node.id] || { x: 0, y: 0 };
    const hasChildren = node.children_ids && node.children_ids.length > 0;
    const hasParent = node.parent_id !== null && node.parent_id !== undefined;
    
    return {
      id: node.id,
      type: 'default', // Use default type for all nodes
      data: {
        label: node.content,
        level: node.level,
        messageReferences: node.message_references || [],
        metadata: node.metadata || {},
        // Store original node data for reference
        originalNode: node
      },
      position: position,
      // Configure source and target handles for horizontal layout
      sourcePosition: 'right',  // Connections go out from the right
      targetPosition: 'left',   // Connections come in from the left
      // Style based on level
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

/**
 * Convert node relationships to React Flow edges
 * 
 * @param {Object} mindMap - The mind map data from backend
 * @returns {Array} - Array of React Flow edge objects
 */
export function convertToReactFlowEdges(mindMap) {
  if (!mindMap || !mindMap.nodes) {
    return [];
  }
  
  const edges = [];
  
  // Iterate through all nodes and create edges from parent to children
  Object.values(mindMap.nodes).forEach(node => {
    if (node.children_ids && node.children_ids.length > 0) {
      node.children_ids.forEach((childId, index) => {
        edges.push({
          id: `e-${node.id}-${childId}`,
          source: node.id,
          target: childId,
          sourceHandle: 'right', // Connect from right side of source
          targetHandle: 'left',  // Connect to left side of target
          type: 'smoothstep', // Use smoothstep for better horizontal flow
          animated: false,
          style: {
            stroke: '#b1b1b7',
            strokeWidth: 2
          },
          // Add arrow marker
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

/**
 * Transform complete MindMap data to React Flow format
 * This is a convenience function that combines node and edge conversion
 * 
 * @param {Object} mindMap - The mind map data from backend
 * @returns {Object} - Object with nodes and edges arrays
 */
export function transformMindMapToReactFlow(mindMap) {
  return {
    nodes: convertToReactFlowNodes(mindMap),
    edges: convertToReactFlowEdges(mindMap)
  };
}

/**
 * Recalculate layout for existing React Flow nodes
 * Useful when nodes need to be repositioned after expand/collapse
 * 
 * @param {Array} nodes - Current React Flow nodes
 * @param {Object} mindMap - The mind map data from backend
 * @returns {Array} - Updated nodes with new positions
 */
export function recalculateLayout(nodes, mindMap) {
  const positions = calculateNodePositions(mindMap);
  
  return nodes.map(node => ({
    ...node,
    position: positions[node.id] || node.position
  }));
}

/**
 * Filter nodes and edges based on expanded state
 * Only shows nodes that are expanded or whose parents are expanded
 * 
 * @param {Object} mindMap - The mind map data from backend
 * @param {Set} expandedNodes - Set of node IDs that are expanded
 * @returns {Object} - Object with filtered nodes and edges
 */
export function filterByExpandedState(mindMap, expandedNodes) {
  if (!mindMap || !mindMap.nodes) {
    return { nodes: [], edges: [] };
  }

  const visibleNodeIds = new Set();
  
  /**
   * Recursively determine which nodes should be visible
   * @param {string} nodeId - The node ID to check
   * @param {boolean} parentExpanded - Whether the parent is expanded
   */
  function checkVisibility(nodeId, parentExpanded = true) {
    const node = mindMap.nodes[nodeId];
    if (!node) return;
    
    // Node is visible if parent is expanded (or it's the root)
    if (parentExpanded || node.level === 0) {
      visibleNodeIds.add(nodeId);
      
      // Check children only if this node is expanded
      const isExpanded = expandedNodes.has(nodeId);
      if (node.children_ids && node.children_ids.length > 0) {
        node.children_ids.forEach(childId => {
          checkVisibility(childId, isExpanded);
        });
      }
    }
  }
  
  // Start from root node
  checkVisibility(mindMap.root_node.id, true);
  
  // Convert to React Flow format, filtering by visibility
  const { nodes, edges } = transformMindMapToReactFlow(mindMap);
  
  const visibleNodes = nodes.filter(node => visibleNodeIds.has(node.id));
  const visibleEdges = edges.filter(edge => 
    visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)
  );
  
  return { nodes: visibleNodes, edges: visibleEdges };
}

/**
 * Get all ancestor node IDs for a given node
 * Useful for expanding the path to a specific node
 * 
 * @param {Object} mindMap - The mind map data from backend
 * @param {string} nodeId - The node ID to find ancestors for
 * @returns {Array} - Array of ancestor node IDs (including the node itself)
 */
export function getAncestorPath(mindMap, nodeId) {
  const path = [];
  let currentNode = mindMap.nodes[nodeId];
  
  while (currentNode) {
    path.unshift(currentNode.id);
    if (currentNode.parent_id) {
      currentNode = mindMap.nodes[currentNode.parent_id];
    } else {
      break;
    }
  }
  
  return path;
}

/**
 * Search nodes by keyword and return matching node IDs
 * 
 * @param {Object} mindMap - The mind map data from backend
 * @param {string} keyword - Search keyword
 * @returns {Array} - Array of matching node IDs
 */
export function searchNodes(mindMap, keyword) {
  if (!mindMap || !keyword) {
    return [];
  }
  
  const lowerKeyword = keyword.toLowerCase();
  const matchingIds = [];
  
  Object.values(mindMap.nodes).forEach(node => {
    if (node.content.toLowerCase().includes(lowerKeyword)) {
      matchingIds.push(node.id);
    }
  });
  
  return matchingIds;
}
