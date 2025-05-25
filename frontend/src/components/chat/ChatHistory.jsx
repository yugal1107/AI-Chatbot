import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import { motion, AnimatePresence } from 'framer-motion'; // For animations

const ChatHistory = ({ messages }) => { // messages = [{ id, role, content}, ...]
  const endOfMessagesRef = useRef(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-grow overflow-y-auto p-4 sm:p-6 space-y-4 bg-background-main">
      <AnimatePresence>
        {messages.map((msg, index) => (
          <motion.div
            key={msg.id || index} // Prefer a unique ID if available
            layout
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
          >
            <MessageBubble message={msg} isUser={msg.role === 'user'} />
          </motion.div>
        ))}
      </AnimatePresence>
      <div ref={endOfMessagesRef} />
    </div>
  );
};

export default ChatHistory;