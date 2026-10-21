<template>
  <div class="daily-records-container">
    <!-- 顶部导航 -->
    <div class="header">
      <el-button @click="goBack" :icon="ArrowLeft" circle />
      <h1>{{ selectedDate }} 的训练记录</h1>
      <div style="width: 40px"></div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>加载中...</p>
    </div>

    <!-- 无数据 -->
    <el-empty v-else-if="records.length === 0" description="当天暂无训练记录" />

    <!-- 记录列表 -->
    <div v-else class="records-content">
      <div class="records-summary">
        <span class="total">共 {{ records.length }} 条记录</span>
      </div>

      <div class="records-table">
        <div
          v-for="record in records"
          :key="record.recordId"
          class="record-card"
          @click="viewDetail(record)"
        >
          <div class="record-type">
            <el-icon v-if="record.actionType === 'batting'"><Trophy /></el-icon>
            <el-icon v-else><Aim /></el-icon>
            <span>{{ record.actionType === 'batting' ? '击球' : '投球' }}</span>
          </div>

          <el-tag :type="getStatusType(record.status)" size="small">
            {{ getStatusText(record.status) }}
          </el-tag>

          <span class="record-time">{{ formatTime(record.createTime) }}</span>

          <template v-if="record.status === 1">
            <span class="record-score">{{ record.overallScore || '--' }}</span>
            <el-tag :type="getGradeType(record.grade)" size="small">
              {{ record.grade || '--' }}
            </el-tag>
            <span class="record-stat">左手 {{ record.leftSpeedMs || '--' }} m/s</span>
            <span class="record-stat">右手 {{ record.rightSpeedMs || '--' }} m/s</span>
            <span class="record-stat">转胯 {{ record.maxHipRotationMm || '--' }} mm</span>
            <span class="record-stat">扭转 {{ record.maxTwistAngleDeg || '--' }}°</span>
          </template>

          <el-button type="primary" size="small" text @click.stop="viewDetail(record)">
            详情 →
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Loading, Trophy, Aim } from '@element-plus/icons-vue'
import { videoApi } from '../utils/api'

const route = useRoute()
const router = useRouter()

const selectedDate = ref(route.params.date)
const records = ref([])
const loading = ref(true)

// 加载数据
const loadRecords = async () => {
  loading.value = true
  try {
    const response = await videoApi.getDailyRecords(selectedDate.value)
    if (response.data.code === '200') {
      records.value = response.data.data || []
    }
  } catch (error) {
    console.error('加载记录失败:', error)
    ElMessage.error('加载记录失败')
  } finally {
    loading.value = false
  }
}

// 查看详情
const viewDetail = (record) => {
  router.push(`/analysis/${record.recordId}`)
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '--'
  const date = new Date(time)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

// 获取状态类型
const getStatusType = (status) => {
  const typeMap = {
    0: 'info',
    1: 'success',
    2: 'danger'
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    0: '分析中',
    1: '已完成',
    2: '失败'
  }
  return statusMap[status] || '未知'
}

// 获取等级类型
const getGradeType = (grade) => {
  const typeMap = {
    'A': 'success',
    'B': 'primary',
    'C': 'warning',
    'D': 'danger',
    'E': 'danger'
  }
  return typeMap[grade] || 'info'
}

onMounted(() => {
  loadRecords()
})
</script>

<style scoped>
.daily-records-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header h1 {
  font-size: 18px;
  margin: 0;
  flex: 1;
  text-align: center;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 20px;
  color: #999;
}

.records-content {
  padding: 20px;
}

.records-summary {
  margin-bottom: 15px;
  font-size: 14px;
  color: #666;
}

.records-table {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.record-card {
  background: white;
  border-radius: 8px;
  padding: 10px 14px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: nowrap;
}

.record-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.record-type {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
  flex-shrink: 0;
}

.record-time {
  font-size: 12px;
  color: #888;
  white-space: nowrap;
  flex-shrink: 0;
}

.record-score {
  font-size: 16px;
  font-weight: bold;
  color: #667eea;
  white-space: nowrap;
  flex-shrink: 0;
}

.record-stat {
  font-size: 11px;
  color: #666;
  white-space: nowrap;
  flex-shrink: 0;
  background: #f5f5f5;
  padding: 2px 8px;
  border-radius: 4px;
}

@media screen and (max-width: 768px) {
  .header h1 {
    font-size: 16px;
  }

  .records-content {
    padding: 15px;
  }

  .record-card {
    padding: 8px 10px;
  }

  .record-stat {
    font-size: 10px;
    padding: 2px 6px;
  }
}
</style>
