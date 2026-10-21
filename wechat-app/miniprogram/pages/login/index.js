const { userApi } = require('../../utils/api')
const { saveLoginInfo } = require('../../utils/auth')

Page({
  data: {
    phone: '',
    code: '',
    loading: false,
    codeSending: false,
    countdown: 60
  },

  onPhoneInput(e) { this.setData({ phone: e.detail.value }) },
  onCodeInput(e) { this.setData({ code: e.detail.value }) },

  sendCode() {
    if (!/^1[3-9]\d{9}$/.test(this.data.phone)) {
      wx.showToast({ title: '请输入正确的手机号', icon: 'none' })
      return
    }
    // TODO: 调用发送验证码接口
    wx.showToast({ title: '验证码已发送', icon: 'success' })
    this.setData({ codeSending: true, countdown: 60 })
    this._timer = setInterval(() => {
      if (this.data.countdown <= 1) {
        clearInterval(this._timer)
        this.setData({ codeSending: false, countdown: 60 })
      } else {
        this.setData({ countdown: this.data.countdown - 1 })
      }
    }, 1000)
  },

  async phoneLogin() {
    if (!this.data.phone || !this.data.code) {
      wx.showToast({ title: '请填写手机号和验证码', icon: 'none' })
      return
    }
    this.setData({ loading: true })
    try {
      const res = await userApi.phoneLogin(this.data.phone, this.data.code)
      if (res.code === '200') {
        const { token, userId, nickname, avatarUrl } = res.data
        saveLoginInfo(token, { userId, nickname, avatarUrl })
        wx.showToast({ title: '登录成功', icon: 'success' })
        wx.switchTab({ url: '/pages/training/index' })
      } else {
        wx.showToast({ title: res.message || '登录失败', icon: 'none' })
      }
    } catch (e) {
      wx.showToast({ title: '登录失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  async wechatLogin(e) {
    if (e.detail.errMsg !== 'getPhoneNumber:ok') return
    // 获取微信手机号后调用后端登录
    wx.login({
      success: async (loginRes) => {
        if (loginRes.code) {
          try {
            const res = await userApi.wechatLogin(loginRes.code)
            if (res.code === '200') {
              const { token, userId, nickname, avatarUrl } = res.data
              saveLoginInfo(token, { userId, nickname, avatarUrl })
              wx.showToast({ title: '登录成功', icon: 'success' })
              wx.switchTab({ url: '/pages/training/index' })
            } else {
              wx.showToast({ title: res.message || '登录失败', icon: 'none' })
            }
          } catch (err) {
            wx.showToast({ title: '登录失败', icon: 'none' })
          }
        }
      }
    })
  },

  goToRegister() {
    wx.navigateTo({ url: '/pages/register/index' })
  }
})
