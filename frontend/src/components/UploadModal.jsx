import React, { useState } from 'react';
import Button from './ui/Button';
import Spinner from './ui/Spinner'; // Assuming you have this
import { uploadPdf } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';

const UploadModal = ({ isOpen, onClose, onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setMessage('');
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage('Please select a PDF file.');
      return;
    }
    if (selectedFile.type !== "application/pdf") {
      setMessage('Invalid file type. Please upload a PDF.');
      return;
    }

    setIsUploading(true);
    setMessage('Uploading...');

    try {
      const response = await uploadPdf(selectedFile); // From your api.js
      setMessage(`Uploaded "${response.data.original_filename}" successfully!`);
      if (onUploadSuccess) {
        onUploadSuccess(response.data);
      }
      // Optionally close modal after a delay or success message
      setTimeout(() => {
          setSelectedFile(null);
          onClose();
      }, 1500);
    } catch (error) {
      console.error('Upload error:', error);
      setMessage(error.response?.data?.detail || 'Upload failed.');
    } finally {
      setIsUploading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={onClose} // Close on backdrop click
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="bg-white p-6 sm:p-8 rounded-lg shadow-xl w-full max-w-md"
            onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside modal
          >
            <h2 className="text-xl sm:text-2xl font-semibold text-text-primary mb-4 sm:mb-6">Upload PDF Document</h2>
            <div className="mb-4">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="block w-full text-sm text-text-secondary
                           file:mr-4 file:py-2 file:px-4
                           file:rounded-full file:border-0
                           file:text-sm file:font-semibold
                           file:bg-brand-primary file:text-text-on-primary
                           hover:file:bg-brand-primary-dark cursor-pointer"
                disabled={isUploading}
              />
            </div>
            {message && <p className={`text-sm mb-4 ${message.includes('failed') || message.includes('Invalid') ? 'text-red-500' : 'text-green-500'}`}>{message}</p>}
            <div className="flex justify-end space-x-3">
              <Button onClick={onClose} variant="outline" disabled={isUploading}>Cancel</Button>
              <Button onClick={handleUpload} variant="primary" disabled={isUploading || !selectedFile}>
                {isUploading ? <Spinner /> : 'Upload'}
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default UploadModal;