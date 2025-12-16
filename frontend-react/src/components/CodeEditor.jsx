import { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check, Download } from 'lucide-react';
import { toast } from 'react-hot-toast';

function CodeEditor({ code, language = 'hcl', title = 'Code' }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      toast.success('Code copied to clipboard!');
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error('Failed to copy code');
    }
  };

  const handleDownload = () => {
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.toLowerCase().replace(/\s+/g, '-')}.tf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success('Code downloaded!');
  };

  return (
    <div className="card overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-dark-border bg-dark-hover">
        <h3 className="text-lg font-semibold text-gray-100">{title}</h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopy}
            className="p-2 hover:bg-dark-surface rounded-lg transition-colors"
            title="Copy code"
          >
            {copied ? (
              <Check className="w-5 h-5 text-success-500" />
            ) : (
              <Copy className="w-5 h-5 text-gray-400" />
            )}
          </button>
          <button
            onClick={handleDownload}
            className="p-2 hover:bg-dark-surface rounded-lg transition-colors"
            title="Download code"
          >
            <Download className="w-5 h-5 text-gray-400" />
          </button>
        </div>
      </div>
      
      <div className="overflow-x-auto max-h-[600px]">
        <SyntaxHighlighter
          language={language}
          style={vscDarkPlus}
          customStyle={{
            margin: 0,
            padding: '1.5rem',
            background: '#151b2e',
            fontSize: '0.875rem',
          }}
          showLineNumbers
        >
          {code}
        </SyntaxHighlighter>
      </div>
    </div>
  );
}

export default CodeEditor;
