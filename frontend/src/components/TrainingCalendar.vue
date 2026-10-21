<template>
  <div class="calendar-container">
    <!-- 日历头部 -->
    <div class="calendar-header">
      <el-button @click="prevMonth" :icon="ArrowLeft" circle size="small" />
      <div class="current-month">{{ currentYear }}年{{ currentMonth }}月</div>
      <el-button @click="nextMonth" :icon="ArrowRight" circle size="small" />
    </div>

    <!-- 星期标题 -->
    <div class="weekdays">
      <div v-for="day in weekdays" :key="day" class="weekday">{{ day }}</div>
    </div>

    <!-- 日历网格 -->
    <div class="calendar-grid">
      <div
        v-for="(day, index) in calendarDays"
        :key="index"
        :class="['calendar-day', {
          'other-month': !day.currentMonth,
          'today': day.isToday,
          'records-1': day.recordCount === 1,
          'records-2': day.recordCount === 2,
          'records-3': day.recordCount === 3,
          'records-many': day.recordCount > 3,
          'selected': day.date === selectedDate
        }]"
        @click="selectDate(day)"
      >
        <div class="day-number">{{ day.day }}</div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <el-icon class="is-loading" :size="30"><Loading /></el-icon>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, ArrowRight, Loading } from '@element-plus/icons-vue'
import { videoApi } from '../utils/api'
import { ElMessage } from 'element-plus'

const router = useRouter()

// 当前年月
const currentDate = new Date()
const currentYear = ref(currentDate.getFullYear())
const currentMonth = ref(currentDate.getMonth() + 1)

// 每日记录数
const dailyRecordCount = ref({})

// 加载状态
const loading = ref(false)

// 星期标题
const weekdays = ['日', '一', '二', '三', '四', '五', '六']

// 计算日历天数
const calendarDays = computed(() => {
  const days = []
  const year = currentYear.value
  const month = currentMonth.value

  // 获取当月第一天是星期几
  const firstDay = new Date(year, month - 1, 1).getDay()
  
  // 获取当月天数
  const daysInMonth = new Date(year, month, 0).getDate()
  
  // 获取上月天数
  const daysInPrevMonth = new Date(year, month - 1, 0).getDate()

  // 添加上月的日期
  for (let i = firstDay - 1; i >= 0; i--) {
    const day = daysInPrevMonth - i
    days.push({
      day,
      date: formatDate(year, month - 1, day),
      currentMonth: false,
      recordCount: 0,
      isToday: false
    })
  }

  // 添加当月的日期
  const today = new Date()
  for (let i = 1; i <= daysInMonth; i++) {
    const isToday = year === today.getFullYear() && 
                    month === today.getMonth() + 1 && 
                    i === today.getDate()
    days.push({
      day: i,
      date: formatDate(year, month, i),
      currentMonth: true,
      recordCount: dailyRecordCount.value[i] || 0,
      isToday
    })
  }

  // 添加下月的日期（补齐 6 行）
  const remainingDays = 42 - days.length
  for (let i = 1; i <= remainingDays; i++) {
    days.push({
      day: i,
      date: formatDate(year, month + 1, i),
      currentMonth: false,
      recordCount: 0,
      isToday: false
    })
  }

  return days
})

// 格式化日期
const formatDate = (year, month, day) => {
  // 处理月份溢出
  if (month > 12) {
    year++
    month = 1
  } else if (month < 1) {
    year--
    month = 12
  }
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

// 上个月
const prevMonth = () => {
  if (currentMonth.value === 1) {
    currentYear.value--
    currentMonth.value = 12
  } else {
    currentMonth.value--
  }
}

// 下个月
const nextMonth = () => {
  if (currentMonth.value === 12) {
    currentYear.value++
    currentMonth.value = 1
  } else {
    currentMonth.value++
  }
}

// 选择日期 - 跳转到新页面
const selectDate = (day) => {
  if (!day.currentMonth) return
  
  // 跳转到日期记录页面
  router.push(`/daily-records/${day.date}`)
}

// 加载每日记录数
const loadDailyRecordCount = async () => {
  loading.value = true
  try {
    const response = await videoApi.getDailyRecordCount(currentYear.value, currentMonth.value)
    if (response.data.code === '200') {
      dailyRecordCount.value = response.data.data || {}
    }
  } catch (error) {
    console.error('加载每日记录数失败:', error)
    ElMessage.error('加载日历数据失败')
  } finally {
    loading.value = false
  }
}

// 监听月份变化
watch([currentYear, currentMonth], () => {
  loadDailyRecordCount()
})

// 初始化
onMounted(() => {
  loadDailyRecordCount()
})
</script>

<style scoped>
.calendar-container {
  background: white;
  border-radius: 8px;
  padding: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  position: relative;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.current-month {
  font-size: 14px;
  font-weight: bold;
  color: #000;
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-bottom: 4px;
}

.weekday {
  text-align: center;
  font-size: 11px;
  color: #000;
  padding: 2px 0;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.calendar-day {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  background: #f5f5f5;
}

.calendar-day:hover {
  background: #ebebeb;
}

.calendar-day.other-month {
  opacity: 0.25;
  cursor: default;
  background: transparent;
}

.calendar-day.today {
  background: #e6f7ff;
  border: 1.5px solid #1890ff;
}

.calendar-day.records-1 {
  background: #dff5d7;
}

.calendar-day.records-2 {
  background: #a3d98e;
}

.calendar-day.records-3 {
  background: #66bb6a;
  color: #fff;
}

.calendar-day.records-many {
  background: #2e7d32;
  color: #fff;
}

.calendar-day.selected {
  background: #667eea;
  color: white;
}

.day-number {
  font-size: 13px;
  font-weight: 600;
  line-height: 1;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  z-index: 10;
}

@media screen and (max-width: 768px) {
  .calendar-container {
    padding: 4px;
  }

  .current-month {
    font-size: 12px;
  }

  .day-number {
    font-size: 10px;
  }
}
</style>
