import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('响应错误:', error)
    return Promise.reject(error)
  }
)

// 交易相关 API
export const tradingAPI = {
  // 获取账户信息
  getAccount() {
    return api.get('/trading/account')
  },
  
  // 下单
  placeOrder(order) {
    return api.post('/trading/order', order)
  },
  
  // 获取订单列表
  getOrders(limit = 50) {
    return api.get('/trading/orders', { params: { limit } })
  },
  
  // 获取交易历史
  getHistory(limit = 50) {
    return api.get('/trading/history', { params: { limit } })
  },
  
  // 更新持仓价格
  updatePositions(prices) {
    return api.post('/trading/positions/update', prices)
  }
}

// 策略相关 API
export const strategiesAPI = {
  // 获取策略列表
  listStrategies() {
    return api.get('/strategies/list')
  },
  
  // 分析市场
  analyzeMarket(config) {
    return api.post('/strategies/analyze', config)
  },
  
  // 获取策略状态
  getStrategyStatus(strategyType, symbol, params = {}) {
    return api.get(`/strategies/status/${strategyType}/${symbol}`, { params })
  },
  
  // 运行回测
  runBacktest(config, days = 60) {
    return api.post('/strategies/backtest', config, { params: { days } })
  },
  
  // 获取 K 线数据
  getKlineData(symbol, days = 60, interval = '1d') {
    return api.get(`/strategies/kline/${encodeURIComponent(symbol)}`, {
      params: { days, interval },
    })
  },

  // 获取支持的标的
  getSupportedSymbols() {
    return api.get('/strategies/symbols')
  }
}

export default api
