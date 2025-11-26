import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import { TeamOutlined, CommentOutlined, HomeOutlined } from '@ant-design/icons'
import AgentList from './pages/AgentList'
import MeetingList from './pages/MeetingList'
import MeetingRoom from './pages/MeetingRoom'
import Home from './pages/Home'

const { Header, Content } = Layout

function App() {
  const location = useLocation()
  
  const menuItems = [
    { key: '/', icon: <HomeOutlined />, label: <Link to="/">首页</Link> },
    { key: '/agents', icon: <TeamOutlined />, label: <Link to="/agents">代理管理</Link> },
    { key: '/meetings', icon: <CommentOutlined />, label: <Link to="/meetings">会议管理</Link> },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center' }}>
        <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold', marginRight: '50px' }}>
          AI 代理会议系统
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={menuItems}
          style={{ flex: 1, minWidth: 0 }}
        />
      </Header>
      <Content style={{ padding: '24px' }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/agents" element={<AgentList />} />
          <Route path="/meetings" element={<MeetingList />} />
          <Route path="/meetings/:meetingId" element={<MeetingRoom />} />
        </Routes>
      </Content>
    </Layout>
  )
}

export default App
