<template>
  <div class="analysis-container">
    <!-- 顶部导航 -->
    <div class="header">
      <el-button @click="goBack" icon="ArrowLeft" circle />
      <h1>分析详情</h1>
      <div style="width: 40px"></div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>加载中...</p>
    </div>

    <!-- 分析结果 -->
    <div v-else-if="analysisResult" class="content">
      <!-- 基本信息 -->
      <div class="info-card">
        <div class="info-header">
          <span class="action-type">
            {{ analysisResult.actionType === 'batting' ? '🏏 击球分析' : '⚾ 投球分析' }}
          </span>
          <span :class="['status', `status-${analysisResult.status}`]">
            {{ getStatusText(analysisResult.status) }}
          </span>
        </div>
        <div class="info-row">
          <span class="label">记录ID:</span>
          <span class="value">{{ analysisResult.recordId }}</span>
        </div>
        <div class="info-row">
          <span class="label">视频信息:</span>
          <span class="value">{{ analysisResult.videoWidth }}x{{ analysisResult.videoHeight }}, {{ analysisResult.fps }}fps</span>
        </div>
      </div>

      <!-- 速度数据 -->
      <div v-if="analysisResult.status === 1" class="data-section">
        <h3>手臂速度</h3>
        <div class="data-grid">
          <div class="data-item">
            <div class="data-label">左手</div>
            <div class="data-value">{{ analysisResult.leftSpeedMs }} m/s</div>
            <div class="data-sub">{{ analysisResult.leftSpeedKmH }} km/h</div>
          </div>
          <div class="data-item">
            <div class="data-label">右手</div>
            <div class="data-value">{{ analysisResult.rightSpeedMs }} m/s</div>
            <div class="data-sub">{{ analysisResult.rightSpeedKmH }} km/h</div>
          </div>
        </div>
      </div>

      <!-- 挥棒速度 -->
      <div v-if="analysisResult.status === 1 && analysisResult.maxBatSpeedKmH" class="data-section">
        <h3>挥棒速度</h3>
        <div class="data-grid">
          <div class="data-item">
            <div class="data-label">最大速度</div>
            <div class="data-value">{{ analysisResult.maxBatSpeedKmH }} km/h</div>
          </div>
          <div class="data-item">
            <div class="data-label">平均速度</div>
            <div class="data-value">{{ analysisResult.avgBatSpeedKmH }} km/h</div>
          </div>
        </div>
      </div>

      <!-- 动作数据 -->
      <div v-if="analysisResult.status === 1" class="data-section">
        <h3>动作数据</h3>
        <div class="data-grid">
          <div class="data-item">
            <div class="data-label">最大转胯</div>
            <div class="data-value">{{ analysisResult.maxHipRotationMm }} mm</div>
          </div>
          <div class="data-item">
            <div class="data-label">最大扭转</div>
            <div class="data-value">{{ analysisResult.maxTwistAngleDeg }}°</div>
          </div>
          <div class="data-item">
            <div class="data-label">肩髋差</div>
            <div class="data-value">{{ analysisResult.shoulderHipDiffDeg }}°</div>
          </div>
        </div>
      </div>

      <!-- 视频播放 -->
      <div v-if="analysisResult.status === 1 && analysisResult.skeletonVideoName" class="video-section">
        <h3>骨骼视频</h3>
        <video 
          v-if="videoUrl"
          :src="videoUrl" 
          controls 
          class="skeleton-video"
        >
          您的浏览器不支持视频播放
        </video>
        <el-button 
          v-else
          type="primary" 
          @click="loadVideo" 
          :loading="loadingVideo"
          class="load-video-btn"
        >
          加载视频
        </el-button>
      </div>

      <!-- 分析中状态 -->
      <div v-if="analysisResult.status === 0" class="analyzing-status">
        <el-icon class="is-loading" :size="60"><Loading /></el-icon>
        <p>分析中，请稍候...</p>
        <p class="tip">预计需要 1-3 分钟</p>
      </div>

      <!-- 分析失败 -->
      <div v-if="analysisResult.status === 2" class="error-status">
        <el-icon :size="60" color="#f56c6c"><CircleCloseFilled /></el-icon>
        <p>分析失败</p>
        <p class="error-message">{{ analysisResult.errorMessage || '未知错误' }}</p>
      </div>
    </div>

    <!-- 无数据 -->
    <div v-else class="empty">
      <el-empty description="暂无分析数据" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Loading, CircleCloseFilled } from '@element-plus/icons-vue'
import { videoApi } from '../utils/api'

const route = useRoute()
const router = useRouter()

const recordId = route.params.recordId
const loading = ref(true)
const analysisResult = ref(null)
const videoUrl = ref(null)
const loadingVideo = ref(false)

// 加载分析结果
const loadAnalysisResult = async () => {
  loading.value = true
  try {
    const response = await videoApi.getAnalysisResult(recordId)
    
    if (response.data.code === '200') {
      analysisResult.value = response.data.data
      
      // 如果分析中，继续轮询
      if (analysisResult.value.status === 0) {
        setTimeout(loadAnalysisResult, 5000)
      }
    } else {
      ElMessage.error(response.data.message || '加载失败')
    }
  } catch (error) {
    ElMessage.error('加载失败：' + (error.response?.data?.message || error.message))
  } finally {
    loading.value = false
  }
}

// 加载视频
const loadVideo = async () => {
  if (!analysisResult.value?.skeletonVideoName) return
  
  loadingVideo.value = true
  try {
    const response = await videoApi.getVideoDownloadUrl(analysisResult.value.skeletonVideoName)
    
    if (response.data.code === '200') {
      videoUrl.value = response.data.data.downloadUrl
    } else {
      ElMessage.error(response.data.message || '加载视频失败')
    }
  } catch (error) {
    ElMessage.error('加载视频失败：' + (error.response?.data?.message || error.message))
  } finally {
    loadingVideo.value = false
  }
}

// 返回上一页
const goBack = () => {
  router.back()
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

onMounted(() => {
  loadAnalysisResult()
})
</script>

<style scoped>
.analysis-container {
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

.info-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.action-type {
  font-size: 18px;
  font-weight: bold;
}

.status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
}

.status-0 {
  background: #e6f7ff;
  color: #1890ff;
}

.status-1 {
  background: #f6ffed;
  color: #52c41a;
}

.status-2 {
  background: #fff1f0;
  color: #f5222d;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-row:last-child {
  border-bottom: none;
}

.info-row .label {
  color: #999;
}

.info-row .value {
  color: #333;
}

.data-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.data-section h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
}

.data-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
}

.data-item {
  text-align: center;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 8px;
}

.data-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.data-value {
  font-size: 20px;
  font-weight: bold;
  color: #667eea;
}

.data-sub {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.video-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.video-section h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
}

.skeleton-video {
  width: 100%;
  border-radius: 8px;
}

.load-video-btn {
  width: 100%;
}

.analyzing-status, .error-status {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 12px;
  margin-bottom: 15px;
}

.analyzing-status p, .error-status p {
  margin: 15px 0 5px;
  font-size: 16px;
}

.tip, .error-message {
  font-size: 14px;
  color: #999;
}

@media screen and (max-width: 768px) {
  .data-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
