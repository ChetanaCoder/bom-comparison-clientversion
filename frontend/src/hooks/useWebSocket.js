import { useState, useEffect, useRef, useCallback } from 'react'

export function useWebSocket(clientId, onMessage = null) {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState(null)
  const [lastMessage, setLastMessage] = useState(null)
  const ws = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const reconnectAttemptsRef = useRef(0)

  const connect = useCallback(() => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.hostname
      const port = window.location.hostname === 'localhost' ? ':8000' : ''
      const wsUrl = `${protocol}//${host}${port}/ws/${clientId}`

      console.log('Connecting to WebSocket:', wsUrl)

      ws.current = new WebSocket(wsUrl)

      ws.current.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        setError(null)
        reconnectAttemptsRef.current = 0
      }

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('WebSocket message received:', data)
          setLastMessage(data)
          if (onMessage) {
            onMessage(data)
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err)
        }
      }

      ws.current.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)

        // Attempt reconnection with exponential backoff
        if (reconnectAttemptsRef.current < 5) {
          const timeout = Math.pow(2, reconnectAttemptsRef.current) * 1000
          console.log(`Reconnecting in ${timeout}ms (attempt ${reconnectAttemptsRef.current + 1})`)

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current += 1
            connect()
          }, timeout)
        }
      }

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        setError('WebSocket connection failed')
      }

    } catch (err) {
      console.error('Failed to create WebSocket connection:', err)
      setError(err.message)
    }
  }, [clientId, onMessage])

  const sendMessage = useCallback((message) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message))
      return true
    }
    console.warn('WebSocket is not connected')
    return false
  }, [])

  const subscribeToWorkflow = useCallback((workflowId) => {
    return sendMessage({
      type: 'subscribe_workflow',
      workflow_id: workflowId
    })
  }, [sendMessage])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [connect])

  return {
    isConnected,
    error,
    lastMessage,
    sendMessage,
    subscribeToWorkflow,
    reconnect: connect
  }
}