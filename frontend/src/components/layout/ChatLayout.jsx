// src/components/layout/ChatLayout.jsx
import React, { useState, useEffect, useCallback } from 'react';
import Header from './Header';
import ChatHistory from '../chat/ChatHistory';
import ChatInputBar from '../chat/ChatInputBar';
import UploadModal from '../UploadModal';
import DocumentSelectorModal from '../DocumentSelectorModal'; // New import
import { askQuestion, getDocuments } from '../../services/api'; // Ensure getDocuments is imported
import Button from '../ui/Button';

const ChatLayout = () => {
  const [messages, setMessages] = useState([]);
  const [currentDocument, setCurrentDocument] = useState(null); // { id, name (original_filename), ...other fields }
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isDocSelectorModalOpen, setIsDocSelectorModalOpen] = useState(false);
  const [documentsList, setDocumentsList] = useState([]); // Store all available documents
  const [docListRefreshTrigger, setDocListRefreshTrigger] = useState(0); // To trigger refetch

  // Fetch initial list of documents
  const fetchAllDocuments = useCallback(async () => {
    try {
      const response = await getDocuments();
      setDocumentsList(response.data || []);
      // If no document is currently selected and there's only one doc, select it? Or prompt.
      // For now, we wait for explicit selection.
    } catch (error) {
      console.error("Failed to fetch documents list:", error);
      // Handle error (e.g., show a toast)
    }
  }, []);

  useEffect(() => {
    fetchAllDocuments();
  }, [fetchAllDocuments, docListRefreshTrigger]);

  const handleSendMessage = async (newMessageContent) => {
    if (!currentDocument) {
      // This should ideally not happen if UI disables input correctly
      alert("Error: No document selected for chat.");
      return;
    }

    const newUserMessage = { id: Date.now(), role: 'user', content: newMessageContent };
    setMessages(prev => [...prev, newUserMessage]);
    setIsChatLoading(true);

    const historyForBackend = messages.map(msg => ({ role: msg.role, content: msg.content }));

    try {
      const response = await askQuestion(currentDocument.id, newMessageContent, historyForBackend);
      const aiResponse = { id: Date.now() + 1, role: 'assistant', content: response.data.answer };
      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      console.error("Error sending message:", error);
      const errorResponse = { id: Date.now() + 1, role: 'assistant', content: "Sorry, I encountered an error. Please try again." };
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleUploadSuccess = (uploadedDoc) => {
    // uploadedDoc = { id, original_filename, ... }
    setDocListRefreshTrigger(prev => prev + 1); // Trigger document list refresh
    setCurrentDocument({
        id: uploadedDoc.id,
        name: uploadedDoc.original_filename,
        // include other relevant fields from uploadedDoc if needed
    });
    setMessages([]); // Clear chat for the new/selected document
    setIsUploadModalOpen(false);
  };

  const handleDocumentSelect = (selectedDoc) => {
    if (currentDocument?.id !== selectedDoc.id) {
      setCurrentDocument({
          id: selectedDoc.id,
          name: selectedDoc.original_filename,
          // include other relevant fields from selectedDoc
      });
      setMessages([]); // Clear chat history for the newly selected document
    }
    // If it's the same document, do nothing or just close modal
    setIsDocSelectorModalOpen(false);
  };

  return (
    <div className="flex flex-col h-screen bg-background-main">
      <Header
        currentDocumentName={currentDocument?.name}
        onUploadClick={() => setIsUploadModalOpen(true)}
        onSelectDocumentClick={() => setIsDocSelectorModalOpen(true)}
        numDocuments={documentsList.length}
      />
      <div className="flex-grow flex flex-col overflow-hidden"> {/* Ensure this div takes remaining space */}
        {currentDocument ? (
          <>
            <ChatHistory messages={messages} />
            <ChatInputBar onSendMessage={handleSendMessage} isLoading={isChatLoading} />
          </>
        ) : (
          <div className="flex-grow flex flex-col items-center justify-center text-center p-8">
            {/* <img src="/close.png" alt="No document selected" className="w-48 h-48 mb-6 text-gray-400" /> Placeholder */}
            <h2 className="text-2xl font-semibold text-text-primary mb-2">Welcome!</h2>
            <p className="text-text-secondary mb-6 max-w-md">
              {documentsList.length > 0
                ? "Please select a document from the top to start chatting, or upload a new one."
                : "Upload a PDF document to begin asking questions about its content."}
            </p>
            {documentsList.length > 0 && (
                 <Button onClick={() => setIsDocSelectorModalOpen(true)} variant="primary">
                    Select Existing Document
                 </Button>
            )}
            {/* The upload button is in the header, but you could add another one here too */}
          </div>
        )}
      </div>

      {isUploadModalOpen && (
        <UploadModal
          isOpen={isUploadModalOpen}
          onClose={() => setIsUploadModalOpen(false)}
          onUploadSuccess={handleUploadSuccess}
        />
      )}
      {isDocSelectorModalOpen && (
        <DocumentSelectorModal
          isOpen={isDocSelectorModalOpen}
          onClose={() => setIsDocSelectorModalOpen(false)}
          onDocumentSelect={handleDocumentSelect}
          triggerRefresh={docListRefreshTrigger} // Pass trigger to refetch if modal reopens after new upload
        />
      )}
    </div>
  );
};

export default ChatLayout;