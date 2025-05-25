import React from "react";

const Button = ({
  children,
  onClick,
  variant = "primary",
  className = "",
  disabled = false,
  type = "button",
}) => {
  const baseStyles =
    "px-4 py-2 rounded-lg font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors duration-150";
  let variantStyles = "";

  switch (variant) {
    case "primary":
      variantStyles =
        "bg-brand-primary text-text-on-primary hover:bg-brand-primary-dark focus:ring-brand-primary";
      break;
    case "outline":
      variantStyles =
        "border border-border-medium text-text-primary hover:bg-gray-100 focus:ring-brand-primary";
      break;
    // Add more variants as needed
    default:
      variantStyles =
        "bg-brand-primary text-text-on-primary hover:bg-brand-primary-dark";
  }

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${baseStyles} ${variantStyles} ${
        disabled ? "opacity-50 cursor-not-allowed" : ""
      } ${className}`}
    >
      {children}
    </button>
  );
};

export default Button;
