const { request, uploadFile } = require('./request')

const userApi = {
  wechatLogin(code) {
    return request('/user/login/wechat?platform=wechat', 'POST', { code })
  },
  phoneLogin(phone, code) {
    return request('/user/login/phone?platform=wechat', 'POST', { phone, code })
  },
  register(phone, code, password, nickname, gender = 0) {
    return request('/user/register?platform=wechat', 'POST', { phone, code, password, nickname, gender })
  },
  getUserInfo() {
    return request('/user/info')
  },
  updateUserInfo(data) {
    return request('/user/update', 'PUT', data)
  },
  getUserPoints() {
    return request('/user/points')
  }
}

const videoApi = {
  uploadVideo(filePath, userId, actionType = 'batting') {
    return uploadFile(filePath, { userId, actionType })
  },
  getAnalysisResult(recordId) {
    return request('/video/result/' + recordId)
  },
  getVideoDownloadUrl(fileName) {
    return request('/video/download?fileName=' + encodeURIComponent(fileName))
  },
  getVideoRecords(params) {
    return request('/video/records', 'POST', params)
  },
  getDailyRecordCount(year, month) {
    return request('/video/records/daily-count?year=' + year + '&month=' + month)
  },
  getDailyRecords(date) {
    return request('/video/records/daily-records?date=' + date)
  }
}

module.exports = { userApi, videoApi }
