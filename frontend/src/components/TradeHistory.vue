<template>
  <el-card class="trade-history-card">
    <template #header>
      <div class="card-header">
        <span>📜 交易历史</span>
        <el-button size="small" @click="refreshHistory">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </template>
    
    <el-tabs v-model="activeTab">
      <el-tab-pane label="订单记录" name="orders">
        <el-table :data="orders" style="width: 100%" size="small" stripe>
          <el-table-column prop="id" label="订单 ID" width="100" />
          <el-table-column prop="symbol" label="标的" width="100" />
          <el-table-column prop="side" label="方向" width="70">
            <template #default="scope">
              <el-tag :type="scope.row.side === 'buy' ? 'success' : 'danger'">
                {{ scope.row.side === 'buy' ? '买入' : '卖出' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="price" label="价格" width="90">
            <template #default="scope">
              ¥{{ scope.row.price.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="scope">
              <el-tag :type="getStatusType(scope.row.status)">
                {{ getStatusText(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="strategy" label="策略" />
          <el-table-column label="时间">
            <template #default="scope">
              {{ formatTime(scope.row.executed_at || scope.row.created_at) }}
            </template>
          </el-table-column>
        </el-table>
        
        <div v-if="orders.length === 0" class="empty-tip">
          暂无订单记录
        </div>
      </el-tab-pane>
      
      <el-tab-pane label="成交记录" name="history">
        <el-table :data="history" style="width: 100%" size="small" stripe>
          <el-table-column prop="id" label="成交 ID" width="100" />
          <el-table-column prop="symbol" label="标的" width="100" />
          <el-table-column prop="side" label="方向" width="70">
            <template #default="scope">
              <el-tag :type="scope.row.side === 'buy' ? 'success' : 'danger'">
                {{ scope.row.side === 'buy' ? '买入' : '卖出' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="price" label="成交价" width="90">
            <template #default="scope">
              ¥{{ scope.row.price.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column label="成交金额" width="120">
            <template #default="scope">
              ¥{{ (scope.row.price * scope.row.quantity).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="strategy" label="策略" />
          <el-table-column label="成交时间">
            <template #default="scope">
              {{ formatTime(scope.row.executed_at) }}
            </template>
          </el-table-column>
        </el-table>
        
        <div v-if="history.length === 0" class="empty-tip">
          暂无成交记录
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { tradingAPI } from '../api'

const activeTab = ref('orders')
const orders = ref([])
const history = ref([])

const getStatusType = (status) => {
  const map = {
    'pending': 'warning',
    'executed': 'success',
    'cancelled': 'info'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    'pending': '待成交',
    'executed': '已成交',
    'cancelled': '已取消'
  }
  return map[status] || status
}

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const refreshHistory = async () => {
  try {
    const [ordersData, historyData] = await Promise.all([
      tradingAPI.getOrders(50),
      tradingAPI.getHistory(50)
    ])
    
    orders.value = ordersData || []
    history.value = historyData || []
  } catch (error) {
    console.error('获取交易历史失败:', error)
  }
}

onMounted(() => {
  refreshHistory()
  // 每 30 秒刷新一次
  setInterval(refreshHistory, 30000)
})
</script>

<style scoped>
.trade-history-card {
  min-height: 400px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-tip {
  text-align: center;
  color: #909399;
  padding: 30px;
}

:deep(.el-table) {
  font-size: 13px;
}

:deep(.el-table th) {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: 600;
}
</style>
