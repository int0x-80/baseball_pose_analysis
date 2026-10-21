import axios from 'axios'

const TOKEN_KEY = 'baseball_token'
const USER_KEY = 'baseball_user'

export const auth = {
  // 保存登录信息
  saveLoginInfo(token, userInfo) {
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(USER_KEY, JSON.stringify(userInfo))
    
    // 设置 axios 默认 token
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
  },

  // 获取 token
  getToken() {
    return localStorage.getItem(TOKEN_KEY)
  },

  // 获取用户信息
  getUserInfo() {
    const userStr = localStorage.getItem(USER_KEY)
    return userStr ? JSON.parse(userStr) : null
  },

  // 检查是否已登录
  isLoggedIn() {
    return !!this.getToken()
  },

  // 登出
  logout() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    delete axios.defaults.headers.common['Authorization']
  },

  // 初始化 axios token
  initToken() {
    const token = this.getToken()
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
  }
}
