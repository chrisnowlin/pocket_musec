import type { RefObject, DragEvent, ChangeEvent, ReactNode } from 'react';

interface FileDropzoneProps {
  isActive: boolean;
  onDragActiveChange: (active: boolean) => void;
  onDrop: (event: DragEvent<HTMLDivElement>) => void;
  fileInputRef: RefObject<HTMLInputElement>;
  onFileSelect: (event: ChangeEvent<HTMLInputElement>) => void;
  className?: string;
  children: (openFileDialog: () => void) => ReactNode;
}

export default function FileDropzone({
  isActive,
  onDragActiveChange,
  onDrop,
  fileInputRef,
  onFileSelect,
  className = '',
  children,
}: FileDropzoneProps) {
  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    if (!isActive) {
      onDragActiveChange(true);
    }
  };

  const handleDragLeave = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    if (isActive) {
      onDragActiveChange(false);
    }
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    onDragActiveChange(false);
    onDrop(event);
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <div
      className={className}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*"
        onChange={onFileSelect}
        className="hidden"
      />
      {children(openFileDialog)}
    </div>
  );
}

