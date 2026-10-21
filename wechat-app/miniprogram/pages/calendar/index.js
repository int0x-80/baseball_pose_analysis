const { videoApi } = require('../../utils/api')
const { isLoggedIn } = require('../../utils/auth')

Page({
  data: {
    currentYear: 0,
    currentMonth: 0,
    weekdays: ['日', '一', '二', '三', '四', '五', '六'],
    calendarDays: [],
    dailyRecordCount: {},
    selectedDate: '',
    loading: false
  },

  onLoad() {
    if (!isLoggedIn()) {
      wx.reLaunch({ url: '/pages/login/index' })
      return
    }
    const now = new Date()
    this.setData({
      currentYear: now.getFullYear(),
      currentMonth: now.getMonth() + 1
    })
    this.buildCalendar()
    this.loadDailyRecordCount()
  },

  prevMonth() {
    let { currentYear, currentMonth } = this.data
    if (currentMonth === 1) {
      currentYear--
      currentMonth = 12
    } else {
      currentMonth--
    }
    this.setData({ currentYear, currentMonth, selectedDate: '' })
    this.buildCalendar()
    this.loadDailyRecordCount()
  },

  nextMonth() {
    let { currentYear, currentMonth } = this.data
    if (currentMonth === 12) {
      currentYear++
      currentMonth = 1
    } else {
      currentMonth++
    }
    this.setData({ currentYear, currentMonth, selectedDate: '' })
    this.buildCalendar()
    this.loadDailyRecordCount()
  },

  formatDate(year, month, day) {
    if (month > 12) { year++; month = 1 }
    else if (month < 1) { year--; month = 12 }
    return year + '-' + String(month).padStart(2, '0') + '-' + String(day).padStart(2, '0')
  },

  buildCalendar() {
    const { currentYear: year, currentMonth: month, dailyRecordCount } = this.data
    const days = []

    const firstDay = new Date(year, month - 1, 1).getDay()
    const daysInMonth = new Date(year, month, 0).getDate()
    const daysInPrevMonth = new Date(year, month - 1, 0).getDate()

    // 上月补齐
    for (let i = firstDay - 1; i >= 0; i--) {
      const d = daysInPrevMonth - i
      days.push({
        day: d,
        date: this.formatDate(year, month - 1, d),
        currentMonth: false,
        recordCount: 0,
        isToday: false
      })
    }

    // 当月
    const today = new Date()
    for (let i = 1; i <= daysInMonth; i++) {
      const isToday = year === today.getFullYear() &&
        month === today.getMonth() + 1 &&
        i === today.getDate()
      days.push({
        day: i,
        date: this.formatDate(year, month, i),
        currentMonth: true,
        recordCount: dailyRecordCount[i] || 0,
        isToday
      })
    }

    // 下月补齐到42格
    const remaining = 42 - days.length
    for (let i = 1; i <= remaining; i++) {
      days.push({
        day: i,
        date: this.formatDate(year, month + 1, i),
        currentMonth: false,
        recordCount: 0,
        isToday: false
      })
    }

    this.setData({ calendarDays: days })
  },

  async loadDailyRecordCount() {
    this.setData({ loading: true })
    try {
      const res = await videoApi.getDailyRecordCount(this.data.currentYear, this.data.currentMonth)
      if (res.code === '200') {
        const countMap = res.data || {}
        this.setData({ dailyRecordCount: countMap })
        this.buildCalendar()
      }
    } catch (e) {
      console.error('加载日历数据失败:', e)
    } finally {
      this.setData({ loading: false })
    }
  },

  selectDate(e) {
    const { date, current } = e.currentTarget.dataset
    if (!current) return
    this.setData({ selectedDate: date })
  },

  viewDayRecords() {
    if (!this.data.selectedDate) return
    wx.navigateTo({
      url: '/pages/daily-records/index?date=' + this.data.selectedDate
    })
  }
})
