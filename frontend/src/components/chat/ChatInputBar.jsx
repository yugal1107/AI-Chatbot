import React, { useState } from 'react';
import IconButton from '../ui/IconButton';
// import SendIcon from '../assets/placeholder-send-icon.svg'; // You'll add actual icons

const ChatInputBar = ({ onSendMessage, isLoading }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-background-main p-3 sm:p-4 border-t border-border-light flex items-center"
    >
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Send a message..."
        disabled={isLoading}
        className="flex-grow px-4 py-3 bg-background-input border border-border-medium rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-primary focus:border-transparent text-sm sm:text-base"
      />
      <IconButton type="submit" disabled={isLoading || !message.trim()} className="ml-2 sm:ml-3 text-brand-primary" ariaLabel="Send message">
        {/* Placeholder for Send Icon */}
        <span><img src='/Arrow.svg'></img></span> {/* Replace with actual icon */}
      </IconButton>
    </form>
  );
};

export default ChatInputBar;