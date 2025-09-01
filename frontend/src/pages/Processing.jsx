import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { 
  FileText,
  Database,
  Zap,
  BarChart3,
  CheckCircle,
  AlertCircle,
  Clock,
  ArrowRight
} from 'lucide-react'

import { ProgressBar, LoadingSpinner, StatusBadge } from '../components/UI'
import { AutonomousAPI } from '../services/api'
import { useWorkflow } from '../hooks/useWorkflow'
import { useWebSocket } from '../hooks/useWebSocket'

export default function ProcessingPage() {
  const { workflowId } = useParams()
  const navigate = useNavigate()
  const { workflows, updateWorkflow } = useWorkflow()
  const [workflow, setWorkflow] = useState(null)
  const [loading, setLoading] = useState(true)

  // WebSocket connection for real-time updates
  const { isConnected, subscribeToWorkflow } = useWebSocket(
    `client_${workflowId}`,
    (message) => {
      if (message.type === 'autonomous_workflow_update' && message.workflow_id === workflowId) {
        console.log('Received workflow update:', message)
        const updatedWorkflow = {
          workflow_id: workflowId,
          status: message.status,
          progress: message.progress,
          current_stage: message.current_stage,
          message: message.message,
          updated_at: message.timestamp
        }
        setWorkflow(updatedWorkflow)
        updateWorkflow(updatedWorkflow)

        if (message.status === 'completed') {
          toast.success('Processing completed!')
          setTimeout(() => navigate(`/results/${workflowId}`), 2000)
        } else if (message.status === 'error') {
          toast.error('Processing failed: ' + message.message)
        }
      }
    }
  )

  useEffect(() => {
    if (workflowId) {
      loadWorkflowStatus()

      // Subscribe to WebSocket updates
      if (isConnected) {
        subscribeToWorkflow(workflowId)
      }
    }
  }, [workflowId, isConnected])

  const loadWorkflowStatus = async () => {
    try {
      const statusData = await AutonomousAPI.getWorkflowStatus(workflowId)
      setWorkflow(statusData)
      updateWorkflow(statusData)

      if (statusData.status === 'completed') {
        navigate(`/results/${workflowId}`)
      }
    } catch (error) {
      console.error('Failed to load workflow status:', error)
      toast.error('Failed to load workflow status')
    } finally {
      setLoading(false)
    }
  }

  const stages = [
    {
      key: 'translation',
      name: 'Translation',
      icon: FileText,
      description: 'AI agent processing Japanese document'
    },
    {
      key: 'extraction',
      name: 'Material Extraction with QA Classification',
      icon: Zap,
      description: 'AI agent extracting materials with QA classification (13 categories)'
    },
    {
      key: 'supplier_bom',
      name: 'Supplier BOM Processing',
      icon: Database,
      description: 'AI agent processing Excel/CSV data'
    },
    {
      key: 'comparison',
      name: 'Smart Comparison with QA Integration',
      icon: BarChart3,
      description: 'AI agent matching QA materials with supplier BOM using classification'
    }
  ]

  const getStageStatus = (stageKey) => {
    if (!workflow) return 'idle'

    const currentStageIndex = stages.findIndex(s => s.key === workflow.current_stage)
    const stageIndex = stages.findIndex(s => s.key === stageKey)

    if (workflow.status === 'error') return 'error'
    if (workflow.status === 'completed') return 'completed'
    if (stageIndex < currentStageIndex) return 'completed'
    if (stageIndex === currentStageIndex) return 'processing'
    return 'idle'
  }

  if (loading && !workflow) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-gray-600">Loading workflow...</span>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Processing Workflow</h1>
          <p className="text-gray-600">
            Workflow ID: <span className="font-mono text-sm">{workflowId}</span> • With QA Classification
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
            isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`} />
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
          {workflow && <StatusBadge status={workflow.status} />}
        </div>
      </div>

      {/* Overall Progress */}
      {workflow && (
        <motion.div
          className="card p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Overall Progress</h2>
            <span className="text-sm text-gray-600">{Math.round(workflow.progress || 0)}%</span>
          </div>
          <ProgressBar progress={workflow.progress || 0} showText={false} />
          {workflow.message && (
            <p className="text-sm text-gray-600 mt-2">{workflow.message}</p>
          )}
        </motion.div>
      )}

      {/* Autonomous Agents Pipeline */}
      <motion.div
        className="card p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Autonomous Agents Pipeline with QA Classification</h2>

        <div className="space-y-6">
          {stages.map((stage, index) => {
            const status = getStageStatus(stage.key)
            const Icon = stage.icon

            return (
              <motion.div
                key={stage.key}
                className="flex items-center space-x-4 p-4 rounded-lg border border-gray-200 bg-gray-50"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                {/* Stage Icon & Status */}
                <div className="flex-shrink-0">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                    status === 'completed' ? 'bg-green-100' :
                    status === 'processing' ? 'bg-blue-100' :
                    status === 'error' ? 'bg-red-100' : 'bg-gray-200'
                  }`}>
                    <Icon className={`w-6 h-6 ${
                      status === 'completed' ? 'text-green-600' :
                      status === 'processing' ? 'text-blue-600' :
                      status === 'error' ? 'text-red-600' : 'text-gray-500'
                    }`} />
                  </div>
                </div>

                {/* Stage Info */}
                <div className="flex-grow">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium text-gray-900">{stage.name}</h3>
                    <div className="flex items-center space-x-2">
                      {status === 'processing' && (
                        <Clock className="w-4 h-4 text-blue-500 animate-spin" />
                      )}
                      {status === 'completed' && (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      )}
                      {status === 'error' && (
                        <AlertCircle className="w-4 h-4 text-red-500" />
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{stage.description}</p>
                </div>

                {/* Connection Arrow */}
                {index < stages.length - 1 && (
                  <div className="flex-shrink-0">
                    <ArrowRight className="w-4 h-4 text-gray-400" />
                  </div>
                )}
              </motion.div>
            )
          })}
        </div>
      </motion.div>
    </div>
  )
}