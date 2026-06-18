import { useState, useCallback } from 'react';
import { backendApi } from '../api/backend';

export function useMeeting() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [threadId, setThreadId] = useState(null);

  const startMeeting = useCallback(async ({ query, provider, usePremium }) => {
    setLoading(true);
    setError(null);
    
    const newThreadId = `meeting_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setThreadId(newThreadId);
    
    try {
      const response = await backendApi.startMeeting({
        query,
        threadId: newThreadId,
        provider,
        usePremium,
      });
      setResult(response);
      return response;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to start meeting';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const continueMeeting = useCallback(async ({ query }) => {
    if (!threadId) {
      throw new Error('No active meeting to continue');
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await backendApi.continueMeeting({
        threadId,
        query,
      });
      setResult(response);
      return response;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to continue meeting';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [threadId]);

  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
    setResult(null);
    setThreadId(null);
  }, []);

  return {
    loading,
    error,
    result,
    threadId,
    startMeeting,
    continueMeeting,
    reset,
  };
}
