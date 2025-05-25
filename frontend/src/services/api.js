import axios from 'axios';

// Determine the base URL for the API.
// You can set REACT_APP_API_BASE_URL in a .env file for your frontend project
// (e.g., REACT_APP_API_BASE_URL=http://localhost:8000/api/v1)
// Fallback to a default if not set.
const API_BASE_URL  = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Create an Axios instance with default configurations
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json', // Default content type for most requests
  },
});

/**
 * Uploads a PDF file to the backend.
 * @param {File} file - The PDF file to upload.
 * @returns {Promise<AxiosResponse<any>>} - The Axios response from the server.
 * Expected backend response (success): { id, original_filename, stored_filename, ... }
 */
export const uploadPdf = (file) => {
  const formData = new FormData();
  formData.append('file', file); // The backend expects the file under the key 'file'

  return apiClient.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data', // Important for file uploads
    },
  });
};

/**
 * Fetches a list of all uploaded documents.
 * @param {number} [skip=0] - Number of documents to skip (for pagination).
 * @param {number} [limit=100] - Maximum number of documents to return.
 * @returns {Promise<AxiosResponse<any>>} - The Axios response containing an array of documents.
 * Expected backend response (success): [{ id, original_filename, ... }, ...]
 */
export const getDocuments = (skip = 0, limit = 10) => {
  return apiClient.get('/documents/', {
    params: { skip, limit },
  });
};

/**
 * Fetches details for a specific document by its ID.
 * @param {number|string} documentId - The ID of the document to fetch.
 * @returns {Promise<AxiosResponse<any>>} - The Axios response containing the document details.
 * Expected backend response (success): { id, original_filename, ... }
 */
export const getDocumentById = (documentId) => {
  return apiClient.get(`/documents/${documentId}`);
};

/**
 * Asks a question related to a specific document, including chat history for context.
 * @param {number|string} documentId - The ID of the document.
 * @param {string} question - The question to ask.
 * @param {Array<{role: string, content: string}>} chatHistory - The history of the conversation.
 * @returns {Promise<AxiosResponse<any>>} - The Axios response containing the answer.
 * Expected backend response (success): { answer: "..." }
 */
export const askQuestion = (documentId, question, chatHistory = []) => {
  return apiClient.post(`/documents/${documentId}/ask`, {
    question: question,
    chat_history: chatHistory, // Ensure this matches the Pydantic model on the backend
  });
};

// You can add other API functions here as your application grows.
// For example, deleting a document:
// export const deleteDocument = (documentId) => {
//   return apiClient.delete(`/documents/${documentId}`);
// };


export default apiClient; // You can also export this if you need to use the instance directly elsewhere.