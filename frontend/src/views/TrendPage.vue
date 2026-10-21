<template>
  <div class="trend-page">
    <!-- 顶部导航 -->
    <div class="header">
      <h1>📊 速度趋势</h1>
      <div class="user-info" @click="goToProfile">
        <el-avatar :size="36" :src="userInfo?.avatarUrl">
          {{ userInfo?.nickname?.charAt(0) || 'U' }}
        </el-avatar>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>加载中...</p>
    </div>

    <!-- 无数据 -->
    <div v-else-if="chartData.length === 0" class="empty">
      <el-empty description="暂无已完成的击球分析记录" />
    </div>

    <!-- 图表内容 -->
    <div v-else class="content">
      <div class="summary">
        <div class="summary-item">
          <div class="summary-label">最近一次</div>
          <div class="summary-value">{{ chartData[chartData.length - 1].speed }} <small>km/h</small></div>
        </div>
        <div class="summary-item">
          <div class="summary-label">最高</div>
          <div class="summary-value highlight">{{ maxSpeed }} <small>km/h</small></div>
        </div>
        <div class="summary-item">
          <div class="summary-label">平均</div>
          <div class="summary-value">{{ avgSpeed }} <small>km/h</small></div>
        </div>
      </div>
      <v-chart class="chart" :option="chartOption" autoresize />
    </div>

    <!-- 底部导航 -->
    <div class="bottom-nav">
      <div class="nav-item" @click="goToTraining">
        <el-icon><HomeFilled /></el-icon>
        <span>训练</span>
      </div>
      <div class="nav-item active">
        <el-icon><TrendCharts /></el-icon>
        <span>趋势</span>
      </div>
      <div class="nav-item" @click="goToProfile">
        <el-icon><User /></el-icon>
        <span>我的</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, HomeFilled, User, TrendCharts } from '@element-plus/icons-vue'
import { videoApi } from '../utils/api'
import { auth } from '../utils/auth'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkLineComponent
} from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent])

const router = useRouter()
const userInfo = ref(auth.getUserInfo())
const loading = ref(true)
const chartData = ref([])

const maxSpeed = computed(() => {
  if (chartData.value.length === 0) return '--'
  return Math.max(...chartData.value.map(d => d.speed))
})

const avgSpeed = computed(() => {
  if (chartData.value.length === 0) return '--'
  return (chartData.value.reduce((a, d) => a + d.speed, 0) / chartData.value.length).toFixed(1)
})

const chartOption = computed(() => {
  const dates = chartData.value.map(d => d.date)
  const batSpeeds = chartData.value.map(d => d.speed)
  const leftSpeeds = chartData.value.map(d => d.leftSpeed)
  const rightSpeeds = chartData.value.map(d => d.rightSpeed)
  const avg = parseFloat(avgSpeed.value)

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        let tip = params[0].axisValue
        params.forEach(p => {
          if (p.value != null) {
            tip += `<br/>${p.marker} ${p.seriesName}: <b>${p.value} km/h</b>`
          }
        })
        return tip
      }
    },
    legend: {
      data: ['挥棒速度', '左手速度', '右手速度'],
      bottom: 0,
      textStyle: { fontSize: 11, color: '#666' }
    },
    grid: { left: 45, right: 15, top: 15, bottom: 35 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: { rotate: 30, fontSize: 10, color: '#999' },
      axisLine: { lineStyle: { color: '#ddd' } }
    },
    yAxis: {
      type: 'value',
      name: 'km/h',
      nameTextStyle: { color: '#999', fontSize: 10 },
      axisLabel: { color: '#999', fontSize: 10 },
      splitLine: { lineStyle: { color: '#f0f0f0' } }
    },
    series: [
      {
        name: '挥棒速度',
        type: 'line',
        data: batSpeeds,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 3,
          color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [{ offset: 0, color: '#667eea' }, { offset: 1, color: '#764ba2' }]
          }
        },
        itemStyle: { color: '#667eea', borderColor: '#fff', borderWidth: 2 },
        areaStyle: {
          color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: 'rgba(102,126,234,0.2)' }, { offset: 1, color: 'rgba(102,126,234,0.02)' }]
          }
        },
        markLine: avg > 0 ? {
          silent: true,
          lineStyle: { type: 'dashed', color: '#E6A23C' },
          label: { formatter: '平均 {c}', color: '#E6A23C', fontSize: 10 },
          data: [{ type: 'average', name: '平均值' }]
        } : undefined
      },
      {
        name: '左手速度',
        type: 'line',
        data: leftSpeeds,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 1.5, color: '#409EFF' },
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '右手速度',
        type: 'line',
        data: rightSpeeds,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 1.5, color: '#F56C6C' },
        itemStyle: { color: '#F56C6C' }
      }
    ]
  }
})

const loadData = async () => {
  loading.value = true
  try {
    const response = await videoApi.getVideoRecords({
      pageNum: 1,
      pageSize: 30,
      status: 1,
      actionType: 'batting',
      sortBy: 'createTime',
      sortOrder: 'asc'
    })
    if (response.data.code === '200') {
      const records = response.data.data.records || []
      chartData.value = records
        .filter(r => r.maxBatSpeedKmH && r.maxBatSpeedKmH > 0)
        .map(r => {
          const d = new Date(r.createTime)
          const dateStr = `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
          return {
            date: dateStr,
            speed: Math.round(r.maxBatSpeedKmH * 10) / 10,
            leftSpeed: r.leftSpeedKmH ? Math.round(r.leftSpeedKmH * 10) / 10 : null,
            rightSpeed: r.rightSpeedKmH ? Math.round(r.rightSpeedKmH * 10) / 10 : null
          }
        })
    } else {
      ElMessage.error(response.data.message || '加载失败')
    }
  } catch (error) {
    ElMessage.error('加载失败：' + (error.response?.data?.message || error.message))
  } finally {
    loading.value = false
  }
}

const goToTraining = () => { router.push('/') }
const goToProfile = () => { router.push('/profile') }

onMounted(() => { loadData() })
</script>

<style scoped>
.trend-page {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 70px;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header h1 {
  font-size: 24px;
  margin: 0;
}

.user-info {
  cursor: pointer;
}

.loading, .empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 20px;
  color: #999;
}

.content {
  padding: 20px;
}

.summary {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.summary-item {
  flex: 1;
  background: white;
  border-radius: 10px;
  padding: 14px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.summary-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.summary-value {
  font-size: 22px;
  font-weight: bold;
  color: #667eea;
}

.summary-value small {
  font-size: 11px;
  font-weight: normal;
  color: #999;
}

.summary-value.highlight {
  color: #E6A23C;
}

.chart {
  width: 100%;
  height: 300px;
  background: white;
  border-radius: 12px;
  padding: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  display: flex;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
  cursor: pointer;
  color: #999;
  transition: all 0.3s;
}

.nav-item.active {
  color: #667eea;
}

.nav-item .el-icon {
  font-size: 24px;
  margin-bottom: 4px;
}

.nav-item span {
  font-size: 12px;
}

/* 移动端适配 */
@media screen and (max-width: 768px) {
  .header {
    padding: 14px 16px;
  }

  .header h1 {
    font-size: 18px;
  }

  .content {
    padding: 12px 16px;
  }

  .summary {
    gap: 8px;
    margin-bottom: 12px;
  }

  .summary-item {
    padding: 10px;
    border-radius: 8px;
  }

  .summary-label {
    font-size: 11px;
  }

  .summary-value {
    font-size: 18px;
  }

  .chart {
    height: 250px;
  }

  .bottom-nav {
    padding-bottom: env(safe-area-inset-bottom, 0);
  }

  .nav-item {
    padding: 8px;
  }

  .nav-item .el-icon {
    font-size: 22px;
  }

  .nav-item span {
    font-size: 11px;
  }
}
</style>
