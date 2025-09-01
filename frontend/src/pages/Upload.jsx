import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { 
  Upload,
  FileText,
  Database,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  X
} from 'lucide-react'

import { FileUploadZone, LoadingSpinner } from '../components/UI'
import { AutonomousAPI } from '../services/api'
import { useWorkflow } from '../hooks/useWorkflow'

export default function UploadPage() {
  const navigate = useNavigate()
  const { setCurrentWorkflow } = useWorkflow()
  const [qaDocument, setQaDocument] = useState(null)
  const [supplierBom, setSupplierBom] = useState(null)
  const [uploading, setUploading] = useState(false)

  const qaDocTypes = ['.pdf', '.docx', '.doc', '.txt']
  const bomTypes = ['.xlsx', '.xls', '.csv']

  const handleQaDocumentSelect = (file) => {
    const fileExt = '.' + file.name.split('.').pop().toLowerCase()
    if (!qaDocTypes.includes(fileExt)) {
      toast.error(`Invalid WI/QC document type. Please upload: ${qaDocTypes.join(', ')}`)
      return
    }
    setQaDocument(file)
    toast.success('WI/QC document selected')
  }

  const handleSupplierBomSelect = (file) => {
    const fileExt = '.' + file.name.split('.').pop().toLowerCase()
    if (!bomTypes.includes(fileExt)) {
      toast.error(`Invalid supplier BOM type. Please upload: ${bomTypes.join(', ')}`)
      return
    }
    setSupplierBom(file)
    toast.success('Item Master selected')
  }

  const handleStartProcessing = async () => {
    if (!qaDocument || !supplierBom) {
      toast.error('Please select both documents')
      return
    }

    setUploading(true)
    try {
      const response = await AutonomousAPI.uploadDocuments(qaDocument, supplierBom)
      const workflowId = response.workflow_id

      setCurrentWorkflow(workflowId)
      toast.success('Documents uploaded! Autonomous processing started with WI/QC Item classification.')
      navigate(`/processing/${workflowId}`)

    } catch (error) {
      console.error('Upload failed:', error)
      toast.error(error.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const FileCard = ({ file, onRemove, icon: Icon }) => (
    <div className="bg-gray-50 border-2 border-dashed border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
            <Icon className="w-5 h-5 text-primary-600" />
          </div>
          <div>
            <p className="font-medium text-gray-900 truncate max-w-xs">
              {file.name}
            </p>
            <p className="text-sm text-gray-500">
              {formatFileSize(file.size)}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <CheckCircle className="w-5 h-5 text-green-500" />
          <button
            onClick={onRemove}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Upload Documents for Autonomous Processing
        </h2>
        <p className="text-gray-600">
          Upload your Japanese WI/QC document and Item Master to start autonomous processing with Item classification
        </p>
      </div>

      <div className="space-y-8">
        {/* WI/QC Document Upload */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900">WI/QC Document (Japanese)</h3>
          {!qaDocument ? (
            <FileUploadZone
              onFileSelect={handleQaDocumentSelect}
              accept={qaDocTypes.join(',')}
              className="cursor-pointer"
            >
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h4 className="text-lg font-medium text-gray-900 mb-2">
                Drop your WI/QC document here
              </h4>
              <p className="text-gray-500 mb-4">
                Supports PDF, DOCX, DOC, TXT formats
              </p>
            </FileUploadZone>
          ) : (
            <FileCard
              file={qaDocument}
              onRemove={() => setQaDocument(null)}
              icon={FileText}
            />
          )}
        </div>

        {/* Item Master Upload */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900">Item Master</h3>
          {!supplierBom ? (
            <FileUploadZone
              onFileSelect={handleSupplierBomSelect}
              accept={bomTypes.join(',')}
              className="cursor-pointer"
            >
              <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h4 className="text-lg font-medium text-gray-900 mb-2">
                Drop your Item Master here
              </h4>
              <p className="text-gray-500 mb-4">
                Supports Excel (XLSX, XLS) and CSV formats
              </p>
            </FileUploadZone>
          ) : (
            <FileCard
              file={supplierBom}
              onRemove={() => setSupplierBom(null)}
              icon={Database}
            />
          )}
        </div>

        {/* Process Button */}
        <div className="flex justify-end">
          <button
            onClick={handleStartProcessing}
            disabled={!qaDocument || !supplierBom || uploading}
            className="btn btn-primary h-10 px-6 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? (
              <>
                <LoadingSpinner size="sm" className="mr-2" />
                Starting...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4 mr-2" />
                Start Autonomous Processing
              </>
            )}
          </button>
        </div>

        {/* Info Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-blue-900">Autonomous Processing with WI/QC Classification</h4>
              <p className="text-sm text-blue-700 mt-1">
                Our autonomous agents will process your documents through translation, 
                extraction with WI/QC Item classification, and intelligent comparison stages. 
                You can monitor progress in real-time.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
