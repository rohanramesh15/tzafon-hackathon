import React, { useEffect, useRef } from 'react';
import { Loader2, ArrowRight } from 'lucide-react';
import { SearchState } from '../types';
interface QueryInputProps {
  query: string;
  setQuery: (q: string) => void;
  onSearch: () => void;
  state: SearchState;
}
const EXAMPLES = [
'Bootstrapped SaaS founder with tactical Twitter presence',
'Indie game developer who streams',
'AI researcher writing accessible threads'];

export function QueryInput({
  query,
  setQuery,
  onSearch,
  state
}: QueryInputProps) {
  const isSearching = state === 'searching';
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [query]);
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      if (query.trim() && !isSearching) {
        onSearch();
      }
    }
  };
  return (
    <div className="w-full max-w-[760px] mx-auto flex flex-col gap-8">
      <div className="text-center space-y-3">
        <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-foreground">
          Find your next podcast guest
        </h1>
        <p className="text-muted-foreground text-base max-w-xl mx-auto">
          Describe who you're looking for in plain English. We search public
          profiles, score topical fit, and draft outreach.
        </p>
      </div>

      <div className="bg-white rounded-xl border border-border shadow-sm focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all">
        <textarea
          ref={textareaRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSearching}
          placeholder="A bootstrapped SaaS founder who tweets tactical advice about scaling…"
          className="w-full min-h-[100px] resize-none bg-transparent border-none p-4 text-base placeholder:text-muted-foreground/60 disabled:opacity-50 outline-none focus:ring-0"
          rows={3} />
        

        <div className="flex flex-wrap items-center justify-between gap-3 px-3 pb-3 pt-2 border-t border-border">
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((ex, i) =>
            <button
              key={i}
              onClick={() => setQuery(ex)}
              disabled={isSearching}
              className="text-xs px-3 py-1.5 rounded-md border border-border bg-white hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50">
              
                {ex}
              </button>
            )}
          </div>

          <button
            onClick={onSearch}
            disabled={!query.trim() || isSearching}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded-md text-sm font-medium transition-all disabled:opacity-40 disabled:hover:bg-indigo-600 shrink-0">
            
            {isSearching ?
            <>
                <Loader2 size={16} className="animate-spin" />
                Searching
              </> :

            <>
                Find guests
                <ArrowRight size={16} />
              </>
            }
          </button>
        </div>
      </div>
    </div>);

}