<template>
  <div class="register-container">
    <div class="register-header">
      <div class="back-btn" @click="goBack">
        <el-icon :size="24"><ArrowLeft /></el-icon>
      </div>
      <h1>注册账号</h1>
      <div style="width: 40px"></div>
    </div>

    <div class="register-form">
      <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
        <!-- 手机号 -->
        <el-form-item label="手机号" prop="phone">
          <el-input
            v-model="form.phone"
            placeholder="请输入手机号"
            maxlength="11"
            type="tel"
            clearable
          >
            <template #prefix>
              <span class="phone-prefix">+86</span>
            </template>
          </el-input>
        </el-form-item>

        <!-- 验证码 -->
        <el-form-item label="验证码" prop="code">
          <div class="code-row">
            <el-input
              v-model="form.code"
              placeholder="请输入验证码"
              maxlength="6"
              type="tel"
            />
            <el-button
              @click="sendCode"
              :disabled="codeSending"
              type="primary"
              plain
              class="code-btn"
            >
              {{ codeSending ? `${codeCountdown}s` : '获取验证码' }}
            </el-button>
          </div>
        </el-form-item>

        <!-- 用户名 -->
        <el-form-item label="用户名" prop="nickname">
          <el-input
            v-model="form.nickname"
            placeholder="请输入用户名"
            maxlength="20"
            clearable
          />
        </el-form-item>

        <!-- 密码 -->
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码（6-20位）"
            show-password
            maxlength="20"
          />
        </el-form-item>

        <!-- 注册按钮 -->
        <el-form-item class="submit-item">
          <el-button
            type="primary"
            @click="submitRegister"
            :loading="loading"
            class="register-button"
          >
            注册
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 跳转登录 -->
      <div class="login-link">
        已有账号？
        <el-link type="primary" @click="goToLogin">立即登录</el-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { userApi } from '../utils/api'
import { auth } from '../utils/auth'

const router = useRouter()
const route = useRoute()

const formRef = ref(null)
const loading = ref(false)

// 平台检测：web / wechat
const platform = ref('app')

const form = reactive({
  phone: '',
  code: '',
  nickname: '',
  password: ''
})

const rules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码为6位数字', trigger: 'blur' }
  ],
  nickname: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度2-20个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度6-20位', trigger: 'blur' }
  ]
}

// 验证码
const codeSending = ref(false)
const codeCountdown = ref(60)

const sendCode = async () => {
  if (!form.phone || !/^1[3-9]\d{9}$/.test(form.phone)) {
    ElMessage.warning('请先输入正确的手机号')
    return
  }

  // TODO: 调用发送验证码接口
  ElMessage.info('验证码发送功能待实现')

  codeSending.value = true
  codeCountdown.value = 60
  const timer = setInterval(() => {
    codeCountdown.value--
    if (codeCountdown.value <= 0) {
      clearInterval(timer)
      codeSending.value = false
      codeCountdown.value = 60
    }
  }, 1000)
}

// 提交注册
const submitRegister = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const response = await userApi.register(
      form.phone,
      form.code,
      form.password,
      form.nickname,
      0,
      platform.value
    )

    if (response.data.code === '200' || response.data.code === 0) {
      const { token, userId, nickname, avatarUrl } = response.data.data

      auth.saveLoginInfo(token, { userId, nickname, avatarUrl })

      ElMessage.success('注册成功')
      router.push('/')
    } else {
      ElMessage.error(response.data.message || '注册失败')
    }
  } catch (error) {
    ElMessage.error('注册失败：' + (error.response?.data?.message || error.message))
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.back()
}

const goToLogin = () => {
  router.replace('/login')
}

onMounted(() => {
  // 检测是否在微信小程序环境中
  if (typeof wx !== 'undefined' && wx.miniProgram) {
    platform.value = 'wechat'
  }

  // 如果从 URL 带了 platform 参数
  if (route.query.platform) {
    platform.value = route.query.platform
  }
})
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding-bottom: 40px;
}

.register-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  color: white;
}

.register-header h1 {
  font-size: 20px;
  margin: 0;
}

.back-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 50%;
  transition: background 0.3s;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.15);
}

.register-form {
  background: white;
  margin: 0 20px;
  border-radius: 16px;
  padding: 30px 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.phone-prefix {
  color: #666;
  font-size: 14px;
  font-weight: 500;
  padding-left: 4px;
}

.code-row {
  display: flex;
  gap: 10px;
  width: 100%;
}

.code-row .el-input {
  flex: 1;
}

.code-btn {
  flex-shrink: 0;
  width: 120px;
}

.submit-item {
  margin-top: 10px;
  margin-bottom: 0;
}

.register-button {
  width: 100%;
  height: 46px;
  font-size: 16px;
  border-radius: 8px;
}

.login-link {
  text-align: center;
  margin-top: 20px;
  color: #666;
  font-size: 14px;
}

/* 移动端适配 */
@media screen and (max-width: 768px) {
  .register-header {
    padding: 14px 16px;
  }

  .register-header h1 {
    font-size: 18px;
  }

  .register-form {
    margin: 0 12px;
    padding: 24px 16px;
    border-radius: 12px;
  }

  .code-btn {
    width: 110px;
    font-size: 13px;
  }
}

/* 小屏手机 */
@media screen and (max-width: 375px) {
  .register-form {
    margin: 0 8px;
    padding: 20px 12px;
  }
}
</style>
