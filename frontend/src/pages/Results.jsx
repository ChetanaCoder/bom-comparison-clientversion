import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { 
  CheckCircle,
  AlertCircle,
  FileText,
  Database,
  Download,
  BarChart3,
  Target,
  Percent,
  ChevronDown,
  ChevronRight,
  Filter,
  Eye,
  PieChart as PieChartIcon
} from 'lucide-react'
import { LoadingSpinner, StatusBadge, StatCard } from '../components/UI'
import { AutonomousAPI } from '../services/api'

export default function ResultsPage() {
  const { workflowId } = useParams()
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(true)
  const [expandedSections, setExpandedSections] = useState({
    qaClassification: true,
    matches: false,
    summary: false,
    reasonChart: false // New section for pie chart
  })
  const [filterRAG, setFilterRAG] = useState('all') // all, green, amber, red

  useEffect(() => {
    if (workflowId) {
      loadResults()
    }
  }, [workflowId])

  const loadResults = async () => {
    try {
      const data = await AutonomousAPI.getResults(workflowId)
      setResults(data)
    } catch (error) {
      console.error('Failed to load results:', error)
      toast.error('Failed to load results')
    } finally {
      setLoading(false)
    }
  }

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  const exportResults = () => {
    if (!results) return
    const dataStr = JSON.stringify(results, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
    const exportFileDefaultName = `bom-comparison-${workflowId}.json`
    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
    toast.success('Results exported!')
  }

  const exportQAClassificationCSV = () => {
    if (!results || !results.matches) return
    // Create CSV header - MODIFIED to include Reason column
    const csvHeaders = [
      'S. No.',
      'Material Name',
      'QC Process / WI Step',
      'Consumable/Jigs/Tools',
      'Name Mismatch',
      'PN (Part Name)',
      'PN Mismatch',
      'Qty',
      'UoM',
      'Obsolete PN',
      'Vendor Name',
      'Kit Available',
      'AI Engine Processing',
      'Confidence Level',
      'Action Path (RAG)',
      'Classification Label',
      'Supplier Match',
      'Match Confidence',
      'Reason' // NEW COLUMN
    ]
    // Create CSV rows - MODIFIED to include reason data
    const csvRows = results.matches.map((match, index) => {
      return [
        index + 1,
        match.qa_material_name || '',
        match.qc_process_step || '',
        match.consumable_jigs_tools ? 'Yes' : 'No',
        match.name_mismatch ? 'Yes' : 'No',
        match.part_number || '',
        match.pn_mismatch ? 'Yes' : 'No',
        match.quantity || '',
        match.unit_of_measure || '',
        match.obsolete_pn ? 'Yes' : 'No',
        match.vendor_name || '',
        match.kit_available ? 'Yes' : 'No',
        'AI Processed',
        match.qa_confidence_level || 'Medium',
        match.qa_action_path || '🟠',
        `Label ${match.qa_classification_label || 5}`,
        match.confidence_score > 0 ? match.supplier_description : 'No Match',
        `${Math.round((match.confidence_score || 0) * 100)}%`,
        match.reasoning || 'No reason provided' // NEW DATA FIELD
      ]
    })
    // Combine header and rows
    const csvContent = [csvHeaders, ...csvRows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n')
    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `qa-classification-${workflowId}.csv`
    link.click()
    toast.success('WI/QC Item Classification exported to CSV!')
  }

  const getActionPathIcon = (actionPath) => {
    switch(actionPath) {
      case '🟢': return { icon: '🟢', text: 'Auto-Register', class: 'text-green-600' }
      case '🟠': return { icon: '🟠', text: 'Auto w/ Flag', class: 'text-yellow-600' }
      case '🔴': return { icon: '🔴', text: 'Human Intervention', class: 'text-red-600' }
      default: return { icon: '🟠', text: 'Auto w/ Flag', class: 'text-yellow-600' }
    }
  }

  const getClassificationDescription = (label) => {
    const descriptions = {
      1: 'Consumable/Jigs/Tools + PN + Qty',
      2: 'Consumable/Jigs/Tools + PN + Spec + Qty', 
      3: 'Consumable/Jigs/Tools (no qty)',
      4: 'Consumable/Jigs/Tools (no Part Number)',
      5: 'No Consumable/Jigs/Tools Mentioned',
      6: 'Consumable/Jigs/Tools + Part Number mismatch',
      7: 'Consumable/Jigs/Tools + Obsolete Part Number',
      8: 'Ambiguous Consumable/Jigs/Tools Name',
      9: 'Vendor Name Only',
      10: 'Multiple Consumable/Jigs/Tools, no mapping',
      11: 'Pre-assembled kit mentioned',
      12: 'Work Instruction mentions Consumable/Jigs/Tools only',
      13: 'Vendor + Kit Mentioned (no PN)'
    }
    return descriptions[label] || 'Unknown Classification'
  }

  // NEW FUNCTION: Prepare data for pie chart
  const prepareReasonChartData = (matches) => {
    const reasonCounts = {}
    matches.forEach(match => {
      const reason = match.reasoning || 'No reason provided'
      reasonCounts[reason] = (reasonCounts[reason] || 0) + 1
    })

    return Object.entries(reasonCounts).map(([reason, count]) => ({
      name: reason,
      value: count,
      percentage: ((count / matches.length) * 100).toFixed(1)
    }))
  }

  // NEW FUNCTION: Get color for pie chart segments
  const getReasonColor = (index) => {
    const colors = [
      '#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1',
      '#d084d0', '#ffb347', '#87ceeb', '#dda0dd', '#98fb98'
    ]
    return colors[index % colors.length]
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-gray-600">Loading results...</span>
      </div>
    )
  }

  if (!results) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Results Not Found</h3>
        <p className="text-gray-500">
          The results for this workflow could not be loaded.
        </p>
        <Link to="/" className="btn btn-primary mt-4">
          Back to Dashboard
        </Link>
      </div>
    )
  }

  const matches = results.matches || []
  const qaClassification = results.qa_classification_summary || {}

  // Count action paths from matches
  const greenCount = matches.filter(m => m.qa_action_path === '🟢').length
  const amberCount = matches.filter(m => m.qa_action_path === '🟠').length
  const redCount = matches.filter(m => m.qa_action_path === '🔴').length

  // Filter matches by RAG classification
  const filteredMatches = filterRAG === 'all' ? matches : 
    matches.filter(match => {
      if (filterRAG === 'green') return match.qa_action_path === '🟢'
      if (filterRAG === 'amber') return match.qa_action_path === '🟠'  
      if (filterRAG === 'red') return match.qa_action_path === '🔴'
      return true
    })

  // NEW: Prepare chart data
  const reasonChartData = prepareReasonChartData(filteredMatches)

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Item Processing Results</h1>
          <p className="text-gray-600">
            Workflow ID: <span className="font-mono text-sm">{workflowId}</span> • With Item Classification & Reasons
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <StatusBadge status="completed" />
          <button
            onClick={exportQAClassificationCSV}
            className="btn btn-primary"
          >
            <Download className="w-4 h-4 mr-2" />
            Export Item Classification
          </button>
          <button
            onClick={exportResults}
            className="btn btn-outline"
          >
            <Download className="w-4 h-4 mr-2" />
            Export JSON
          </button>
        </div>
      </div>

      {/* Item Classification Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Materials"
          value={matches.length}
          icon={FileText}
          trend="Extracted with Item classification"
        />
        <StatCard
          title="Auto-Register"
          value={greenCount}
          icon={CheckCircle}
          trend="🟢 High confidence"
          className="border-l-4 border-green-500"
        />
        <StatCard
          title="Auto w/ Flag"
          value={amberCount}
          icon={AlertCircle}
          trend="🟠 Medium confidence"
          className="border-l-4 border-yellow-500"
        />
        <StatCard
          title="Human Intervention"
          value={redCount}
          icon={Target}
          trend="🔴 Low confidence"
          className="border-l-4 border-red-500"
        />
      </div>


      {/* Item Classification Table - MODIFIED */}
      <motion.div
        className="card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div 
          className="p-6 border-b border-gray-200 cursor-pointer"
          onClick={() => toggleSection('qaClassification')}
        >
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              QA Material Classification ({matches.length})
            </h2>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Filter className="w-4 h-4 text-gray-400" />
                <select 
                  value={filterRAG} 
                  onChange={(e) => setFilterRAG(e.target.value)}
                  className="text-sm border rounded px-2 py-1"
                  onClick={(e) => e.stopPropagation()}
                >
                  <option value="all">All ({matches.length})</option>
                  <option value="green">🟢 Auto-Register ({greenCount})</option>
                  <option value="amber">🟠 Auto w/ Flag ({amberCount})</option>
                  <option value="red">🔴 Human Intervention ({redCount})</option>
                </select>
              </div>
              {expandedSections.qaClassification ? (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronRight className="w-5 h-5 text-gray-400" />
              )}
            </div>
          </div>
        </div>
        {expandedSections.qaClassification && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">S.No.</th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Material Name</th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">QC Process/WI Step</th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Consumable/Jigs/Tools</th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Part Number</th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Qty</th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">UoM</th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vendor</th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Classification</th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Confidence</th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action Path</th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Supplier Match</th>
                  {/* NEW COLUMN HEADER */}
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reason</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredMatches.map((match, index) => {
                  const actionPath = getActionPathIcon(match.qa_action_path)
                  return (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-900">{index + 1}</td>
                      <td className="px-3 py-4 text-sm">
                        <div className="font-medium text-gray-900 max-w-xs">
                          <div className="truncate" title={match.qa_material_name}>
                            {match.qa_material_name}
                          </div>
                        </div>
                        {match.qa_excerpt && (
                          <div className="text-xs text-gray-500 italic max-w-xs mt-1">
                            <div className="truncate" title={match.qa_excerpt}>
                              "{match.qa_excerpt}"
                            </div>
                          </div>
                        )}
                      </td>
                      <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="max-w-xs truncate" title={match.qc_process_step || '-'}>
                          {match.qc_process_step || '-'}
                        </div>
                      </td>
                      <td className="px-3 py-4 whitespace-nowrap text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs ${match.consumable_jigs_tools ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                          {match.consumable_jigs_tools ? 'Yes' : 'No'}
                        </span>
                      </td>
                      <td className="px-3 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                        <div className="max-w-xs truncate" title={match.part_number || '-'}>
                          {match.part_number || '-'}
                        </div>
                      </td>
                      <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-900">
                        {match.quantity || '-'}
                      </td>
                      <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-500">
                        {match.unit_of_measure || '-'}
                      </td>
                      <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="max-w-xs truncate" title={match.vendor_name || '-'}>
                          {match.vendor_name || '-'}
                        </div>
                      </td>
                      <td className="px-3 py-4 text-sm">
                        <div className="font-medium">Label {match.qa_classification_label || 5}</div>
                        <div className="text-xs text-gray-500 max-w-xs" title={getClassificationDescription(match.qa_classification_label || 5)}>
                          <div className="truncate">
                            {getClassificationDescription(match.qa_classification_label || 5)}
                          </div>
                        </div>
                      </td>
                      <td className="px-3 py-4 whitespace-nowrap text-sm">
                        <span className={`font-semibold ${
                          match.qa_confidence_level === 'High' ? 'text-green-600' :
                          match.qa_confidence_level === 'Medium' ? 'text-yellow-600' : 'text-red-600'
                        }`}>
                          {match.qa_confidence_level || 'Medium'}
                        </span>
                      </td>
                      <td className="px-3 py-4 whitespace-nowrap text-sm">
                        <div className={`flex items-center space-x-1 ${actionPath.class}`}>
                          <span>{actionPath.icon}</span>
                          <span className="text-xs truncate max-w-20" title={actionPath.text}>
                            {actionPath.text}
                          </span>
                        </div>
                      </td>
                      <td className="px-3 py-4 text-sm">
                        {match.confidence_score > 0 ? (
                          <div>
                            <div className="font-medium text-gray-900 max-w-xs">
                              <div className="truncate" title={match.supplier_description}>
                                {match.supplier_description}
                              </div>
                            </div>
                            <div className="text-xs text-gray-500">
                              <div className="truncate">
                                {match.supplier_part_number} • {Math.round(match.confidence_score * 100)}%
                              </div>
                            </div>
                          </div>
                        ) : (
                          <span className="text-gray-500 italic">No match found</span>
                        )}
                      </td>
                      {/* NEW REASON COLUMN */}
                      <td className="px-3 py-4 text-sm">
                        <div className="max-w-xs">
                          <div className="truncate text-gray-900" title={match.reasoning || 'No reason provided'}>
                            {match.reasoning || 'No reason provided'}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            {filteredMatches.length === 0 && (
              <div className="text-center py-8">
                <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Materials Found</h3>
                <p className="text-gray-500">
                  No materials match the selected filter criteria.
                </p>
              </div>
            )}
          </div>
        )}
      </motion.div>
    </div>
  )
}
