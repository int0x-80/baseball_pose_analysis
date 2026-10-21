<template>
  <div class="training-container">
    <!-- 顶部导航 -->
    <div class="header">
      <h1>🏏 训练中心</h1>
      <div class="user-info" @click="goToProfile">
        <el-avatar :size="36" :src="userInfo?.avatarUrl">
          {{ userInfo?.nickname?.charAt(0) || 'U' }}
        </el-avatar>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon">🎯</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.totalAnalysis || 0 }}</div>
          <div class="stat-label">分析次数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⭐</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.points || 0 }}</div>
          <div class="stat-label">积分</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">👑</div>
        <div class="stat-info">
          <div class="stat-value">VIP{{ stats.vipLevel || 0 }}</div>
          <div class="stat-label">会员等级</div>
        </div>
      </div>
    </div>

    <!-- 日历 + 上传 并排区域 -->
    <div class="middle-row">
      <!-- 训练日历 -->
      <div class="calendar-section">
        <h2>训练日历</h2>
        <TrainingCalendar />
      </div>

      <!-- 视频上传区域 -->
      <div class="upload-section">
        <h2>上传视频分析</h2>

        <el-form :model="uploadForm" class="upload-form">
          <el-radio-group v-model="uploadForm.actionType" size="small" class="action-type-group">
            <el-radio-button label="batting">🏏 击球</el-radio-button>
            <el-radio-button label="pitching">⚾ 投球</el-radio-button>
          </el-radio-group>

          <el-upload
            ref="uploadRef"
            class="upload-demo"
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :limit="1"
            accept="video/*"
          >
            <div class="upload-inner">
              <el-icon :size="18"><UploadFilled /></el-icon>
              <span class="upload-text">拖拽或<em>点击上传</em></span>
            </div>
          </el-upload>

          <el-button
            type="primary"
            @click="submitUpload"
            :loading="uploading"
            :disabled="!selectedFile"
            class="upload-button"
            size="small"
          >
            {{ uploading ? '分析中...' : '开始分析' }}
          </el-button>
        </el-form>
      </div>
    </div>

    <!-- 分析结果列表 -->
    <div class="results-section" v-if="analysisList.length > 0">
      <h2>分析记录</h2>
      <div class="results-list">
        <div
          v-for="item in analysisList"
          :key="item.recordId"
          class="result-card"
          @click="viewAnalysis(item.recordId)"
        >
          <div class="result-header">
            <span class="result-type">
              {{ item.actionType === 'batting' ? '🏏 击球' : '⚾ 投球' }}
            </span>
            <span :class="['result-status', `status-${item.status}`]">
              {{ getStatusText(item.status) }}
            </span>
          </div>
          <div class="result-info">
            <div class="result-score" v-if="item.status === 1">
              <span class="score-value">{{ item.overallScore || '--' }}</span>
              <span class="score-label">分</span>
            </div>
            <div class="result-time">
              {{ formatTime(item.createTime) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部导航 -->
    <div class="bottom-nav">
      <div class="nav-item active">
        <el-icon><HomeFilled /></el-icon>
        <span>训练</span>
      </div>
      <div class="nav-item" @click="goToTrend">
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
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled, HomeFilled, User, TrendCharts } from '@element-plus/icons-vue'
import { videoApi, userApi } from '../utils/api'
import { auth } from '../utils/auth'
import TrainingCalendar from '../components/TrainingCalendar.vue'

const router = useRouter()

// 用户信息
const userInfo = ref(auth.getUserInfo())

// 统计数据
const stats = reactive({
  totalAnalysis: 0,
  points: 0,
  vipLevel: 0
})

// 上传表单
const uploadRef = ref(null)
const uploadForm = reactive({
  actionType: 'batting'
})
const selectedFile = ref(null)
const uploading = ref(false)

// 分析记录列表
const analysisList = ref([])

// 加载用户信息
const loadUserInfo = async () => {
  try {
    const response = await userApi.getUserInfo()
    if (response.data.code === '200') {
      const data = response.data.data
      stats.totalAnalysis = data.totalAnalysisCount || 0
      stats.points = data.points || 0
      stats.vipLevel = data.vipLevel || 0
    }
  } catch (error) {
    console.error('加载用户信息失败:', error)
  }
}

// 加载分析记录
const loadAnalysisList = async () => {
  // TODO: 从后端获取分析记录列表
  // 这里使用模拟数据
  analysisList.value = []
}

// 处理文件选择
const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

// 处理文件移除
const handleFileRemove = () => {
  selectedFile.value = null
}

// 提交上传
const submitUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择视频文件')
    return
  }

  uploading.value = true
  try {
    const response = await videoApi.uploadVideo(
      selectedFile.value,
      userInfo.value.userId,
      uploadForm.actionType
    )

    if (response.data.code === 0 || response.data.code === '200') {
      const recordId = response.data.data.recordId
      ElMessage.success('上传成功，开始分析')

      // 添加到列表
      analysisList.value.unshift({
        recordId,
        actionType: uploadForm.actionType,
        status: 0, // 分析中
        createTime: new Date().toISOString()
      })

      // 开始轮询结果
      pollAnalysisResult(recordId)

      // 清空文件
      selectedFile.value = null
      uploadRef.value?.clearFiles()
    } else {
      ElMessage.error(response.data.message || '上传失败')
    }
  } catch (error) {
    ElMessage.error('上传失败：' + (error.response?.data?.message || error.message))
  } finally {
    uploading.value = false
  }
}

// 轮询分析结果
const pollAnalysisResult = async (recordId) => {
  const maxAttempts = 60 // 最多轮询 60 次（5分钟）
  let attempts = 0

  const poll = async () => {
    if (attempts >= maxAttempts) {
      ElMessage.warning('分析超时，请稍后查看结果')
      return
    }

    attempts++

    try {
      const response = await videoApi.getAnalysisResult(recordId)

      if (response.data.code === '200') {
        const data = response.data.data

        if (data.status === 1) { // 完成
          // 更新列表
          const index = analysisList.value.findIndex(item => item.recordId === recordId)
          if (index !== -1) {
            analysisList.value[index] = {
              ...analysisList.value[index],
              status: 1,
              overallScore: data.overallScore,
              grade: data.grade
            }
          }

          ElMessage.success('分析完成')
          loadUserInfo() // 刷新统计
        } else if (data.status === 2) { // 失败
          const index = analysisList.value.findIndex(item => item.recordId === recordId)
          if (index !== -1) {
            analysisList.value[index].status = 2
          }
          ElMessage.error('分析失败')
        } else {
          // 继续轮询
          setTimeout(poll, 5000)
        }
      }
    } catch (error) {
      console.error('轮询失败:', error)
      setTimeout(poll, 5000)
    }
  }

  setTimeout(poll, 3000) // 3秒后开始第一次轮询
}

// 查看分析详情
const viewAnalysis = (recordId) => {
  router.push(`/analysis/${recordId}`)
}

// 跳转到个人中心
const goToProfile = () => {
  router.push('/profile')
}

// 跳转到趋势页
const goToTrend = () => {
  router.push('/trend')
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

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`

  return `${date.getMonth() + 1}月${date.getDate()}日`
}

onMounted(() => {
  loadUserInfo()
  loadAnalysisList()
})
</script>

<style scoped>
.training-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 80px;
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

.stats-cards {
  display: flex;
  gap: 10px;
  padding: 20px;
  margin-top: -10px;
}

.stat-card {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 15px;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  font-size: 32px;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 12px;
  color: #999;
}

.middle-row {
  display: flex;
  gap: 12px;
  padding: 0 20px;
  margin-bottom: 20px;
}

.calendar-section {
  flex: none;
  width: 25vw;
  min-width: 0;
  background: white;
  padding: 8px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.calendar-section h2 {
  margin: 0 0 6px 0;
  font-size: 12px;
}

.upload-section {
  flex: none;
  width: 25vw;
  min-width: 0;
  background: white;
  padding: 8px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.upload-section h2 {
  margin: 0 0 8px 0;
  font-size: 12px;
}

.upload-form {
  margin-top: 4px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-type-group {
  display: flex;
  width: 100%;
}

.action-type-group :deep(.el-radio-button) {
  flex: 1;
}

.action-type-group :deep(.el-radio-button__inner) {
  width: 100%;
}

/* 紧凑上传区域 */
.upload-form :deep(.upload-demo) {
  width: 100%;
}

.upload-form :deep(.upload-demo .el-upload) {
  width: 100%;
}

.upload-form :deep(.upload-demo .el-upload-dragger) {
  padding: 8px 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
}

.upload-inner {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
  font-size: 12px;
}

.upload-inner em {
  color: #667eea;
  font-style: normal;
}

/* 按钮居中 */
.upload-button {
  width: 100%;
  height: 34px;
  font-size: 13px;
  border-radius: 6px;
}

.results-section {
  background: white;
  margin: 20px;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.results-section h2 {
  margin: 0 0 20px 0;
  font-size: 18px;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-card {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.result-card:hover {
  background: #f0f0f0;
  transform: translateY(-2px);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.result-type {
  font-size: 16px;
  font-weight: bold;
}

.result-status {
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

.result-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-score {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.score-value {
  font-size: 24px;
  font-weight: bold;
  color: #667eea;
}

.score-label {
  font-size: 14px;
  color: #999;
}

.result-time {
  font-size: 12px;
  color: #999;
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

/* ========== 移动端适配 ========== */
@media screen and (max-width: 768px) {
  .training-container {
    padding-bottom: 70px;
  }

  /* 顶部导航 */
  .header {
    padding: 14px 16px;
  }

  .header h1 {
    font-size: 18px;
  }

  /* 统计卡片：横向滚动或堆叠 */
  .stats-cards {
    gap: 8px;
    padding: 12px 16px;
    margin-top: -6px;
  }

  .stat-card {
    padding: 10px 12px;
    border-radius: 10px;
    gap: 8px;
  }

  .stat-icon {
    font-size: 24px;
  }

  .stat-value {
    font-size: 16px;
  }

  .stat-label {
    font-size: 11px;
  }

  /* 日历 + 上传：纵向堆叠，全宽 */
  .middle-row {
    flex-direction: column;
    gap: 10px;
    padding: 0 16px;
    margin-bottom: 16px;
  }

  .calendar-section {
    width: 100%;
  }

  .upload-section {
    width: 100%;
  }

  .calendar-section h2,
  .upload-section h2 {
    font-size: 14px;
    margin-bottom: 8px;
  }

  /* 上传表单在移动端 */
  .upload-form :deep(.upload-demo .el-upload-dragger) {
    padding: 12px 16px;
  }

  .upload-inner {
    font-size: 13px;
  }

  .upload-button {
    width: 100%;
    height: 40px;
    font-size: 15px;
  }

  /* 分析记录 */
  .results-section {
    margin: 12px 16px;
    padding: 14px;
    border-radius: 10px;
  }

  .results-section h2 {
    font-size: 16px;
    margin-bottom: 12px;
  }

  .result-card {
    padding: 12px;
  }

  .result-type {
    font-size: 14px;
  }

  .score-value {
    font-size: 20px;
  }

  /* 底部导航 */
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

/* 小屏手机 (<375px) */
@media screen and (max-width: 375px) {
  .header h1 {
    font-size: 16px;
  }
}
</style>
