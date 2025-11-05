import { Button } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import ScientistTeamWorkspace from '../components/ScientistTeam/ScientistTeamWorkspace'
import './ScientistTeamPage.css'

function ScientistTeamPage() {
  const navigate = useNavigate()

  return (
    <div className="scientist-team-page">
      {/* 顶部导航栏 */}
      <div className="page-header">
        <Button 
          type="text" 
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/')}
          className="back-button"
        >
          返回首页
        </Button>
        <h1 className="page-title">科学家团队协作模式</h1>
      </div>

      {/* 工作区 */}
      <div className="page-content">
        <ScientistTeamWorkspace />
      </div>
    </div>
  )
}

export default ScientistTeamPage

