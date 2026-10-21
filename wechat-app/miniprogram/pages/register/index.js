const { userApi } = require('../../utils/api')
const { saveLoginInfo } = require('../../utils/auth')

Page({
  data: {
    phone: '',
    code: '',
    nickname: '',
    password: '',
    gender: 0,
    loading: false,
    codeSending: false,
    countdown: 60
  },

  onPhoneInput(e) { this.setData({ phone: e.detail.value }) },
  onCodeInput(e) { this.setData({ code: e.detail.value }) },
  onNicknameInput(e) { this.setData({ nickname: e.detail.value }) },
  onPasswordInput(e) { this.setData({ password: e.detail.value }) },

  selectGender(e) {
    this.setData({ gender: parseInt(e.currentTarget.dataset.value) })
  },

  goBack() {
    wx.navigateBack()
  },

  goToLogin() {
    wx.redirectTo({ url: '/pages/login/index' })
  },

  async sendCode() {
    const { phone, codeSending } = this.data
    if (codeSending) return
    if (!phone || !/^1[3-9]\d{9}$/.test(phone)) {
      wx.showToast({ title: '请输入正确的手机号', icon: 'none' })
      return
    }

    // TODO: 调用发送验证码接口
    wx.showToast({ title: '验证码发送功能待实现', icon: 'none' })

    this.setData({ codeSending: true, countdown: 60 })
    this._timer = setInterval(() => {
      const c = this.data.countdown - 1
      if (c <= 0) {
        clearInterval(this._timer)
        this.setData({ codeSending: false, countdown: 60 })
      } else {
        this.setData({ countdown: c })
      }
    }, 1000)
  },

  async doRegister() {
    const { phone, code, nickname, password, gender, loading } = this.data
    if (loading) return

    if (!phone || !/^1[3-9]\d{9}$/.test(phone)) {
      wx.showToast({ title: '请输入正确的手机号', icon: 'none' })
      return
    }
    if (!code) {
      wx.showToast({ title: '请输入验证码', icon: 'none' })
      return
    }
    if (!nickname || nickname.length < 1) {
      wx.showToast({ title: '请输入昵称', icon: 'none' })
      return
    }
    if (!password || password.length < 6 || password.length > 20) {
      wx.showToast({ title: '密码长度需在6-20位之间', icon: 'none' })
      return
    }

    this.setData({ loading: true })
    try {
      const res = await userApi.register(phone, code, password, nickname, gender)
      if (res.code === '200') {
        const { token, userId, nickname: nick, avatarUrl } = res.data
        saveLoginInfo(token, { userId, nickname: nick, avatarUrl })
        wx.showToast({ title: '注册成功', icon: 'success' })
        setTimeout(() => {
          wx.switchTab({ url: '/pages/training/index' })
        }, 1000)
      } else {
        wx.showToast({ title: res.message || '注册失败', icon: 'none' })
      }
    } catch (err) {
      wx.showToast({ title: '注册失败：' + (err.message || '网络错误'), icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  onUnload() {
    if (this._timer) clearInterval(this._timer)
  }
})
