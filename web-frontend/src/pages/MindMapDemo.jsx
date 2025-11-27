/**
 * Mind Map Demo Page
 * Demonstrates the MindMapViewer component with sample data
 */

import React, { useState } from 'react';
import { Card, Button, Space, message, Spin } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import MindMapViewer from '../components/MindMapViewer';
import { meetingsAPI } from '../api/client';

// Sample mind map data for demonstration
const sampleMindMap = {
  id: 'mindmap-demo',
  meeting_id: 'meeting-demo',
  root_node: {
    id: 'root',
    content: 'AI Agent Meeting System',
    level: 0,
    parent_id: null,
    children_ids: ['node-1', 'node-2', 'node-3'],
    message_references: [],
    metadata: {}
  },
  nodes: {
    'root': {
      id: 'root',
      content: 'AI Agent Meeting System',
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
      parent_id: 'root',
      children_ids: ['node-1-1', 'node-1-2'],
      message_references: ['msg-1', 'msg-2'],
      metadata: { category: 'technical' }
    },
    'node-1-1': {
      id: 'node-1-1',
      content: 'Backend Services',
      level: 2,
      parent_id: 'node-1',
      children_ids: ['node-1-1-1', 'node-1-1-2'],
      message_references: ['msg-3'],
      metadata: {}
    },
    'node-1-1-1': {
      id: 'node-1-1-1',
      content: 'Meeting Service',
      level: 3,
      parent_id: 'node-1-1',
      children_ids: [],
      message_references: ['msg-4', 'msg-5'],
      metadata: {}
    },
    'node-1-1-2': {
      id: 'node-1-1-2',
      content: 'Agent Service',
      level: 3,
      parent_id: 'node-1-1',
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
      message_references: ['msg-7', 'msg-8'],
      metadata: {}
    },
    'node-2': {
      id: 'node-2',
      content: 'Features',
      level: 1,
      parent_id: 'root',
      children_ids: ['node-2-1', 'node-2-2', 'node-2-3'],
      message_references: ['msg-9'],
      metadata: { category: 'features' }
    },
    'node-2-1': {
      id: 'node-2-1',
      content: 'Agent Management',
      level: 2,
      parent_id: 'node-2',
      children_ids: [],
      message_references: ['msg-10'],
      metadata: {}
    },
    'node-2-2': {
      id: 'node-2-2',
      content: 'Meeting Control',
      level: 2,
      parent_id: 'node-2',
      children_ids: [],
      message_references: ['msg-11', 'msg-12'],
      metadata: {}
    },
    'node-2-3': {
      id: 'node-2-3',
      content: 'Mind Map Visualization',
      level: 2,
      parent_id: 'node-2',
      children_ids: [],
      message_references: ['msg-13'],
      metadata: {}
    },
    'node-3': {
      id: 'node-3',
      content: 'Implementation Plan',
      level: 1,
      parent_id: 'root',
      children_ids: ['node-3-1', 'node-3-2'],
      message_references: ['msg-14'],
      metadata: { category: 'planning' }
    },
    'node-3-1': {
      id: 'node-3-1',
      content: 'Phase 1: Core Features',
      level: 2,
      parent_id: 'node-3',
      children_ids: [],
      message_references: ['msg-15'],
      metadata: {}
    },
    'node-3-2': {
      id: 'node-3-2',
      content: 'Phase 2: Advanced Features',
      level: 2,
      parent_id: 'node-3',
      children_ids: [],
      message_references: ['msg-16'],
      metadata: {}
    }
  },
  created_at: '2024-01-01T00:00:00',
  created_by: 'demo-user',
  version: 1
};

function MindMapDemo() {
  const navigate = useNavigate();
  const [mindMapData] = useState(sampleMindMap);
  const [exporting, setExporting] = useState(false);

  const handleMessageRefClick = (messageId) => {
    message.info(`Message reference clicked: ${messageId}`);
    console.log('Navigate to message:', messageId);
  };

  const handleExport = async (format) => {
    setExporting(true);
    try {
      message.loading(`Exporting mind map as ${format.toUpperCase()}...`, 0);
      
      // For demo, we'll simulate export
      // In real implementation, this would call the API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      message.destroy();
      message.success(`Mind map exported as ${format.toUpperCase()}`);
      console.log('Export format:', format);
    } catch (error) {
      message.destroy();
      message.error(`Failed to export: ${error.message}`);
      console.error('Export error:', error);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div style={{ padding: '24px', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Card 
        title="Mind Map Visualization Demo"
        extra={
          <Button 
            icon={<ArrowLeftOutlined />} 
            onClick={() => navigate('/')}
          >
            Back to Home
          </Button>
        }
        style={{ marginBottom: '16px' }}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <p>
            This is a demonstration of the interactive mind map visualization component.
            Try the following features:
          </p>
          <ul>
            <li>Click on nodes to expand/collapse their children</li>
            <li>Hover over nodes to see detailed information and message references</li>
            <li>Use the search box to find specific nodes</li>
            <li>Use zoom controls to navigate the map</li>
            <li>Click "Expand All" or "Collapse All" to control visibility</li>
            <li>Click on message reference tags to navigate (simulated)</li>
          </ul>
        </Space>
      </Card>

      <Card style={{ flex: 1, overflow: 'hidden' }}>
        <div style={{ height: '100%' }}>
          <MindMapViewer
            mindMapData={mindMapData}
            onMessageRefClick={handleMessageRefClick}
            onExport={handleExport}
          />
        </div>
      </Card>
    </div>
  );
}

export default MindMapDemo;
