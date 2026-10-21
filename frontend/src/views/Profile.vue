<template>
  <div class="profile-container">
    <!-- 顶部用户信息 -->
    <div class="profile-header">
      <div class="user-avatar">
        <el-avatar :size="80" :src="userInfo?.avatarUrl">
          {{ userInfo?.nickname?.charAt(0) || 'U' }}
        </el-avatar>
      </div>
      <div class="user-name">{{ userInfo?.nickname || '用户' }}</div>
      <div class="user-id">ID: {{ userInfo?.userId }}</div>
    </div>

    <!-- 统计信息 -->
    <div class="stats-section">
      <div class="stat-item">
        <div class="stat-value">{{ stats.totalAnalysis }}</div>
        <div class="stat-label">分析次数</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ stats.points }}</div>
        <div class="stat-label">积分</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">VIP{{ stats.vipLevel }}</div>
        <div class="stat-label">会员等级</div>
      </div>
    </div>

    <!-- 功能菜单 -->
    <div class="menu-section">
      <div class="menu-item" @click="showEditProfile = true">
        <el-icon><Edit /></el-icon>
        <span>编辑资料</span>
        <el-icon class="arrow"><ArrowRight /></el-icon>
      </div>
      <div class="menu-item" @click="showPointsLog = true">
        <el-icon><Coin /></el-icon>
        <span>积分记录</span>
        <el-icon class="arrow"><ArrowRight /></el-icon>
      </div>
      <div class="menu-item">
        <el-icon><Setting /></el-icon>
        <span>设置</span>
        <el-icon class="arrow"><ArrowRight /></el-icon>
      </div>
      <div class="menu-item">
        <el-icon><InfoFilled /></el-icon>
        <span>关于</span>
        <el-icon class="arrow"><ArrowRight /></el-icon>
      </div>
    </div>

    <!-- 退出登录 -->
    <div class="logout-section">
      <el-button type="danger" @click="handleLogout" class="logout-button">
        退出登录
      </el-button>
    </div>

    <!-- 底部导航 -->
    <div class="bottom-nav">
      <div class="nav-item" @click="goToTraining">
        <el-icon><HomeFilled /></el-icon>
        <span>训练</span>
      </div>
      <div class="nav-item" @click="goToTrend">
        <el-icon><TrendCharts /></el-icon>
        <span>趋势</span>
      </div>
      <div class="nav-item active">
        <el-icon><User /></el-icon>
        <span>我的</span>
      </div>
    </div>

    <!-- 编辑资料弹窗 -->
    <el-dialog v-model="showEditProfile" title="编辑资料" width="90%">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="昵称">
          <el-input v-model="editForm.nickname" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="editForm.gender">
            <el-radio :label="0">未知</el-radio>
            <el-radio :label="1">男</el-radio>
            <el-radio :label="2">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="生日">
          <el-date-picker 
            v-model="editForm.birthday" 
            type="date" 
            placeholder="选择生日"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" type="email" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditProfile = false">取消</el-button>
        <el-button type="primary" @click="saveProfile" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 积分记录弹窗 -->
    <el-dialog v-model="showPointsLog" title="积分记录" width="90%">
      <div class="points-log-list">
        <div v-if="pointsLog.length === 0" class="empty-tip">暂无积分记录</div>
        <div v-for="log in pointsLog" :key="log.id" class="points-log-item">
          <div class="log-info">
            <div class="log-reason">{{ log.reason || '积分变动' }}</div>
            <div class="log-time">{{ formatTime(log.createTime) }}</div>
          </div>
          <div :class="['log-points', log.points > 0 ? 'positive' : 'negative']">
            {{ log.points > 0 ? '+' : '' }}{{ log.points }}
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, ArrowRight, Coin, Setting, InfoFilled, HomeFilled, User, TrendCharts } from '@element-plus/icons-vue'
import { userApi } from '../utils/api'
import { auth } from '../utils/auth'

const router = useRouter()

// 用户信息
const userInfo = ref(auth.getUserInfo())

// 统计数据
const stats = reactive({
  totalAnalysis: 0,
  points: 0,
  vipLevel: 0
})

// 编辑资料
const showEditProfile = ref(false)
const saving = ref(false)
const editForm = reactive({
  nickname: '',
  gender: 0,
  birthday: '',
  email: ''
})

// 积分记录
const showPointsLog = ref(false)
const pointsLog = ref([])

// 加载用户信息
const loadUserInfo = async () => {
  try {
    const response = await userApi.getUserInfo()
    if (response.data.code === '200') {
      const data = response.data.data
      userInfo.value = {
        userId: data.id,
        nickname: data.nickname,
        avatarUrl: data.avatarUrl
      }
      stats.totalAnalysis = data.totalAnalysisCount || 0
      stats.points = data.points || 0
      stats.vipLevel = data.vipLevel || 0
      
      // 填充编辑表单
      editForm.nickname = data.nickname
      editForm.gender = data.gender || 0
      editForm.birthday = data.birthday
      editForm.email = data.email
    }
  } catch (error) {
    console.error('加载用户信息失败:', error)
  }
}

// 加载积分记录
const loadPointsLog = async () => {
  try {
    const response = await userApi.getPointsLog(1, 20)
    if (response.data.code === '200') {
      pointsLog.value = response.data.data || []
    }
  } catch (error) {
    console.error('加载积分记录失败:', error)
  }
}

// 保存资料
const saveProfile = async () => {
  saving.value = true
  try {
    const response = await userApi.updateUserInfo({
      nickname: editForm.nickname,
      gender: editForm.gender,
      birthday: editForm.birthday,
      email: editForm.email
    })
    
    if (response.data.code === '200') {
      ElMessage.success('保存成功')
      showEditProfile.value = false
      loadUserInfo()
    } else {
      ElMessage.error(response.data.message || '保存失败')
    }
  } catch (error) {
    ElMessage.error('保存失败：' + (error.response?.data?.message || error.message))
  } finally {
    saving.value = false
  }
}

// 退出登录
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    auth.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 用户取消
  }
}

// 跳转到训练页
const goToTraining = () => {
  router.push('/')
}

// 跳转到趋势页
const goToTrend = () => {
  router.push('/trend')
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

onMounted(() => {
  loadUserInfo()
  loadPointsLog()
})
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 80px;
}

.profile-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px 20px;
  text-align: center;
}

.user-avatar {
  margin-bottom: 15px;
}

.user-name {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.user-id {
  font-size: 14px;
  opacity: 0.9;
}

.stats-section {
  background: white;
  margin: 20px;
  padding: 20px;
  border-radius: 12px;
  display: flex;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.stat-item {
  flex: 1;
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #667eea;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 12px;
  color: #999;
}

.menu-section {
  background: white;
  margin: 20px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.3s;
}

.menu-item:last-child {
  border-bottom: none;
}

.menu-item:hover {
  background: #f9f9f9;
}

.menu-item .el-icon {
  font-size: 20px;
  color: #667eea;
  margin-right: 15px;
}

.menu-item span {
  flex: 1;
  font-size: 16px;
}

.menu-item .arrow {
  color: #ccc;
  margin-right: 0;
}

.logout-section {
  margin: 20px;
}

.logout-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
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

.points-log-list {
  max-height: 400px;
  overflow-y: auto;
}

.empty-tip {
  text-align: center;
  padding: 40px;
  color: #999;
}

.points-log-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.points-log-item:last-child {
  border-bottom: none;
}

.log-info {
  flex: 1;
}

.log-reason {
  font-size: 14px;
  color: #333;
  margin-bottom: 5px;
}

.log-time {
  font-size: 12px;
  color: #999;
}

.log-points {
  font-size: 18px;
  font-weight: bold;
}

.log-points.positive {
  color: #52c41a;
}

.log-points.negative {
  color: #f5222d;
}

@media screen and (max-width: 768px) {
  .profile-header {
    padding: 30px 15px;
  }
  
  .user-name {
    font-size: 20px;
  }
}
</style>
