<template>
  <div class="login-container">
    <div class="login-header">
      <h1>🏏 棒球动作分析</h1>
      <p>专业的棒球动作分析系统</p>
    </div>

    <div class="login-form">
      <!-- 登录方式切换 -->
      <div class="login-tabs">
        <div 
          :class="['tab', { active: loginType === 'phone' }]" 
          @click="loginType = 'phone'"
        >
          手机号登录
        </div>
        <div 
          :class="['tab', { active: loginType === 'wechat' }]" 
          @click="loginType = 'wechat'"
        >
          微信登录
        </div>
      </div>

      <!-- 手机号登录 -->
      <div v-if="loginType === 'phone'" class="form-content">
        <el-form :model="phoneForm" :rules="phoneRules" ref="phoneFormRef">
          <el-form-item prop="phone">
            <el-input 
              v-model="phoneForm.phone" 
              placeholder="请输入手机号"
              prefix-icon="Phone"
              maxlength="11"
            />
          </el-form-item>
          <el-form-item prop="code">
            <div class="code-input">
              <el-input 
                v-model="phoneForm.code" 
                placeholder="请输入验证码"
                maxlength="6"
              />
              <el-button 
                @click="sendCode" 
                :disabled="codeSending"
                type="primary"
              >
                {{ codeSending ? `${codeCountdown}s` : '获取验证码' }}
              </el-button>
            </div>
          </el-form-item>
          <el-form-item>
            <el-button 
              type="primary" 
              @click="phoneLogin" 
              :loading="loading"
              class="login-button"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 微信登录 -->
      <div v-else class="form-content">
        <div class="wechat-login">
          <el-icon :size="80" color="#07C160"><ChatDotRound /></el-icon>
          <p class="wechat-tip">点击下方按钮进行微信登录</p>
          <el-button 
            type="success" 
            @click="wechatLogin" 
            :loading="loading"
            class="login-button"
          >
            微信一键登录
          </el-button>
        </div>
      </div>

      <!-- 注册链接 -->
      <div class="register-link">
        还没有账号？
        <el-link type="primary" @click="goToRegister">立即注册</el-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Phone, ChatDotRound } from '@element-plus/icons-vue'
import { userApi } from '../utils/api'
import { auth } from '../utils/auth'

const router = useRouter()

// 登录类型
const loginType = ref('phone')
const loading = ref(false)

// 手机号登录表单
const phoneFormRef = ref(null)
const phoneForm = reactive({
  phone: '',
  code: ''
})

const phoneRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' }
  ]
}

// 验证码发送
const codeSending = ref(false)
const codeCountdown = ref(60)

const sendCode = async () => {
  if (!phoneForm.phone) {
    ElMessage.warning('请先输入手机号')
    return
  }
  
  // TODO: 调用发送验证码接口
  ElMessage.info('验证码发送功能待实现')
  
  codeSending.value = true
  const timer = setInterval(() => {
    codeCountdown.value--
    if (codeCountdown.value <= 0) {
      clearInterval(timer)
      codeSending.value = false
      codeCountdown.value = 60
    }
  }, 1000)
}

// 手机号登录
const phoneLogin = async () => {
  const valid = await phoneFormRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const response = await userApi.phoneLogin(phoneForm.phone, phoneForm.code)
    
    if (response.data.code === '200') {
      const { token, userId, nickname, avatarUrl } = response.data.data
      
      auth.saveLoginInfo(token, { userId, nickname, avatarUrl })
      
      ElMessage.success('登录成功')
      router.push('/')
    } else {
      ElMessage.error(response.data.message || '登录失败')
    }
  } catch (error) {
    ElMessage.error('登录失败：' + (error.response?.data?.message || error.message))
  } finally {
    loading.value = false
  }
}

// 微信登录
const wechatLogin = async () => {
  loading.value = true
  try {
    // TODO: 调用微信 SDK 获取 code
    const code = 'mock_wechat_code'
    
    const response = await userApi.wechatLogin(code)
    
    if (response.data.code === '200') {
      const { token, userId, nickname, avatarUrl } = response.data.data
      
      auth.saveLoginInfo(token, { userId, nickname, avatarUrl })
      
      ElMessage.success('登录成功')
      router.push('/')
    } else {
      ElMessage.error(response.data.message || '登录失败')
    }
  } catch (error) {
    ElMessage.error('登录失败：' + (error.response?.data?.message || error.message))
  } finally {
    loading.value = false
  }
}

// 跳转到注册页
const goToRegister = () => {
  router.push('/register')
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.login-header {
  text-align: center;
  color: white;
  padding: 60px 0 40px;
}

.login-header h1 {
  font-size: 32px;
  margin-bottom: 10px;
}

.login-header p {
  font-size: 16px;
  opacity: 0.9;
}

.login-form {
  background: white;
  border-radius: 16px;
  padding: 30px 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.login-tabs {
  display: flex;
  margin-bottom: 30px;
  border-bottom: 2px solid #f0f0f0;
}

.tab {
  flex: 1;
  text-align: center;
  padding: 12px;
  cursor: pointer;
  font-size: 16px;
  color: #666;
  transition: all 0.3s;
}

.tab.active {
  color: #667eea;
  border-bottom: 2px solid #667eea;
  margin-bottom: -2px;
}

.form-content {
  min-height: 200px;
}

.code-input {
  display: flex;
  gap: 10px;
}

.code-input .el-input {
  flex: 1;
}

.login-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
}

.wechat-login {
  text-align: center;
  padding: 40px 0;
}

.wechat-tip {
  margin: 20px 0;
  color: #666;
}

.register-link {
  text-align: center;
  margin-top: 20px;
  color: #666;
}

@media screen and (max-width: 768px) {
  .login-header h1 {
    font-size: 24px;
  }
  
  .login-form {
    padding: 20px 15px;
  }
}
</style>
