/**
 * MindMapViewer Component
 * Interactive mind map visualization using React Flow
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  Panel
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Button, Space, Input, Tooltip, Tag, message, Dropdown } from 'antd';
import {
  ZoomInOutlined,
  ZoomOutOutlined,
  ExpandOutlined,
  CompressOutlined,
  DownloadOutlined,
  SearchOutlined
} from '@ant-design/icons';
import { 
  transformMindMapToReactFlow, 
  filterByExpandedState,
  getAncestorPath,
  searchNodes
} from '../utils/mindMapTransform';

/**
 * Inner MindMapViewer Component (with React Flow context)
 */
function MindMapViewerInner({ mindMapData, onMessageRefClick, onExport }) {
  const reactFlowInstance = useReactFlow();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [highlightedNodes, setHighlightedNodes] = useState(new Set());
  const [hoveredNode, setHoveredNode] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState(null);

  // Initialize nodes and edges from mind map data
  useEffect(() => {
    if (mindMapData) {
      // Initially expand all nodes
      const allNodeIds = new Set(Object.keys(mindMapData.nodes || {}));
      setExpandedNodes(allNodeIds);
    }
  }, [mindMapData]);

  // Update visible nodes and edges when expanded state changes
  useEffect(() => {
    if (mindMapData && expandedNodes.size > 0) {
      const { nodes: visibleNodes, edges: visibleEdges } = filterByExpandedState(
        mindMapData, 
        expandedNodes
      );
      
      // Add visual indicators for expandable nodes
      const enhancedNodes = visibleNodes.map(node => {
        const originalNode = mindMapData.nodes[node.id];
        const hasChildren = originalNode.children_ids && originalNode.children_ids.length > 0;
        const isExpanded = expandedNodes.has(node.id);
        const isHighlighted = highlightedNodes.has(node.id);
        
        return {
          ...node,
          data: {
            ...node.data,
            hasChildren,
            isExpanded,
            label: hasChildren 
              ? `${node.data.label} ${isExpanded ? '▼' : '▶'}` 
              : node.data.label
          },
          style: {
            ...node.style,
            border: isHighlighted 
              ? '2px solid #52c41a' 
              : node.style.border,
            boxShadow: isHighlighted 
              ? '0 0 10px rgba(82, 196, 26, 0.5)' 
              : 'none'
          }
        };
      });
      
      setNodes(enhancedNodes);
      setEdges(visibleEdges);
    }
  }, [mindMapData, expandedNodes, highlightedNodes, setNodes, setEdges]);

  // Handle node click - expand/collapse
  const handleNodeClick = useCallback((event, node) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(node.id)) {
        newSet.delete(node.id);
      } else {
        newSet.add(node.id);
      }
      return newSet;
    });
    setSelectedNode(node.id);
  }, []);

  // Handle node hover - show tooltip
  const handleNodeMouseEnter = useCallback((event, node) => {
    setHoveredNode(node);
    
    // Calculate tooltip position
    const rect = event.target.getBoundingClientRect();
    setTooltipPosition({
      x: rect.right + 10,
      y: rect.top
    });
  }, []);

  const handleNodeMouseLeave = useCallback(() => {
    setHoveredNode(null);
    setTooltipPosition(null);
  }, []);

  // Zoom controls
  const handleZoomIn = useCallback(() => {
    if (reactFlowInstance) {
      reactFlowInstance.zoomIn({ duration: 300 });
    }
  }, [reactFlowInstance]);

  const handleZoomOut = useCallback(() => {
    if (reactFlowInstance) {
      reactFlowInstance.zoomOut({ duration: 300 });
    }
  }, [reactFlowInstance]);

  const handleFitView = useCallback(() => {
    if (reactFlowInstance) {
      reactFlowInstance.fitView({ padding: 0.2, duration: 300 });
    }
  }, [reactFlowInstance]);

  // Expand/collapse all nodes
  const handleExpandAll = useCallback(() => {
    if (mindMapData) {
      const allNodeIds = new Set(Object.keys(mindMapData.nodes));
      setExpandedNodes(allNodeIds);
    }
  }, [mindMapData]);

  const handleCollapseAll = useCallback(() => {
    // Only keep root node expanded
    if (mindMapData && mindMapData.root_node) {
      setExpandedNodes(new Set([mindMapData.root_node.id]));
    }
  }, [mindMapData]);

  // Search functionality
  const handleSearch = useCallback((value) => {
    setSearchKeyword(value);
    
    if (!value || !mindMapData) {
      setHighlightedNodes(new Set());
      return;
    }

    // Find matching nodes
    const matchedNodeIds = searchNodes(mindMapData, value);
    
    if (matchedNodeIds.length === 0) {
      message.info('未找到匹配的节点');
      setHighlightedNodes(new Set());
      return;
    }

    // Expand paths to all matched nodes
    const nodesToExpand = new Set(expandedNodes);
    matchedNodeIds.forEach(nodeId => {
      const ancestorPath = getAncestorPath(mindMapData, nodeId);
      ancestorPath.forEach(ancestorId => nodesToExpand.add(ancestorId));
    });

    setHighlightedNodes(new Set(matchedNodeIds));
    setExpandedNodes(nodesToExpand);
    message.success(`找到 ${matchedNodeIds.length} 个匹配节点`);
  }, [mindMapData, expandedNodes]);

  // Handle message reference click
  const handleMessageRefClick = useCallback((messageId) => {
    if (onMessageRefClick) {
      onMessageRefClick(messageId);
      message.success(`正在跳转到消息: ${messageId}`);
    } else {
      message.warning('消息导航未配置');
    }
  }, [onMessageRefClick]);

  // Handle export
  const handleExport = useCallback((format) => {
    if (onExport) {
      onExport(format);
    }
  }, [onExport]);

  // Export menu items
  const exportMenuItems = [
    {
      key: 'png',
      label: '导出为 PNG',
      onClick: () => handleExport('png')
    },
    {
      key: 'svg',
      label: '导出为 SVG',
      onClick: () => handleExport('svg')
    },
    {
      key: 'json',
      label: '导出为 JSON',
      onClick: () => handleExport('json')
    },
    {
      key: 'markdown',
      label: '导出为 Markdown',
      onClick: () => handleExport('markdown')
    }
  ];

  if (!mindMapData) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100%' 
      }}>
        <p>暂无思维导图数据</p>
      </div>
    );
  }

  return (
    <div style={{ 
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      width: '100%', 
      height: '100%'
    }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        onNodeMouseEnter={handleNodeMouseEnter}
        onNodeMouseLeave={handleNodeMouseLeave}
        fitView
        attributionPosition="bottom-left"
        minZoom={0.1}
        maxZoom={2}
      >
        <Background />
        <Controls />
        <MiniMap />
        
        {/* Toolbar Panel */}
        <Panel position="top-left" style={{ margin: '10px' }}>
          <div style={{ 
            background: 'white', 
            padding: '12px', 
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            position: 'relative',
            zIndex: 10
          }}>
            <Space direction="vertical" size="small">
              <Input.Search
                placeholder="搜索节点..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                onSearch={handleSearch}
                style={{ width: 250 }}
                prefix={<SearchOutlined />}
              />
              
              <Space wrap>
                <Tooltip title="放大">
                  <Button 
                    icon={<ZoomInOutlined />} 
                    onClick={handleZoomIn}
                    size="small"
                  />
                </Tooltip>
                
                <Tooltip title="缩小">
                  <Button 
                    icon={<ZoomOutOutlined />} 
                    onClick={handleZoomOut}
                    size="small"
                  />
                </Tooltip>
                
                <Tooltip title="全部展开">
                  <Button 
                    icon={<ExpandOutlined />} 
                    onClick={handleExpandAll}
                    size="small"
                  />
                </Tooltip>
                
                <Tooltip title="全部折叠">
                  <Button 
                    icon={<CompressOutlined />} 
                    onClick={handleCollapseAll}
                    size="small"
                  />
                </Tooltip>
                
                <Tooltip title="适应视图">
                  <Button 
                    onClick={handleFitView}
                    size="small"
                  >
                    适应
                  </Button>
                </Tooltip>
                
                <Dropdown menu={{ items: exportMenuItems }} placement="bottomRight">
                  <Tooltip title="导出">
                    <Button 
                      icon={<DownloadOutlined />} 
                      size="small"
                    >
                      导出
                    </Button>
                  </Tooltip>
                </Dropdown>
              </Space>
            </Space>
          </div>
        </Panel>
      </ReactFlow>

      {/* Tooltip for hovered node */}
      {hoveredNode && tooltipPosition && (
        <div
          style={{
            position: 'fixed',
            left: tooltipPosition.x,
            top: tooltipPosition.y,
            background: 'white',
            border: '1px solid #d9d9d9',
            borderRadius: '8px',
            padding: '16px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            maxWidth: '350px',
            zIndex: 1000,
            pointerEvents: 'auto'
          }}
        >
          {/* Node content */}
          <div style={{ marginBottom: '12px' }}>
            <div style={{ 
              fontSize: '14px', 
              fontWeight: 'bold',
              marginBottom: '4px',
              color: '#1890ff'
            }}>
              {hoveredNode.data.originalNode?.content || hoveredNode.data.label}
            </div>
            <div style={{ fontSize: '12px', color: '#999' }}>
              层级 {hoveredNode.data.level}
            </div>
          </div>
          
          {/* Node metadata */}
          {hoveredNode.data.metadata && Object.keys(hoveredNode.data.metadata).length > 0 && (
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                元数据:
              </div>
              <div style={{ fontSize: '12px', color: '#333' }}>
                {JSON.stringify(hoveredNode.data.metadata, null, 2)}
              </div>
            </div>
          )}
          
          {/* Message references */}
          {hoveredNode.data.messageReferences && 
           hoveredNode.data.messageReferences.length > 0 && (
            <div>
              <div style={{ 
                fontSize: '12px', 
                color: '#666', 
                marginBottom: '8px',
                fontWeight: '500'
              }}>
                相关消息 ({hoveredNode.data.messageReferences.length}):
              </div>
              <Space wrap size="small">
                {hoveredNode.data.messageReferences.map((msgId, index) => (
                  <Tag
                    key={msgId}
                    color="blue"
                    style={{ 
                      cursor: 'pointer',
                      margin: '2px'
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleMessageRefClick(msgId);
                    }}
                  >
                    消息 {index + 1}
                  </Tag>
                ))}
              </Space>
            </div>
          )}
          
          {/* Children info */}
          {hoveredNode.data.hasChildren && (
            <div style={{ 
              marginTop: '12px', 
              paddingTop: '12px', 
              borderTop: '1px solid #f0f0f0',
              fontSize: '12px',
              color: '#666'
            }}>
              {hoveredNode.data.isExpanded 
                ? `${hoveredNode.data.originalNode?.children_ids?.length || 0} 个子节点已展开`
                : `${hoveredNode.data.originalNode?.children_ids?.length || 0} 个子节点已折叠`
              }
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * MindMapViewer Component (with React Flow Provider)
 * 
 * @param {Object} props
 * @param {Object} props.mindMapData - Mind map data from backend
 * @param {Function} props.onMessageRefClick - Callback when message reference is clicked
 * @param {Function} props.onExport - Callback for export action
 */
function MindMapViewer(props) {
  return (
    <ReactFlowProvider>
      <MindMapViewerInner {...props} />
    </ReactFlowProvider>
  );
}

export default MindMapViewer;
