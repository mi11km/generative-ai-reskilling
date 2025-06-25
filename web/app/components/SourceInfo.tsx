import { useState } from 'react';
import type { SourceDocument } from '../lib/types';

interface SourceInfoProps {
  sources: SourceDocument[];
  confidence: number;
}

export function SourceInfo({ sources, confidence }: SourceInfoProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const confidenceColor = confidence >= 0.8 
    ? 'text-green-600' 
    : confidence >= 0.6 
    ? 'text-yellow-600' 
    : 'text-red-600';

  const confidenceLabel = confidence >= 0.8 
    ? '高い' 
    : confidence >= 0.6 
    ? '中程度' 
    : '低い';

  return (
    <div className="mt-3 border-t border-gray-200 pt-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>信頼度:</span>
          <span className={`font-medium ${confidenceColor}`}>
            {confidenceLabel} ({Math.round(confidence * 100)}%)
          </span>
          <span>•</span>
          <span>{sources.length}件の参照</span>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-sm text-blue-600 hover:text-blue-800 transition-colors"
        >
          {isExpanded ? '折りたたむ' : '詳細を見る'}
        </button>
      </div>

      {isExpanded && (
        <div className="mt-3 space-y-3">
          {sources.map((source, index) => (
            <div key={index} className="bg-gray-50 rounded-lg p-3">
              <div className="font-medium text-sm text-gray-700 mb-1">
                📄 {source.section}
              </div>
              <div className="text-sm text-gray-600 leading-relaxed">
                {source.content.length > 200 
                  ? `${source.content.substring(0, 200)}...` 
                  : source.content
                }
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}