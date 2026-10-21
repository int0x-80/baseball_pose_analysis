const { videoApi, userApi } = require('../../utils/api')
const { getUserInfo, isLoggedIn } = require('../../utils/auth')

Page({
  data: {
    stats: { totalAnalysis: 0, points: 0, vipLevel: 0 },
    actionType: 'batting',
    videoPath: '',
    videoName: '',
    uploading: false,
    analysisList: [],
    loading: false,
    loadingMore: false,
    hasMore: false,
    pageNum: 1,
    pageSize: 10
  },

  onLoad() {
    if (!isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/index' })
      return
    }
    this.loadUserInfo()
    this.loadRecords()
  },

  onShow() {
    if (!isLoggedIn()) return
    // 每次显示时刷新记录（从分析详情返回时更新状态）
    this.refreshFirstPage()
  },

  onPullDownRefresh() {
    this.refreshFirstPage().then(() => wx.stopPullDownRefresh())
  },

  selectAction(e) {
    this.setData({ actionType: e.currentTarget.dataset.type })
  },

  chooseVideo() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['video'],
      sourceType: ['album', 'camera'],
      maxDuration: 60,
      success: (res) => {
        const file = res.tempFiles[0]
        const path = file.tempFilePath
        const name = path.split('/').pop() || 'video.mp4'
        this.setData({ videoPath: path, videoName: name })
      }
    })
  },

  removeVideo() {
    this.setData({ videoPath: '', videoName: '' })
  },

  async loadUserInfo() {
    try {
      const res = await userApi.getUserInfo()
      if (res.code === '200') {
        const d = res.data
        this.setData({
          'stats.totalAnalysis': d.totalAnalysisCount || 0,
          'stats.points': d.points || 0,
          'stats.vipLevel': d.vipLevel || 0
        })
      }
    } catch (e) {
      console.error('加载用户信息失败:', e)
    }
  },

  async loadRecords() {
    this.setData({ loading: true })
    try {
      const res = await videoApi.getVideoRecords({
        pageNum: 1,
        pageSize: this.data.pageSize,
        actionType: 'batting'
      })
      if (res.code === '200') {
        const data = res.data
        const list = (data.records || data.list || []).map(item => this.formatRecord(item))
        this.setData({
          analysisList: list,
          pageNum: 1,
          hasMore: list.length >= this.data.pageSize
        })
      }
    } catch (e) {
      console.error('加载记录失败:', e)
    } finally {
      this.setData({ loading: false })
    }
  },

  async refreshFirstPage() {
    try {
      const res = await videoApi.getVideoRecords({
        pageNum: 1,
        pageSize: this.data.pageSize,
        actionType: 'batting'
      })
      if (res.code === '200') {
        const data = res.data
        const list = (data.records || data.list || []).map(item => this.formatRecord(item))
        this.setData({
          analysisList: list,
          pageNum: 1,
          hasMore: list.length >= this.data.pageSize
        })
      }
    } catch (e) { /* silent */ }
  },

  async loadMore() {
    if (this.data.loadingMore) return
    this.setData({ loadingMore: true })
    const nextPage = this.data.pageNum + 1
    try {
      const res = await videoApi.getVideoRecords({
        pageNum: nextPage,
        pageSize: this.data.pageSize,
        actionType: 'batting'
      })
      if (res.code === '200') {
        const data = res.data
        const list = (data.records || data.list || []).map(item => this.formatRecord(item))
        this.setData({
          analysisList: [...this.data.analysisList, ...list],
          pageNum: nextPage,
          hasMore: list.length >= this.data.pageSize
        })
      }
    } catch (e) {
      console.error('加载更多失败:', e)
    } finally {
      this.setData({ loadingMore: false })
    }
  },

  formatRecord(item) {
    const statusMap = { 0: '分析中', 1: '已完成', 2: '失败' }
    return {
      recordId: item.recordId,
      type: item.type || item.actionType,
      status: item.status,
      statusText: statusMap[item.status] || '未知',
      timeText: this.formatTime(item.createTime),
      maxBatSpeedKmH: item.maxBatSpeedKmH || null
    }
  },

  formatTime(time) {
    if (!time) return ''
    const date = new Date(time)
    const now = new Date()
    const diff = now - date
    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
    if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
    return (date.getMonth() + 1) + '月' + date.getDate() + '日'
  },

  async submitUpload() {
    const { videoPath, uploading, actionType } = this.data
    if (!videoPath || uploading) return

    this.setData({ uploading: true })
    wx.showLoading({ title: '上传中...' })

    try {
      const userInfo = getUserInfo()
      const res = await videoApi.uploadVideo(videoPath, userInfo.userId, actionType)
      wx.hideLoading()

      if (res.code === 0 || res.code === '200') {
        const recordId = res.data.recordId
        wx.showToast({ title: '上传成功，开始分析', icon: 'success' })

        // 添加到列表顶部
        const newItem = this.formatRecord({
          recordId,
          actionType,
          status: 0,
          createTime: new Date().toISOString()
        })
        this.setData({
          analysisList: [newItem, ...this.data.analysisList],
          videoPath: '',
          videoName: ''
        })

        this.pollResult(recordId)
      } else {
        wx.showToast({ title: res.message || '上传失败', icon: 'none' })
      }
    } catch (e) {
      wx.hideLoading()
      wx.showToast({ title: '上传失败：' + (e.message || '网络错误'), icon: 'none' })
    } finally {
      this.setData({ uploading: false })
    }
  },

  pollResult(recordId) {
    let attempts = 0
    const maxAttempts = 60
    const poll = async () => {
      if (attempts >= maxAttempts) {
        wx.showToast({ title: '分析超时，请稍后查看', icon: 'none' })
        return
      }
      attempts++
      try {
        const res = await videoApi.getAnalysisResult(recordId)
        if (res.code === '200') {
          const d = res.data
          if (d.status === 1) {
            const idx = this.data.analysisList.findIndex(i => i.recordId === recordId)
            if (idx !== -1) {
              this.setData({
                [`analysisList[${idx}].status`]: 1,
                [`analysisList[${idx}].statusText`]: '已完成',
                [`analysisList[${idx}].maxBatSpeedKmH`]: d.maxBatSpeedKmH || null
              })
            }
            wx.showToast({ title: '分析完成', icon: 'success' })
            this.loadUserInfo()
            return
          } else if (d.status === 2) {
            const idx = this.data.analysisList.findIndex(i => i.recordId === recordId)
            if (idx !== -1) {
              this.setData({
                [`analysisList[${idx}].status`]: 2,
                [`analysisList[${idx}].statusText`]: '失败'
              })
            }
            wx.showToast({ title: '分析失败', icon: 'none' })
            return
          }
        }
      } catch (e) { /* continue polling */ }
      setTimeout(poll, 5000)
    }
    setTimeout(poll, 3000)
  },

  viewAnalysis(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: '/pages/analysis/index?recordId=' + id })
  }
})
