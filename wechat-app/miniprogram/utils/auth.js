const TOKEN_KEY = 'baseball_token'
const USER_KEY = 'baseball_user'

function getToken() {
  return wx.getStorageSync(TOKEN_KEY) || ''
}

function getUserInfo() {
  const info = wx.getStorageSync(USER_KEY)
  return info ? (typeof info === 'string' ? JSON.parse(info) : info) : null
}

function saveLoginInfo(token, userInfo) {
  wx.setStorageSync(TOKEN_KEY, token)
  wx.setStorageSync(USER_KEY, userInfo)
}

function clearLoginInfo() {
  wx.removeStorageSync(TOKEN_KEY)
  wx.removeStorageSync(USER_KEY)
}

function isLoggedIn() {
  return !!getToken()
}

module.exports = { getToken, getUserInfo, saveLoginInfo, clearLoginInfo, isLoggedIn }
