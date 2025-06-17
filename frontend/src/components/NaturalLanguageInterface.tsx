import { useState } from 'react';

interface Result {
  message: string;
}

export default function NaturalLanguageInterface() {
  const [command, setCommand] = useState('');
  const [history, setHistory] = useState<string[]>([]);
  const [result, setResult] = useState<Result | null>(null);

  async function execute() {
    setHistory((h) => [...h, command]);
    const resp = await fetch('/api/nl-command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command }),
    });
    const data = await resp.json();
    setResult(data);
  }

  return (
    <div className="p-4 backdrop-blur-sm bg-white/10 rounded-xl">
      <textarea
        className="w-full p-2 bg-transparent border border-gray-600 rounded"
        value={command}
        onChange={(e) => setCommand(e.target.value)}
        placeholder="Enter command..."
      />
      <button className="mt-2 px-4 py-1 bg-blue-600 text-white rounded" onClick={execute}>
        Run
      </button>
      {result && (
        <pre className="mt-4 bg-black/20 p-2 rounded text-sm text-white">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
      {history.length > 0 && (
        <ul className="mt-4 text-sm text-gray-300">
          {history.map((c, i) => (
            <li key={i}>{c}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
