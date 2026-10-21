const { userApi } = require('../../utils/api')
const { getUserInfo, saveLoginInfo, getToken, clearLoginInfo } = require('../../utils/auth')

Page({
  data: {
    userInfo: {},
    stats: { totalAnalysis: 0, points: 0, vipLevel: 0 },
    showEditModal: false,
    showPointsModal: false,
    editForm: { nickname: '', gender: 0 },
    saving: false,
    pointsLog: []
  },

  onLoad() {
    this.loadUserInfo()
  },

  onShow() {
    this.loadUserInfo()
  },

  async loadUserInfo() {
    const stored = getUserInfo()
    if (stored) {
      this.setData({ userInfo: stored })
    }
    try {
      const res = await userApi.getUserInfo()
      if (res.code === '200') {
        const d = res.data
        const info = {
          userId: d.userId || d.id,
          nickname: d.nickname,
          avatarUrl: d.avatarUrl,
          gender: d.gender
        }
        this.setData({
          userInfo: info,
          'stats.totalAnalysis': d.totalAnalysisCount || 0,
          'stats.points': d.points || 0,
          'stats.vipLevel': d.vipLevel || 0
        })
        // 更新本地存储
        saveLoginInfo(getToken(), info)
      }
    } catch (e) {
      console.error('加载用户信息失败:', e)
    }
  },

  editProfile() {
    const { userInfo } = this.data
    this.setData({
      showEditModal: true,
      'editForm.nickname': userInfo.nickname || '',
      'editForm.gender': userInfo.gender || 0
    })
  },

  closeEditModal() {
    this.setData({ showEditModal: false })
  },

  onEditNickname(e) {
    this.setData({ 'editForm.nickname': e.detail.value })
  },

  onEditGender(e) {
    this.setData({ 'editForm.gender': parseInt(e.currentTarget.dataset.value) })
  },

  async saveProfile() {
    const { editForm, saving } = this.data
    if (saving) return
    if (!editForm.nickname.trim()) {
      wx.showToast({ title: '昵称不能为空', icon: 'none' })
      return
    }

    this.setData({ saving: true })
    try {
      const res = await userApi.updateUserInfo({
        nickname: editForm.nickname.trim(),
        gender: editForm.gender
      })
      if (res.code === '200') {
        const info = { ...this.data.userInfo, nickname: editForm.nickname.trim(), gender: editForm.gender }
        this.setData({ userInfo: info, showEditModal: false })
        saveLoginInfo(getToken(), info)
        wx.showToast({ title: '保存成功', icon: 'success' })
      } else {
        wx.showToast({ title: res.message || '保存失败', icon: 'none' })
      }
    } catch (e) {
      wx.showToast({ title: '保存失败', icon: 'none' })
    } finally {
      this.setData({ saving: false })
    }
  },

  async showPointsLog() {
    this.setData({ showPointsModal: true })
    try {
      const res = await userApi.getUserPoints()
      if (res.code === '200') {
        const list = (res.data.records || res.data.list || []).map(item => ({
          id: item.id,
          description: item.description || item.reason || '积分变动',
          amount: item.points || item.amount || 0,
          timeText: this.formatTime(item.createTime)
        }))
        this.setData({ pointsLog: list })
      }
    } catch (e) {
      console.error('加载积分记录失败:', e)
    }
  },

  closePointsModal() {
    this.setData({ showPointsModal: false })
  },

  formatTime(time) {
    if (!time) return ''
    const d = new Date(time)
    return (d.getMonth() + 1) + '月' + d.getDate() + '日 ' +
      String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0')
  },

  showAbout() {
    wx.showModal({
      title: '关于',
      content: '棒球动作分析 v1.0.0\n基于 AI 姿态识别的专业棒球训练辅助工具',
      showCancel: false
    })
  },

  logout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          clearLoginInfo()
          wx.reLaunch({ url: '/pages/login/index' })
        }
      }
    })
  }
})
