<template>
  <div id="app">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>📈 量化交易平台</h1>
          <div class="header-info">
            <el-tag :type="marketStatus === 'open' ? 'success' : 'info'">
              {{ marketStatus === 'open' ? '市场开放' : '市场关闭' }}
            </el-tag>
          </div>
        </div>
      </el-header>
      
      <el-main>
        <el-row :gutter="20">
          <!-- 左侧：账户信息和交易历史 -->
          <el-col :span="8">
            <Dashboard />
          </el-col>
          
          <!-- 右侧：策略面板 -->
          <el-col :span="16">
            <StrategyPanel />
          </el-col>
        </el-row>

        <!-- K 线图 -->
        <el-row style="margin-top: 20px;">
          <el-col :span="24">
            <CandlestickChart />
          </el-col>
        </el-row>
        
        <!-- 底部：交易历史 -->
        <el-row style="margin-top: 20px;">
          <el-col :span="24">
            <TradeHistory />
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Dashboard from './components/Dashboard.vue'
import StrategyPanel from './components/StrategyPanel.vue'
import TradeHistory from './components/TradeHistory.vue'
import CandlestickChart from './components/CandlestickChart.vue'

const marketStatus = ref('open')

onMounted(() => {
  // 模拟市场状态
  const hour = new Date().getHours()
  marketStatus.value = (hour >= 9 && hour < 15) ? 'open' : 'closed'
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.el-header {
  background-color: #409EFF;
  color: white;
  padding: 0 20px;
  display: flex;
  align-items: center;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-content h1 {
  font-size: 24px;
  font-weight: 600;
}

.header-info {
  display: flex;
  gap: 10px;
  align-items: center;
}

.el-main {
  padding: 20px;
}

.el-card {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 20px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409EFF;
  margin: 10px 0;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}

.positive {
  color: #67C23A !important;
}

.negative {
  color: #F56C6C !important;
}
</style>
