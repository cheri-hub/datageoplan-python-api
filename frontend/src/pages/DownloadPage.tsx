import { ParcelaDownload } from '../components';

export function DownloadPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Download de Parcela</h1>
      
      <div className="max-w-4xl">
        <ParcelaDownload />
        
        <div className="mt-6 card bg-gray-50">
          <h3 className="font-medium mb-3">📖 Sobre os arquivos CSV</h3>
          <div className="grid md:grid-cols-3 gap-4 text-sm">
            <div>
              <h4 className="font-medium text-govbr-primary">Parcela</h4>
              <p className="text-gray-600">
                Informações gerais da parcela: código, denominação, área, situação, etc.
              </p>
            </div>
            <div>
              <h4 className="font-medium text-govbr-primary">Vértice</h4>
              <p className="text-gray-600">
                Coordenadas dos vértices que compõem o perímetro da parcela.
              </p>
            </div>
            <div>
              <h4 className="font-medium text-govbr-primary">Limite</h4>
              <p className="text-gray-600">
                Informações sobre os limites/confrontações da parcela.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
