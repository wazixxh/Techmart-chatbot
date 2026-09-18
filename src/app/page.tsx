import { BotMessageSquare, Sparkles } from "lucide-react";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-blue-600/20 blur-[120px]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-emerald-600/20 blur-[120px]" />

      <div className="z-10 max-w-3xl w-full flex flex-col items-center justify-center space-y-8 text-center">
        <div className="flex items-center justify-center p-5 bg-slate-800/50 rounded-2xl border border-slate-700/50 backdrop-blur-sm mb-4 shadow-xl">
          <BotMessageSquare className="w-14 h-14 text-blue-400" />
        </div>
        
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-emerald-400 to-teal-400 drop-shadow-sm">
          Techmart AI
        </h1>
        
        <p className="text-lg md:text-xl text-slate-400 max-w-2xl leading-relaxed">
          Your intelligent shopping assistant. Ask me anything about our products, policies, or get personalized tech recommendations.
        </p>

        <div className="w-full max-w-2xl mt-12 bg-slate-900/60 backdrop-blur-md rounded-2xl border border-slate-700/50 p-2 shadow-2xl flex items-center relative overflow-hidden group transition-all duration-300 hover:border-slate-600/80">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-emerald-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <input 
            type="text" 
            placeholder="Ask about laptops, phones, or return policies..." 
            className="w-full bg-transparent border-none outline-none px-6 py-4 text-slate-200 placeholder-slate-500 relative z-10 text-lg"
            disabled
          />
          <button className="bg-gradient-to-r from-blue-600 to-emerald-600 text-white px-6 py-4 rounded-xl flex items-center gap-2 hover:opacity-90 transition-opacity relative z-10 font-medium shadow-lg cursor-not-allowed">
            <Sparkles className="w-5 h-5" />
            <span>Chat Soon</span>
          </button>
        </div>

        <p className="text-sm text-slate-500 mt-6 font-medium">
          * Currently a UI mockup. Backend integration is coming next!
        </p>
      </div>
    </main>
  );
}
