import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  return (
    <div className={`space-y-2 ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Custom styling for headings with emojis
          h1: ({ children }) => (
            <h1 className="text-lg font-bold text-gray-900 mb-3 mt-4 flex items-center gap-2">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-base font-semibold text-gray-900 mb-2 mt-3 flex items-center gap-2">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-sm font-semibold text-gray-900 mb-2 mt-2 flex items-center gap-2">
              {children}
            </h3>
          ),
          // Custom styling for paragraphs
          p: ({ children }) => (
            <p className="text-sm text-gray-700 leading-relaxed mb-2">{children}</p>
          ),
          // Custom styling for lists with bullet points
          ul: ({ children }) => (
            <ul className="space-y-1 mb-2 text-sm text-gray-700">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="space-y-1 mb-2 text-sm text-gray-700 list-decimal list-inside">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="leading-relaxed flex items-start gap-2">
              <span className="text-purple-500 mt-0.5">•</span>
              <span>{children}</span>
            </li>
          ),
          // Custom styling for bold and italic
          strong: ({ children }) => (
            <strong className="font-semibold text-gray-900">{children}</strong>
          ),
          em: ({ children }) => (
            <em className="italic text-gray-600">{children}</em>
          ),
          // Custom styling for code
          code: ({ node, inline, className, children, ...props }: any) => {
            return inline ? (
              <code className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-xs font-mono" {...props}>
                {children}
              </code>
            ) : (
              <code className="bg-gray-100 text-gray-800 px-3 py-2 rounded text-xs font-mono overflow-x-auto block" {...props}>
                {children}
              </code>
            );
          },
          // Custom styling for blockquotes
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-purple-300 pl-4 py-2 mb-2 bg-purple-50 italic text-gray-700 rounded-r">
              {children}
            </blockquote>
          ),
          // Custom styling for horizontal rules
          hr: () => (
            <hr className="border-gray-200 my-4" />
          ),
          // Custom styling for links to make them clickable and styled
          a: ({ href, children }) => (
            <a 
              href={href} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 underline transition-colors duration-200"
              onClick={(e) => {
                // Ensure the link opens in a new tab
                e.preventDefault();
                window.open(href, '_blank', 'noopener,noreferrer');
              }}
            >
              {children}
            </a>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;