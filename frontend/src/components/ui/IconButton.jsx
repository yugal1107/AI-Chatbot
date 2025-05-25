import React from 'react';

const IconButton = ({ children, onClick, className = '', ariaLabel, disabled = false }) => {
  return (
    <button
      onClick={onClick}
      aria-label={ariaLabel}
      disabled={disabled}
      className={`p-2 rounded-full hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-primary focus:ring-offset-1 ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
    >
      {children} {/* Placeholder for icon SVG/component */}
    </button>
  );
};

export default IconButton;