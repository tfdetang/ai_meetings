/**
 * Mind Map View Page
 * Full-screen mind map visualization for a meeting
 */

import React, { useState, useEffect } from 'react';
import { Card, Button, Space, message, Spin, Modal } from 'antd';
import { ArrowLeftOutlined, ReloadOutlined } from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import MindMapViewer from '../components/MindMapViewer';
import { meetingsAPI } from '../api/client';

function MindMapView() {
  const navigate = useNavigate();
  const { meetingId } = useParams();
  const [mindMapData, setMindMapData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [exporting, setExporting] = useState(false);

  // Load mind map data
  useEffect(() => {
    loadMindMap();
  }, [meetingId]);

  const loadMindMap = async () => {
    setLoading(true);
    try {
      const response = await meetingsAPI.getMindMap(meetingId);
      setMindMapData(response.data);
    } catch (error) {
      if (error.response?.status === 404) {
        // No mind map exists yet
        setMindMapData(null);
      } else {
        message.error('加载思维导图失败');
        console.error('Load mind map error:', error);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateMindMap = async () => {
    setGenerating(true);
    try {
      message.loading('正在生成思维导图...', 0);
      const response = await meetingsAPI.generateMindMap(meetingId);
      message.destroy();
      message.success('思维导图生成成功');
      setMindMapData(response.data);
    } catch (error) {
      message.destroy();
      message.error(`生成思维导图失败: ${error.response?.data?.detail || error.message}`);
      console.error('Generate mind map error:', error);
    } finally {
      setGenerating(false);
    }
  };

  const handleMessageRefClick = (messageId) => {
    // Navigate back to meeting room and scroll to message
    navigate(`/meetings/${meetingId}`, { state: { scrollToMessage: messageId } });
  };

  const handleExport = async (format) => {
    setExporting(true);
    try {
      message.loading(`正在导出为 ${format.toUpperCase()} 格式...`, 0);
      
      const response = await meetingsAPI.exportMindMap(meetingId, format);
      
      // Create download link
      const blob = new Blob([response.data], { 
        type: response.headers['content-type'] 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Extract filename from content-disposition header or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = `mind_map_${meetingId}.${format}`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      message.destroy();
      message.success(`思维导图已导出为 ${format.toUpperCase()} 格式`);
    } catch (error) {
      message.destroy();
      message.error(`导出失败: ${error.response?.data?.detail || error.message}`);
      console.error('Export error:', error);
    } finally {
      setExporting(false);
    }
  };

  const handleRegenerate = () => {
    Modal.confirm({
      title: '重新生成思维导图',
      content: '确定要重新生成思维导图吗？这将替换当前版本。',
      okText: '重新生成',
      cancelText: '取消',
      onOk: handleGenerateMindMap
    });
  };

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <Spin size="large" tip="正在加载思维导图..." />
      </div>
    );
  }

  if (!mindMapData) {
    return (
      <div style={{ padding: '24px', height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Card 
          title="思维导图"
          extra={
            <Button 
              icon={<ArrowLeftOutlined />} 
              onClick={() => navigate(`/meetings/${meetingId}`)}
            >
              返回会议
            </Button>
          }
        >
          <div style={{ 
            textAlign: 'center', 
            padding: '60px 20px' 
          }}>
            <h3>暂无思维导图</h3>
            <p style={{ color: '#666', marginBottom: '24px' }}>
              生成思维导图以可视化会议讨论结构。
            </p>
            <Button 
              type="primary" 
              size="large"
              loading={generating}
              onClick={handleGenerateMindMap}
            >
              生成思维导图
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ 
      padding: '24px', 
      height: '100vh', 
      display: 'flex', 
      flexDirection: 'column',
      boxSizing: 'border-box'
    }}>
      <Card 
        title="思维导图可视化"
        extra={
          <Space>
            <Button 
              icon={<ReloadOutlined />}
              loading={generating}
              onClick={handleRegenerate}
            >
              重新生成
            </Button>
            <Button 
              icon={<ArrowLeftOutlined />} 
              onClick={() => navigate(`/meetings/${meetingId}`)}
            >
              返回会议
            </Button>
          </Space>
        }
        style={{ marginBottom: '16px', flexShrink: 0 }}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <p>
            交互式思维导图可视化会议讨论内容。
            点击节点展开/折叠，悬停查看详情，使用工具栏进行导航。
          </p>
          {/* Note about minutes integration */}
          <div style={{ 
            padding: '8px 12px', 
            background: '#f0f5ff', 
            borderRadius: '4px',
            fontSize: '13px',
            color: '#666'
          }}>
            💡 提示：思维导图基于会议内容生成。如果会议有纪要，关键决策将被引用到相关节点中。
          </div>
        </Space>
      </Card>

      <div style={{ 
        flex: 1,
        minHeight: 0,
        position: 'relative'
      }}>
        {exporting && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            zIndex: 1000,
            background: 'rgba(255, 255, 255, 0.9)',
            padding: '20px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
          }}>
            <Spin size="large" tip="正在导出..." />
          </div>
        )}
        <div style={{ 
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0
        }}>
          <MindMapViewer
            mindMapData={mindMapData}
            onMessageRefClick={handleMessageRefClick}
            onExport={handleExport}
          />
        </div>
      </div>
    </div>
  );
}

export default MindMapView;
