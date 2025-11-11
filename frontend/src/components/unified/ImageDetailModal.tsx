import type { ImageData } from '../../types/unified';

interface ImageDetailModalProps {
  image: ImageData | null;
  onClose: () => void;
  onDelete: (id: string) => void;
}

export default function ImageDetailModal({ image, onClose, onDelete }: ImageDetailModalProps) {
  if (!image) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
    >
      <div
        className="workspace-card rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-2xl font-bold text-ink-800">{image.filename}</h3>
          <button onClick={onClose} className="text-ink-500 hover:text-ink-700">
            ✕
          </button>
        </div>
        <div className="space-y-4 text-sm text-ink-600">
          <p>Uploaded: {new Date(image.uploaded_at).toLocaleString()}</p>
          <p>Size: {(image.file_size / 1024).toFixed(2)} KB</p>
          <p>Type: {image.mime_type}</p>
          {image.ocr_text && (
            <div>
              <h4 className="font-semibold text-ink-800 mb-2">OCR Extracted Text</h4>
              <div className="bg-parchment-200 rounded p-4 text-sm text-ink-700 whitespace-pre-wrap">
                {image.ocr_text}
              </div>
            </div>
          )}
          {image.vision_analysis && (
            <div>
              <h4 className="font-semibold text-ink-800 mb-2">Vision Analysis</h4>
              <div className="bg-parchment-200 rounded p-4 text-sm text-ink-700 whitespace-pre-wrap">
                {image.vision_analysis}
              </div>
            </div>
          )}
          <div className="flex justify-end gap-3">
            <button
              onClick={() => onDelete(image.id)}
              className="px-4 py-2 bg-ink-700 text-parchment-100 rounded-md hover:bg-ink-800"
            >
              Delete
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-ink-600 text-parchment-100 rounded-md hover:bg-ink-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
