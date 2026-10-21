const { videoApi } = require('../../utils/api')

Page({
  data: {
    recordId: '',
    loading: true,
    result: null,
    statusText: '',
    videoUrl: '',
    loadingVideo: false
  },

  onLoad(options) {
    this.setData({ recordId: options.recordId })
    this.loadResult()
  },

  async loadResult() {
    this.setData({ loading: true })
    try {
      const res = await videoApi.getAnalysisResult(this.data.recordId)
      if (res.code === '200') {
        const d = res.data
        const statusMap = { 0: '分析中', 1: '已完成', 2: '失败' }
        this.setData({
          result: d,
          statusText: statusMap[d.status] || '未知'
        })
        // 分析中则继续轮询
        if (d.status === 0) {
          setTimeout(() => this.loadResult(), 5000)
        }
      } else {
        wx.showToast({ title: res.message || '加载失败', icon: 'none' })
      }
    } catch (e) {
      wx.showToast({ title: '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  async loadVideo() {
    const name = this.data.result && this.data.result.skeletonVideoName
    if (!name || this.data.loadingVideo) return

    this.setData({ loadingVideo: true })
    try {
      const res = await videoApi.getVideoDownloadUrl(name)
      if (res.code === '200') {
        this.setData({ videoUrl: res.data.downloadUrl })
      } else {
        wx.showToast({ title: '加载视频失败', icon: 'none' })
      }
    } catch (e) {
      wx.showToast({ title: '加载视频失败', icon: 'none' })
    } finally {
      this.setData({ loadingVideo: false })
    }
  }
})
