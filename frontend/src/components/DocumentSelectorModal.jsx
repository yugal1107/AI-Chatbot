// src/components/DocumentSelectorModal.jsx
import React, { useState, useEffect } from 'react';
import { getDocuments } from '../services/api';
import Button from './ui/Button';
import Spinner from './ui/Spinner';
import { motion, AnimatePresence } from 'framer-motion';

const DocumentSelectorModal = ({ isOpen, onClose, onDocumentSelect, triggerRefresh }) => {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      const fetchDocs = async () => {
        setIsLoading(true);
        setError('');
        try {
          const response = await getDocuments();
          setDocuments(response.data || []);
        } catch (err) {
          console.error("Failed to fetch documents:", err);
          setError('Failed to load documents.');
        } finally {
          setIsLoading(false);
        }
      };
      fetchDocs();
    }
  }, [isOpen, triggerRefresh]); // Refetch when modal opens or refresh is triggered

  const handleSelect = (doc) => {
    onDocumentSelect(doc);
    onClose();
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
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="bg-white p-6 sm:p-8 rounded-lg shadow-xl w-full max-w-lg max-h-[80vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-xl sm:text-2xl font-semibold text-text-primary mb-4 sm:mb-6">Select a Document</h2>
            {isLoading && <div className="flex justify-center py-4"><Spinner /></div>}
            {error && <p className="text-red-500 text-center py-4">{error}</p>}
            {!isLoading && !error && documents.length === 0 && (
              <p className="text-text-secondary text-center py-4">No documents uploaded yet.</p>
            )}
            {!isLoading && !error && documents.length > 0 && (
              <ul className="space-y-2 overflow-y-auto flex-grow">
                {documents.map((doc) => (
                  <li key={doc.id}>
                    <button
                      onClick={() => handleSelect(doc)}
                      className="w-full text-left px-4 py-3 rounded-md hover:bg-gray-100 focus:bg-gray-200 focus:outline-none transition-colors"
                    >
                      <span className="font-medium text-text-primary">{doc.original_filename}</span>
                      <span className="text-xs text-text-secondary block">
                        ID: {doc.id} - Uploaded: {new Date(doc.upload_date).toLocaleDateString()}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <div className="mt-6 flex justify-end">
              <Button onClick={onClose} variant="outline">Cancel</Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default DocumentSelectorModal;