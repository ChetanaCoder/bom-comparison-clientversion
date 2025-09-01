import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { 
  Upload,
  FileText,
  Database,
  Zap,
  BarChart3,
  Activity,
  TrendingUp,
  Clock
} from 'lucide-react'

import { StatCard, LoadingSpinner, EmptyState, AgentStatusIcon, StatusBadge } from '../components/UI'
import { AutonomousAPI } from '../services/api'
import { useWorkflow } from '../hooks/useWorkflow'

export default function Dashboard() {
  const { workflows, agentStats, setWorkflows, setAgentStats, loading, setLoading, setError } = useWorkflow()
  const [recentWorkflows, setRecentWorkflows] = useState([])

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setLoading(true)
    try {
      // Load workflows and agent stats in parallel
      const [workflowsData, agentStatsData] = await Promise.all([
        AutonomousAPI.listWorkflows(),
        AutonomousAPI.getAgentStats()
      ])

      setWorkflows(workflowsData.workflows || [])
      setAgentStats(agentStatsData)

      // Set recent workflows (last 5)
      const recent = (workflowsData.workflows || [])
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, 5)
      setRecentWorkflows(recent)

    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      setError(error.message)
      toast.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const workflowsArray = Object.values(workflows)
  const completedWorkflows = workflowsArray.filter(w => w.status === 'completed').length
  const processingWorkflows = workflowsArray.filter(w => w.status === 'processing').length
  const totalWorkflows = workflowsArray.length

  const averageProgress = workflowsArray.length > 0 
    ? workflowsArray.reduce((sum, w) => sum + (w.progress || 0), 0) / workflowsArray.length
    : 0

  if (loading && workflowsArray.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-gray-600">Loading dashboard...</span>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Monitor your autonomous BOM processing workflows with QA classification</p>
        </div>
        <Link
          to="/upload"
          className="btn btn-primary h-10 px-4 py-2"
        >
          <Upload className="w-4 h-4 mr-2" />
          New Processing
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Workflows"
          value={totalWorkflows}
          icon={FileText}
          trend={`${processingWorkflows} active`}
        />
        <StatCard
          title="Completed"
          value={completedWorkflows}
          icon={BarChart3}
          trend={totalWorkflows > 0 ? `${Math.round((completedWorkflows / totalWorkflows) * 100)}% success rate` : ''}
        />
        <StatCard
          title="Average Progress"
          value={`${Math.round(averageProgress)}%`}
          icon={TrendingUp}
          trend="Across all workflows"
        />
        <StatCard
          title="QA Classification"
          value={agentStats?.autonomous_agents?.qa_classification_enabled ? "Enabled" : "Demo Mode"}
          icon={Activity}
          trend={agentStats?.platform_info?.gemini_configured ? "LLM Connected" : "Demo Mode"}
        />
      </div>

      {/* Agent Status */}
      {agentStats && (
        <motion.div
          className="card p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Autonomous Agents with QA Classification</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <AgentStatusIcon agent="translation" status="idle" />
              <span className="text-sm text-gray-600">
                {agentStats.autonomous_agents?.translation_agent?.documents_processed || 0} docs
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <AgentStatusIcon agent="extraction" status="idle" />
              <span className="text-sm text-gray-600">
                {agentStats.autonomous_agents?.extraction_agent?.materials_extracted || 0} materials
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <AgentStatusIcon agent="supplier_bom" status="idle" />
              <span className="text-sm text-gray-600">
                {agentStats.autonomous_agents?.supplier_bom_agent?.items_extracted || 0} items
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <AgentStatusIcon agent="comparison" status="idle" />
              <span className="text-sm text-gray-600">
                {agentStats.autonomous_agents?.comparison_agent?.matches_found || 0} matches
              </span>
            </div>
          </div>
        </motion.div>
      )}

      {/* Recent Workflows */}
      <motion.div
        className="card p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Recent Workflows</h2>
          {totalWorkflows > 5 && (
            <span className="text-sm text-gray-500">
              Showing {Math.min(5, totalWorkflows)} of {totalWorkflows}
            </span>
          )}
        </div>

        {recentWorkflows.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No workflows yet"
            description="Start by uploading your first WI/QC document and Item Master for autonomous processing with Item classification."
            action={
              <Link to="/upload" className="btn btn-primary">
                <Upload className="w-4 h-4 mr-2" />
                Start Processing
              </Link>
            }
          />
        ) : (
          <div className="space-y-3">
            {recentWorkflows.map((workflow) => (
              <Link
                key={workflow.workflow_id}
                to={workflow.status === 'completed' 
                  ? `/results/${workflow.workflow_id}` 
                  : `/processing/${workflow.workflow_id}`
                }
                className="block p-4 hover:bg-gray-50 rounded-lg border border-gray-100 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                      <FileText className="w-5 h-5 text-primary-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 truncate max-w-xs">
                        {workflow.workflow_id}
                      </p>
                      <p className="text-sm text-gray-500">
                        {workflow.current_stage} • {new Date(workflow.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="text-right">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${workflow.progress || 0}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 mt-1">
                        {Math.round(workflow.progress || 0)}%
                      </span>
                    </div>
                    <StatusBadge status={workflow.status} />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  )
}
