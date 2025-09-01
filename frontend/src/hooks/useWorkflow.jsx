import React, { createContext, useContext, useReducer } from 'react'

const WorkflowContext = createContext()

// Initial state
const initialState = {
  workflows: {},
  currentWorkflowId: null,
  agentStats: null,
  loading: false,
  error: null
}

// Actions
const WORKFLOW_ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  SET_CURRENT_WORKFLOW: 'SET_CURRENT_WORKFLOW',
  UPDATE_WORKFLOW: 'UPDATE_WORKFLOW',
  SET_WORKFLOWS: 'SET_WORKFLOWS',
  SET_AGENT_STATS: 'SET_AGENT_STATS',
  CLEAR_ERROR: 'CLEAR_ERROR'
}

// Reducer
function workflowReducer(state, action) {
  switch (action.type) {
    case WORKFLOW_ACTIONS.SET_LOADING:
      return { ...state, loading: action.payload }

    case WORKFLOW_ACTIONS.SET_ERROR:
      return { ...state, error: action.payload, loading: false }

    case WORKFLOW_ACTIONS.CLEAR_ERROR:
      return { ...state, error: null }

    case WORKFLOW_ACTIONS.SET_CURRENT_WORKFLOW:
      return { ...state, currentWorkflowId: action.payload }

    case WORKFLOW_ACTIONS.UPDATE_WORKFLOW:
      return {
        ...state,
        workflows: {
          ...state.workflows,
          [action.payload.workflow_id]: {
            ...state.workflows[action.payload.workflow_id],
            ...action.payload
          }
        }
      }

    case WORKFLOW_ACTIONS.SET_WORKFLOWS:
      const workflowsMap = {}
      action.payload.forEach(workflow => {
        workflowsMap[workflow.workflow_id] = workflow
      })
      return { ...state, workflows: workflowsMap }

    case WORKFLOW_ACTIONS.SET_AGENT_STATS:
      return { ...state, agentStats: action.payload }

    default:
      return state
  }
}

// Provider component
export function WorkflowProvider({ children }) {
  const [state, dispatch] = useReducer(workflowReducer, initialState)

  const setLoading = (loading) => {
    dispatch({ type: WORKFLOW_ACTIONS.SET_LOADING, payload: loading })
  }

  const setError = (error) => {
    dispatch({ type: WORKFLOW_ACTIONS.SET_ERROR, payload: error })
  }

  const clearError = () => {
    dispatch({ type: WORKFLOW_ACTIONS.CLEAR_ERROR })
  }

  const setCurrentWorkflow = (workflowId) => {
    dispatch({ type: WORKFLOW_ACTIONS.SET_CURRENT_WORKFLOW, payload: workflowId })
  }

  const updateWorkflow = (workflowData) => {
    dispatch({ type: WORKFLOW_ACTIONS.UPDATE_WORKFLOW, payload: workflowData })
  }

  const setWorkflows = (workflows) => {
    dispatch({ type: WORKFLOW_ACTIONS.SET_WORKFLOWS, payload: workflows })
  }

  const setAgentStats = (stats) => {
    dispatch({ type: WORKFLOW_ACTIONS.SET_AGENT_STATS, payload: stats })
  }

  const value = {
    ...state,
    setLoading,
    setError,
    clearError,
    setCurrentWorkflow,
    updateWorkflow,
    setWorkflows,
    setAgentStats
  }

  return (
    <WorkflowContext.Provider value={value}>
      {children}
    </WorkflowContext.Provider>
  )
}

// Hook to use workflow context
export function useWorkflow() {
  const context = useContext(WorkflowContext)
  if (!context) {
    throw new Error('useWorkflow must be used within a WorkflowProvider')
  }
  return context
}

export { WORKFLOW_ACTIONS }