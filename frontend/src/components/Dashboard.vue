<template>
  <el-card class="dashboard-card">
    <template #header>
      <div class="card-header">
        <span>💰 账户信息</span>
        <el-button size="small" @click="refreshAccount">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </template>
    
    <div class="stats-grid">
      <div class="stat-item">
        <div class="stat-label">总资产</div>
        <div class="stat-value">¥{{ formatNumber(account.total_capital) }}</div>
      </div>
      
      <div class="stat-item">
        <div class="stat-label">可用资金</div>
        <div class="stat-value">¥{{ formatNumber(account.available_capital) }}</div>
      </div>
      
      <div class="stat-item">
        <div class="stat-label">冻结资金</div>
        <div class="stat-value">¥{{ formatNumber(account.frozen_capital) }}</div>
      </div>
      
      <div class="stat-item">
        <div class="stat-label">总盈亏</div>
        <div :class="['stat-value', account.total_pnl >= 0 ? 'positive' : 'negative']">
          {{ account.total_pnl >= 0 ? '+' : '' }}¥{{ formatNumber(account.total_pnl) }}
        </div>
      </div>
      
      <div class="stat-item">
        <div class="stat-label">收益率</div>
        <div :class="['stat-value', account.pnl_rate >= 0 ? 'positive' : 'negative']">
          {{ account.pnl_rate >= 0 ? '+' : '' }}{{ account.pnl_rate.toFixed(2) }}%
        </div>
      </div>
    </div>
    
    <el-divider />
    
    <div class="positions-section">
      <h3>📊 持仓明细</h3>
      <el-table :data="account.positions" style="width: 100%" size="small">
        <el-table-column prop="symbol" label="标的" width="100" />
        <el-table-column prop="quantity" label="数量" width="80" />
        <el-table-column prop="average_price" label="成本价" width="90">
          <template #default="scope">
            ¥{{ scope.row.average_price.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="current_price" label="现价" width="90">
          <template #default="scope">
            ¥{{ scope.row.current_price.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column label="盈亏">
          <template #default="scope">
            <span :class="scope.row.unrealized_pnl >= 0 ? 'positive' : 'negative'">
              {{ scope.row.unrealized_pnl >= 0 ? '+' : '' }}¥{{ scope.row.unrealized_pnl.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="account.positions.length === 0" class="empty-tip">
        暂无持仓
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { tradingAPI } from '../api'

const account = ref({
  total_capital: 100000,
  available_capital: 100000,
  frozen_capital: 0,
  total_pnl: 0,
  pnl_rate: 0,
  positions: []
})

const formatNumber = (num) => {
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const refreshAccount = async () => {
  try {
    const data = await tradingAPI.getAccount()
    account.value = data
  } catch (error) {
    console.error('获取账户信息失败:', error)
  }
}

onMounted(() => {
  refreshAccount()
  // 每 30 秒刷新一次
  setInterval(refreshAccount, 30000)
})
</script>

<style scoped>
.dashboard-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-label {
  color: #909399;
  font-size: 13px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #409EFF;
}

.positive {
  color: #67C23A !important;
}

.negative {
  color: #F56C6C !important;
}

.positions-section h3 {
  margin-bottom: 15px;
  font-size: 16px;
  color: #303133;
}

.empty-tip {
  text-align: center;
  color: #909399;
  padding: 30px;
}
</style>
