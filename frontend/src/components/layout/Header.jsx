import React from "react";
import Button from "../ui/Button";
// import UploadIcon from '../assets/placeholder-upload-icon.svg'; // You'll add actual icons

const Header = ({
  currentDocumentName,
  onUploadClick,
  onSelectDocumentClick,
  numDocuments,
}) => {
  return (
    <header className="text-white p-3 sm:p-4 flex items-center justify-between shadow-black ">
      <div className="flex items-center">
        {/* Placeholder for Logo */}
        <img
          src="/LogoWithName.png"
          alt="Planet AI Logo"
          className="h-8 sm:h-10 mr-3"
        />
        {/* <span className="font-semibold text-lg sm:text-xl">planet</span> */}
      </div>
      <div className="flex items-center space-x-3 sm:space-x-4">
        {currentDocumentName ? (
          <div className="flex items-center text-sm sm:text-base text-brand-primary px-3 py-1.5">
            {/* Placeholder for Document Icon */}
            <span className="mr-2">
              <img src="/FileIcon.svg"></img>
            </span>{" "}
            {/* Replace with actual icon */}
            <span>{currentDocumentName}</span>
          </div>
        ) : (<></>)}
        <Button
          onClick={onUploadClick}
          variant="outline"
          className="bg-white text-text-primary border-black border-2 hover:bg-gray-200 flex"
        >
          {/* Placeholder for Upload Icon */}
          <span className="mr-1 sm:mr-2 my-auto">
            <img src="/AddIcon(Plus).png"></img>
          </span>
          {/* Replace with actual icon */}
          <span>Upload PDF</span>
        </Button>
      </div>
    </header>
  );
};

export default Header;
