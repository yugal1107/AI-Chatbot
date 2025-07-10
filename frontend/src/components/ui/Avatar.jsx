import React from "react";

const Avatar = ({ initial, type = "user", size = "md" }) => {
  const sizeClasses = {
    sm: "w-8 h-8 text-sm",
    md: "w-10 h-10 text-base", // Matches image S and AI avatars
  };

  const bgClasses = type === "user" ? "bg-brand-secondary" : "";

  return (
    <div
      className={`flex items-center justify-center rounded-full text-white font-semibold ${sizeClasses[size]} ${bgClasses}`}
    >
      {initial ? (
        initial.toUpperCase()
      ) : (
        <img
          src="/Logo.avif"
          alt="avatar placeholder"
          className="w-full h-full rounded-full object-cover"
        />
      )}
    </div>
  );
};

export default Avatar;
