const { isLoggedIn } = require('./utils/auth')

App({
  onLaunch() {
    if (!isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/index' })
    }
  },
  globalData: {
    userInfo: null
  }
})
