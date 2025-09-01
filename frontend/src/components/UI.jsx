import React from 'react'
import { motion } from 'framer-motion'
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertCircle,
  Loader2,
  FileText,
  Database,
  Zap,
  BarChart3
} from 'lucide-react'

// Loading Spinner
export function LoadingSpinner({ size = 'md', className = '' }) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12'
  }

  return (
    <Loader2 className={`animate-spin ${sizeClasses[size]} ${className}`} />
  )
}

// Progress Bar
export function ProgressBar({ progress, showText = true, className = '' }) {
  return (
    <div className={`w-full ${className}`}>
      <div className="flex justify-between items-center mb-2">
        {showText && (
          <span className="text-sm font-medium text-gray-700">
            {Math.round(progress)}%
          </span>
        )}
      </div>
      <div className="progress-bar">
        <motion.div
          className="progress-fill"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>
    </div>
  )
}

// Status Badge
export function StatusBadge({ status, className = '' }) {
  const statusConfig = {
    processing: {
      icon: Clock,
      className: 'status-processing',
      label: 'Processing'
    },
    completed: {
      icon: CheckCircle,
      className: 'status-completed',
      label: 'Completed'
    },
    error: {
      icon: XCircle,
      className: 'status-error',
      label: 'Error'
    },
    initialized: {
      icon: AlertCircle,
      className: 'bg-gray-100 text-gray-800',
      label: 'Initialized'
    }
  }

  const config = statusConfig[status] || statusConfig.initialized
  const Icon = config.icon

  return (
    <span className={`status-indicator ${config.className} ${className}`}>
      <Icon className="w-3 h-3 mr-1" />
      {config.label}
    </span>
  )
}

// Stat Card
export function StatCard({ title, value, icon: Icon, trend, className = '' }) {
  return (
    <motion.div
      className={`card p-6 ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
          {trend && (
            <p className="text-xs text-gray-500 mt-1">{trend}</p>
          )}
        </div>
        {Icon && (
          <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
            <Icon className="w-6 h-6 text-primary-600" />
          </div>
        )}
      </div>
    </motion.div>
  )
}

// File Upload Zone
export function FileUploadZone({ onFileSelect, accept, children, className = '' }) {
  const [isDragOver, setIsDragOver] = React.useState(false)

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragOver(false)
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      onFileSelect(files[0])
    }
  }

  const handleFileInput = (e) => {
    const files = Array.from(e.target.files)
    if (files.length > 0) {
      onFileSelect(files[0])
    }
  }

  return (
    <div
      className={`upload-zone ${isDragOver ? 'dragover' : ''} ${className}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => document.getElementById('file-input').click()}
    >
      {children}
      <input
        id="file-input"
        type="file"
        accept={accept}
        onChange={handleFileInput}
        className="hidden"
      />
    </div>
  )
}

// Agent Status Icon
export function AgentStatusIcon({ agent, status = 'idle' }) {
  const agentIcons = {
    translation: FileText,
    extraction: Zap,
    supplier_bom: Database,
    comparison: BarChart3
  }

  const statusColors = {
    idle: 'text-gray-400',
    processing: 'text-yellow-500 animate-pulse',
    completed: 'text-green-500',
    error: 'text-red-500'
  }

  const Icon = agentIcons[agent] || AlertCircle

  return (
    <div className="flex items-center space-x-2">
      <Icon className={`w-5 h-5 ${statusColors[status]}`} />
      <span className="text-sm capitalize">{agent.replace('_', ' ')}</span>
    </div>
  )
}

// Empty State
export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="text-center py-12">
      {Icon && (
        <div className="w-16 h-16 mx-auto bg-gray-100 rounded-lg flex items-center justify-center mb-4">
          <Icon className="w-8 h-8 text-gray-400" />
        </div>
      )}
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-500 mb-6 max-w-md mx-auto">{description}</p>
      {action}
    </div>
  )
}