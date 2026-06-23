import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://ai-board-backend-production.up.railway.app';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for board meetings
  headers: {
    'Content-Type': 'application/json',
  },
});

export const backendApi = {
  // Health check
  health: async () => {
    const response = await api.get('/health');
    return response.data;
  },

  // Start a new meeting
  startMeeting: async ({ query, threadId, provider, usePremium }) => {
    const response = await api.post('/meeting', {
      query,
      thread_id: threadId,
      provider,
      use_premium: usePremium,
      stream: false,
    });
    return response.data;
  },

  // Continue existing meeting
  continueMeeting: async ({ threadId, query }) => {
    const response = await api.post('/meeting/continue', {
      thread_id: threadId,
      query,
    });
    return response.data;
  },

  // Get meeting by ID
  getMeeting: async (threadId) => {
    const response = await api.get(`/meeting/${threadId}`);
    return response.data;
  },

  // List all meetings
  listMeetings: async () => {
    const response = await api.get('/meetings');
    return response.data;
  },
};

export default api;
