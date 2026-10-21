<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { auth } from './utils/auth'

onMounted(() => {
  // 初始化 token
  auth.initToken()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: #f5f7fa;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 移动端优化 */
@media screen and (max-width: 768px) {
  html {
    font-size: 14px;
  }
}
</style>
