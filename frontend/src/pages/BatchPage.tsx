import { BatchDownload } from '../components';

export function BatchPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Download em Lote</h1>
      
      <div className="max-w-4xl">
        <BatchDownload />
      </div>
    </div>
  );
}
