import axios from 'axios'

const API_BASE = '/api'

export const userApi = {
  // 微信登录
  wechatLogin(code, platform = 'wechat') {
    return axios.post(`${API_BASE}/user/login/wechat?platform=${platform}`, { code })
  },

  // 手机号登录
  phoneLogin(phone, code, platform = 'app') {
    return axios.post(`${API_BASE}/user/login/phone?platform=${platform}`, { phone, code })
  },

  // 用户注册
  register(phone, code, password, nickname, gender = 0, platform = 'app') {
    return axios.post(`${API_BASE}/user/register?platform=${platform}`, {
      phone, code, password, nickname, gender
    })
  },

  // 获取用户信息
  getUserInfo() {
    return axios.get(`${API_BASE}/user/info`)
  },

  // 更新用户信息
  updateUserInfo(data) {
    return axios.put(`${API_BASE}/user/update`, data)
  },

  // 获取用户积分
  getUserPoints() {
    return axios.get(`${API_BASE}/user/points`)
  },

  // 获取积分记录
  getPointsLog(page = 1, size = 10) {
    return axios.get(`${API_BASE}/user/points/log`, { params: { page, size } })
  }
}

export const videoApi = {
  // 上传视频分析
  uploadVideo(file, userId, actionType = 'batting') {
    const formData = new FormData()
    formData.append('video', file)
    formData.append('userId', userId)
    formData.append('actionType', actionType)

    return axios.post(`${API_BASE}/video/analyze`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 获取分析结果
  getAnalysisResult(recordId) {
    return axios.get(`${API_BASE}/video/result/${recordId}`)
  },

  // 获取视频下载链接
  getVideoDownloadUrl(fileName) {
    return axios.get(`${API_BASE}/video/download`, {
      params: { fileName }
    })
  },

  // 查询用户视频记录（分页）
  getVideoRecords(params) {
    return axios.post(`${API_BASE}/video/records`, params)
  },

  // 查询每日记录数（日历展示）
  getDailyRecordCount(year, month) {
    return axios.get(`${API_BASE}/video/records/daily-count`, {
      params: { year, month }
    })
  },

  // 查询某天的所有记录
  getDailyRecords(date) {
    return axios.get(`${API_BASE}/video/records/daily-records`, {
      params: { date }
    })
  }
}
