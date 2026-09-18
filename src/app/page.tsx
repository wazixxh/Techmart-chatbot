'use client';

import { useChat } from '@ai-sdk/react';
import { BotMessageSquare, SendHorizontal, Sparkles, User, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useEffect, useRef } from 'react';

export default function Home() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: '/api/chat',
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <main className="flex min-h-screen flex-col items-center p-4 md:p-8 relative overflow-hidden bg-slate-950 text-slate-50">
      {/* Background decoration */}
      <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-blue-600/10 blur-[120px] pointer-events-none" />
      <div className="fixed bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-emerald-600/10 blur-[120px] pointer-events-none" />

      {/* Header */}
      <header className="z-10 w-full max-w-4xl flex items-center gap-4 p-4 mb-4 border-b border-slate-800/60 bg-slate-900/50 backdrop-blur-md rounded-2xl">
        <div className="flex items-center justify-center p-3 bg-slate-800/80 rounded-xl border border-slate-700/50 shadow-lg">
          <BotMessageSquare className="w-8 h-8 text-blue-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
            Techmart AI
          </h1>
          <p className="text-sm text-slate-400">Intelligent Shopping Assistant</p>
        </div>
      </header>

      {/* Chat Area */}
      <div className="z-10 flex-1 w-full max-w-4xl flex flex-col bg-slate-900/40 backdrop-blur-sm rounded-3xl border border-slate-800/60 shadow-2xl overflow-hidden relative">
        
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center space-y-6">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-500/20 to-emerald-500/20 rounded-full flex items-center justify-center border border-slate-700/50">
              <Sparkles className="w-10 h-10 text-emerald-400" />
            </div>
            <h2 className="text-3xl font-semibold">How can I help you today?</h2>
            <p className="text-slate-400 max-w-md">
              Ask me about our latest laptops, smartphones, return policies, or personalized recommendations.
            </p>
            <div className="flex flex-wrap justify-center gap-3 mt-4">
              {['How long do I have to return a laptop?', 'Which gaming laptop do you recommend?'].map((q) => (
                <button 
                  key={q}
                  onClick={() => handleInputChange({ target: { value: q } } as any)}
                  className="px-4 py-2 bg-slate-800/50 hover:bg-slate-700/50 rounded-full text-sm text-slate-300 border border-slate-700 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 scroll-smooth">
            {messages.map((m) => (
              <div key={m.id} className={`flex gap-4 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {m.role === 'assistant' && (
                  <div className="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0 mt-1">
                    <BotMessageSquare className="w-5 h-5 text-blue-400" />
                  </div>
                )}
                
                <div className={`max-w-[85%] md:max-w-[75%] rounded-2xl px-5 py-4 ${
                  m.role === 'user' 
                    ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-md' 
                    : 'bg-slate-800/80 border border-slate-700/50 text-slate-200 shadow-sm'
                }`}>
                  {m.role === 'assistant' ? (
                    <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-slate-900">
                      <ReactMarkdown>{m.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap">{m.content}</p>
                  )}
                </div>

                {m.role === 'user' && (
                  <div className="w-10 h-10 rounded-full bg-blue-900 border border-blue-800 flex items-center justify-center shrink-0 mt-1">
                    <User className="w-5 h-5 text-blue-200" />
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-4 justify-start">
                <div className="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0">
                  <BotMessageSquare className="w-5 h-5 text-blue-400" />
                </div>
                <div className="bg-slate-800/80 border border-slate-700/50 rounded-2xl px-5 py-4 flex items-center gap-2">
                  <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
                  <span className="text-slate-400 text-sm">Searching knowledge base...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 bg-slate-900/80 border-t border-slate-800/60 backdrop-blur-md">
          <form onSubmit={handleSubmit} className="flex relative items-end bg-slate-950/50 border border-slate-700/50 rounded-2xl overflow-hidden focus-within:border-blue-500/50 focus-within:ring-1 focus-within:ring-blue-500/50 transition-all shadow-inner">
            <textarea
              className="w-full bg-transparent border-none outline-none px-6 py-4 text-slate-200 placeholder-slate-500 resize-none min-h-[60px] max-h-[200px]"
              value={input}
              onChange={handleInputChange}
              placeholder="Ask about laptops, phones, or return policies..."
              rows={1}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  // @ts-ignore
                  handleSubmit(e);
                }
              }}
            />
            <button 
              type="submit" 
              disabled={isLoading || !input.trim()}
              className="m-2 p-3 bg-gradient-to-br from-blue-600 to-emerald-600 text-white rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
            >
              <SendHorizontal className="w-5 h-5" />
            </button>
          </form>
          <div className="text-center mt-3">
            <p className="text-xs text-slate-500 font-medium">Answers are generated from TechMart's policy and product catalog.</p>
          </div>
        </div>
      </div>
    </main>
  );
}
