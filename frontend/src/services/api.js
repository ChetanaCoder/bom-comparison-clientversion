import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('API Response Error:', error.response || error.message)
    return Promise.reject(error)
  }
)

export class AutonomousAPI {
  // Health check
  static async healthCheck() {
    const response = await api.get('/health')
    return response.data
  }

  // Upload documents for autonomous processing
  static async uploadDocuments(qaDocument, supplierBom) {
    const formData = new FormData()
    formData.append('qa_document', qaDocument)
    formData.append('supplier_bom', supplierBom)

    const response = await api.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  // Get workflow status
  static async getWorkflowStatus(workflowId) {
    const response = await api.get(`/api/status/${workflowId}`)
    return response.data
  }

  // Get intermediate results from autonomous agents
  static async getIntermediateResults(workflowId, stage = null) {
    const url = stage 
      ? `/api/intermediate/${workflowId}?stage=${stage}`
      : `/api/intermediate/${workflowId}`
    const response = await api.get(url)
    return response.data
  }

  // Get final results with QA classification
  static async getResults(workflowId) {
    const response = await api.get(`/api/results/${workflowId}`)
    return response.data
  }

  // List all workflows
  static async listWorkflows() {
    const response = await api.get('/api/workflows')
    return response.data
  }

  // Get autonomous agent statistics
  static async getAgentStats() {
    const response = await api.get('/api/agent_stats')
    return response.data
  }
}

export default api