// DatabaseMonitor.js
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const DatabaseMonitor = () => {
  const [logs, setLogs] = useState([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const logsEndRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (isExpanded) {
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isExpanded]);

  // Fetch logs from backend
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/database/logs?limit=50');
        setLogs(response.data.logs || []);
        setIsConnected(true);
      } catch (error) {
        console.error('Error fetching database logs:', error);
        setIsConnected(false);
      }
    };

    // Fetch logs every 2 seconds
    fetchLogs();
    const interval = setInterval(fetchLogs, 2000);

    return () => clearInterval(interval);
  }, []);

  const clearLogs = async () => {
    try {
      await axios.post('http://localhost:8000/api/database/logs/clear');
      setLogs([]);
    } catch (error) {
      console.error('Error clearing logs:', error);
    }
  };

  const getStatusIcon = (status) => {
    if (status === 'success') return '✓';
    if (status === 'error') return '✗';
    return '⚠';
  };

  const getTypeColor = (type) => {
    switch(type) {
      case 'INSERT': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'SELECT': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'UPDATE': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'DELETE': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Floating Button */}
      {!isExpanded && (
        <button
          onClick={() => setIsExpanded(true)}
          className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full p-4 shadow-lg flex items-center space-x-2"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
          </svg>
          <span className="font-medium">Database Monitor</span>
          {logs.length > 0 && (
            <span className="bg-red-500 text-white text-xs rounded-full px-2 py-1">
              {logs.length}
            </span>
          )}
        </button>
      )}

      {/* Expanded Panel */}
      {isExpanded && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl w-[600px] max-h-[600px] flex flex-col border border-gray-200 dark:border-gray-700">
          {/* Header */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
              </svg>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">Database Activity</h3>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {logs.length} operations logged
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`flex items-center space-x-1 px-2 py-1 rounded-full ${isConnected ? 'bg-green-100 dark:bg-green-900' : 'bg-red-100 dark:bg-red-900'}`}>
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
                <span className={`text-xs font-medium ${isConnected ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'}`}>
                  {isConnected ? 'Live' : 'Offline'}
                </span>
              </div>
              <button
                onClick={clearLogs}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                title="Clear logs"
              >
                <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
              <button
                onClick={() => setIsExpanded(false)}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Stats Bar */}
          <div className="grid grid-cols-3 gap-2 p-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
            <div className="text-center">
              <div className="text-xs text-gray-500 dark:text-gray-400">Inserts</div>
              <div className="text-lg font-bold text-green-600 dark:text-green-400">
                {logs.filter(l => l.type === 'INSERT').length}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500 dark:text-gray-400">Queries</div>
              <div className="text-lg font-bold text-blue-600 dark:text-blue-400">
                {logs.filter(l => l.type === 'SELECT').length}
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500 dark:text-gray-400">Avg Time</div>
              <div className="text-lg font-bold text-purple-600 dark:text-purple-400">
                {logs.length > 0 ? Math.round(logs.reduce((a, b) => a + (b.duration || 0), 0) / logs.length) : 0}ms
              </div>
            </div>
          </div>

          {/* Logs List */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {logs.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-gray-400">
                <svg className="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <p className="text-sm">No database operations yet</p>
                <p className="text-xs">Activity will appear here</p>
              </div>
            ) : (
              logs.map((log, index) => (
                <div
                  key={index}
                  className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 border border-gray-200 dark:border-gray-700 text-sm"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className={`text-lg ${log.status === 'success' ? 'text-green-500' : 'text-red-500'}`}>
                        {getStatusIcon(log.status)}
                      </span>
                      <span className={`px-2 py-0.5 text-xs font-semibold rounded ${getTypeColor(log.type)}`}>
                        {log.type}
                      </span>
                      <span className="px-2 py-0.5 text-xs font-mono bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded">
                        {log.table}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </div>
                      <div className="text-xs font-semibold text-indigo-600 dark:text-indigo-400">
                        {log.duration}ms
                      </div>
                    </div>
                  </div>
                  
                  <div className="font-mono text-xs text-gray-600 dark:text-gray-400 mb-2 truncate">
                    {log.action}
                  </div>
                  
                  {log.data && (
                    <details className="text-xs">
                      <summary className="cursor-pointer text-indigo-600 dark:text-indigo-400 hover:underline">
                        View data
                      </summary>
                      <pre className="mt-2 bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-x-auto">
                        {JSON.stringify(log.data, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              ))
            )}
            <div ref={logsEndRef} />
          </div>
        </div>
      )}
    </div>
  );
};

export default DatabaseMonitor;