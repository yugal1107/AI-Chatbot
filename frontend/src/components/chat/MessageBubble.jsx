import React from "react";
import Avatar from "../ui/Avatar";
import ReactMarkdown from "react-markdown";

const MessageBubble = ({ message, isUser }) => {
  // message object: { role: 'user'/'assistant', content: '...' }
  const alignment = "justify-start"; // Always align to the left for both user and AI
  const bubbleColor = isUser ? "bg-background-main" : "bg-background-main";
  const textColor = "text-text-primary";
  const avatarInitial = isUser ? "S" : ""; // Or get from user data / AI config
  const avatarType = isUser ? "user" : "ai";

  return (
    <div className={`flex ${alignment} mb-4 w-full`}>
      <div className={`flex items-start flex-row`}>
        {/* max-w-xs sm:max-w-md md:max-w-lg lg:max-w-xl */}
        <div className="mx-2 mr-2">
          <Avatar initial={avatarInitial} type={avatarType} />
        </div>
        <div
          className={`px-4 py-3 rounded-chat-bubble ${bubbleColor} ${textColor} shadow-sm`}
          style={{
            borderTopLeftRadius: "0.25rem", // Consistent styling for both user and AI
            borderTopRightRadius: undefined, // Flatten corner next to avatar for both
          }}
        >
          <p className="text-sm sm:text-base leading-relaxed">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </p>
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
