const { videoApi } = require('../../utils/api')

Page({
  data: {
    loading: true,
    records: [],
    latestSpeed: '--',
    maxSpeed: '--',
    avgSpeed: '--',
    hasLeftRight: false
  },

  onLoad() {
    this.loadData()
  },

  onShow() {
    if (!this.data.loading && this.data.records.length > 0) {
      this.loadData()
    }
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const res = await videoApi.getVideoRecords({
        pageNum: 1,
        pageSize: 30,
        status: 1,
        actionType: 'batting',
        sortBy: 'createTime',
        sortOrder: 'asc'
      })

      if (res.code === '200') {
        const raw = res.data.records || res.data.list || []
        const records = raw
          .filter(r => r.maxBatSpeedKmH != null)
          .map(r => {
            const d = new Date(r.createTime)
            return {
              recordId: r.recordId,
              dateText: (d.getMonth() + 1) + '/' + d.getDate(),
              batSpeed: r.maxBatSpeedKmH || 0,
              batSpeedText: r.maxBatSpeedKmH ? r.maxBatSpeedKmH.toFixed(1) : '--',
              leftSpeed: r.leftSpeedKmH || 0,
              leftSpeedText: r.leftSpeedKmH ? r.leftSpeedKmH.toFixed(1) : '--',
              rightSpeed: r.rightSpeedKmH || 0,
              rightSpeedText: r.rightSpeedKmH ? r.rightSpeedKmH.toFixed(1) : '--'
            }
          })

        const hasLeftRight = records.some(r => r.leftSpeed > 0 || r.rightSpeed > 0)

        if (records.length > 0) {
          const speeds = records.map(r => r.batSpeed)
          const latest = speeds[speeds.length - 1].toFixed(1)
          const max = Math.max(...speeds).toFixed(1)
          const avg = (speeds.reduce((a, b) => a + b, 0) / speeds.length).toFixed(1)

          this.setData({
            records,
            latestSpeed: latest,
            maxSpeed: max,
            avgSpeed: avg,
            hasLeftRight: hasLeftRight
          })

          // 延迟绘制图表，等 canvas 就绪
          setTimeout(() => this.drawChart(records, hasLeftRight), 100)
        } else {
          this.setData({ records: [] })
        }
      }
    } catch (e) {
      console.error('加载趋势数据失败:', e)
    } finally {
      this.setData({ loading: false })
    }
  },

  drawChart(records, hasLeftRight) {
    const query = wx.createSelectorQuery()
    query.select('#trendChart')
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res[0]) return
        const canvas = res[0].node
        const ctx = canvas.getContext('2d')
        const dpr = wx.getWindowInfo().pixelRatio
        canvas.width = res[0].width * dpr
        canvas.height = res[0].height * dpr
        ctx.scale(dpr, dpr)

        const W = res[0].width
        const H = res[0].height
        const pad = { top: 20, right: 16, bottom: 30, left: 40 }
        const plotW = W - pad.left - pad.right
        const plotH = H - pad.top - pad.bottom

        // 数据范围
        const allVals = records.map(r => r.batSpeed)
        if (hasLeftRight) {
          records.forEach(r => {
            if (r.leftSpeed > 0) allVals.push(r.leftSpeed)
            if (r.rightSpeed > 0) allVals.push(r.rightSpeed)
          })
        }
        const minV = Math.floor(Math.min(...allVals) * 0.9)
        const maxV = Math.ceil(Math.max(...allVals) * 1.1)
        const range = maxV - minV || 1
        const n = records.length

        const xStep = n > 1 ? plotW / (n - 1) : plotW
        const toX = (i) => pad.left + (n > 1 ? i * xStep : plotW / 2)
        const toY = (v) => pad.top + plotH - ((v - minV) / range) * plotH

        // 清空
        ctx.clearRect(0, 0, W, H)

        // 网格线
        ctx.strokeStyle = '#eee'
        ctx.lineWidth = 0.5
        for (let i = 0; i <= 4; i++) {
          const y = pad.top + (plotH / 4) * i
          ctx.beginPath()
          ctx.moveTo(pad.left, y)
          ctx.lineTo(W - pad.right, y)
          ctx.stroke()

          // Y轴标签
          const val = maxV - (range / 4) * i
          ctx.fillStyle = '#999'
          ctx.font = '10px sans-serif'
          ctx.textAlign = 'right'
          ctx.fillText(val.toFixed(0), pad.left - 6, y + 4)
        }

        // X轴标签（最多显示8个）
        ctx.fillStyle = '#999'
        ctx.font = '10px sans-serif'
        ctx.textAlign = 'center'
        const labelStep = Math.max(1, Math.ceil(n / 8))
        for (let i = 0; i < n; i += labelStep) {
          ctx.fillText(records[i].dateText, toX(i), H - 6)
        }

        // 绘制线条函数
        const drawLine = (data, color, key) => {
          ctx.strokeStyle = color
          ctx.lineWidth = 2
          ctx.lineJoin = 'round'
          ctx.beginPath()
          let started = false
          for (let i = 0; i < n; i++) {
            const v = data[i][key]
            if (v <= 0) continue
            const x = toX(i)
            const y = toY(v)
            if (!started) { ctx.moveTo(x, y); started = true }
            else ctx.lineTo(x, y)
          }
          ctx.stroke()

          // 数据点
          ctx.fillStyle = color
          for (let i = 0; i < n; i++) {
            const v = data[i][key]
            if (v <= 0) continue
            ctx.beginPath()
            ctx.arc(toX(i), toY(v), 3, 0, Math.PI * 2)
            ctx.fill()
          }
        }

        drawLine(records, '#667eea', 'batSpeed')
        if (hasLeftRight) {
          drawLine(records, '#42b8dd', 'leftSpeed')
          drawLine(records, '#f56c6c', 'rightSpeed')
        }
      })
  }
})
