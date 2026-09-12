import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

export const healthApi = {
  check: () => api.get('/health'),
  ready: () => api.get('/ready'),
};

export const predictionApi = {
  predict: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/predict/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  explain: (file, targetLabel = null) => {
    const formData = new FormData();
    formData.append('file', file);
    if (targetLabel) formData.append('target_label', targetLabel);
    return api.post('/predict/explain', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export default api;