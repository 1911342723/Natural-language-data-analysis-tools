import { Tabs, Card } from 'antd'
import { 
  TableOutlined, 
  BarChartOutlined, 
  FileTextOutlined 
} from '@ant-design/icons'
import TableResult from './TableResult'
import ChartResult from './ChartResult'
import AISummary from './AISummary'
import './ResultDisplay.css'

const { TabPane } = Tabs

function ResultDisplay({ result }) {
  if (!result) return null

  const hasTable = result.table_data && result.table_data.length > 0
  const hasChart = result.chart_base64
  const hasSummary = result.summary

  return (
    <Card className="result-display-card" variant="borderless">
      <Tabs defaultActiveKey="summary" className="result-tabs">
        {/* AI 总结 */}
        {hasSummary && (
          <TabPane
            tab={
              <span>
                <FileTextOutlined />
                AI 总结
              </span>
            }
            key="summary"
          >
            <AISummary summary={result.summary} />
          </TabPane>
        )}

        {/* 表格数据 */}
        {hasTable && (
          <TabPane
            tab={
              <span>
                <TableOutlined />
                数据表格
              </span>
            }
            key="table"
          >
            <TableResult data={result.table_data} columns={result.table_columns} />
          </TabPane>
        )}

        {/* 图表 */}
        {hasChart && (
          <TabPane
            tab={
              <span>
                <BarChartOutlined />
                图表
              </span>
            }
            key="chart"
          >
            <ChartResult
              chartBase64={result.chart_base64}
              chartTitle={result.chart_title}
            />
          </TabPane>
        )}
      </Tabs>
    </Card>
  )
}

export default ResultDisplay


