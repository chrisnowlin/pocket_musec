import DocumentIngestion from '../components/DocumentIngestion';

export default function IngestionPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Document Ingestion</h1>
        <p className="mt-2 text-gray-600">
          Upload and process music education documents with AI-powered analysis
        </p>
      </div>
      
      <DocumentIngestion />
    </div>
  );
}