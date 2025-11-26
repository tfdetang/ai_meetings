import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 360000, // 6 minutes (360 seconds)
})

// Add request interceptor for logging
client.interceptors.request.use(
  (config) => {
    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, config.data)
    return config
  },
  (error) => {
    console.error('[API Request Error]', error)
    return Promise.reject(error)
  }
)

// Add response interceptor for logging
client.interceptors.response.use(
  (response) => {
    console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data)
    return response
  },
  (error) => {
    console.error('[API Response Error]', error.config?.url, error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// Agents API
export const agentsAPI = {
  list: () => client.get('/agents'),
  get: (id) => client.get(`/agents/${id}`),
  create: (data) => client.post('/agents', data),
  update: (id, data) => client.put(`/agents/${id}`, data),
  delete: (id) => client.delete(`/agents/${id}`),
  test: (id) => client.post(`/agents/${id}/test`),
}

// Templates API
export const templatesAPI = {
  list: () => client.get('/templates'),
}

// Meetings API
export const meetingsAPI = {
  list: () => client.get('/meetings'),
  get: (id) => client.get(`/meetings/${id}`),
  create: (data) => client.post('/meetings', data),
  delete: (id) => client.delete(`/meetings/${id}`),
  start: (id) => client.post(`/meetings/${id}/start`),
  pause: (id) => client.post(`/meetings/${id}/pause`),
  end: (id) => client.post(`/meetings/${id}/end`),
  sendMessage: (id, message) => client.post(`/meetings/${id}/messages`, { message }),
  requestAgent: (id, agentId) => client.post(`/meetings/${id}/request/${agentId}`),
  exportMarkdown: (id) => client.get(`/meetings/${id}/export/markdown`),
  exportJson: (id) => client.get(`/meetings/${id}/export/json`),
}

export default client
