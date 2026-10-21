const { videoApi } = require('../../utils/api')

Page({
  data: {
    date: '',
    records: [],
    loading: true
  },

  onLoad(options) {
    this.setData({ date: options.date || '' })
    if (options.date) {
      wx.setNavigationBarTitle({ title: options.date + ' 训练记录' })
    }
    this.loadRecords()
  },

  async loadRecords() {
    this.setData({ loading: true })
    try {
      const res = await videoApi.getDailyRecords(this.data.date)
      if (res.code === '200') {
        const list = (res.data || []).map(item => this.formatRecord(item))
        this.setData({ records: list })
      }
    } catch (e) {
      console.error('加载记录失败:', e)
      wx.showToast({ title: '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  formatRecord(item) {
    const statusMap = { 0: '分析中', 1: '已完成', 2: '失败' }
    const time = item.createTime ? new Date(item.createTime) : null
    return {
      recordId: item.recordId,
      type: item.type || item.actionType,
      status: item.status,
      statusText: statusMap[item.status] || '未知',
      timeText: time ? String(time.getHours()).padStart(2, '0') + ':' + String(time.getMinutes()).padStart(2, '0') : '--',
      maxBatSpeedKmH: item.maxBatSpeedKmH || null,
      leftSpeedMs: item.leftSpeedMs || null,
      rightSpeedMs: item.rightSpeedMs || null,
      maxHipRotationMm: item.maxHipRotationMm || null,
      maxTwistAngleDeg: item.maxTwistAngleDeg || null
    }
  },

  viewDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: '/pages/analysis/index?recordId=' + id })
  }
})
