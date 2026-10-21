const { API_BASE } = require('./config')
const { getToken, clearLoginInfo } = require('./auth')

function request(url, method = 'GET', data = {}, header = {}) {
  return new Promise((resolve, reject) => {
    const token = getToken()
    const defaultHeader = {
      'Content-Type': 'application/json'
    }
    if (token) {
      defaultHeader['Authorization'] = 'Bearer ' + token
    }

    wx.request({
      url: API_BASE + url,
      method,
      data,
      header: { ...defaultHeader, ...header },
      success(res) {
        if (res.statusCode === 401) {
          clearLoginInfo()
          wx.reLaunch({ url: '/pages/login/index' })
          reject(new Error('未授权，请重新登录'))
          return
        }
        resolve(res.data)
      },
      fail(err) {
        reject(err)
      }
    })
  })
}

function uploadFile(filePath, formData) {
  return new Promise((resolve, reject) => {
    const token = getToken()
    wx.uploadFile({
      url: API_BASE + '/video/analyze',
      filePath,
      name: 'video',
      formData,
      header: {
        'Authorization': token ? 'Bearer ' + token : ''
      },
      success(res) {
        resolve(JSON.parse(res.data))
      },
      fail(err) {
        reject(err)
      }
    })
  })
}

module.exports = { request, uploadFile }
