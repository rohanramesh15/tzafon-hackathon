import React, { useEffect, useRef } from 'react';
import { Loader2, ArrowRight } from 'lucide-react';
import { SearchState } from '../types';

interface QueryInputProps {
  query: string;
  setQuery: (q: string) => void;
  onSearch: () => void;
  state: SearchState;
}

export function QueryInput({
  query,
  setQuery,
  onSearch,
  state
}: QueryInputProps) {
  const isSearching = state === 'searching';
  const isClarifying = state === 'clarifying';
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
      if (query.trim() && !isSearching && !isClarifying) {
        onSearch();
      }
    }
  };

  return (
    <div className="w-full max-w-[680px] mx-auto flex flex-col gap-6">
      <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-foreground text-center">
        Who do you want on your podcast?
      </h1>

      <div className="bg-white rounded-2xl border-2 border-indigo-300 shadow-sm focus-within:border-indigo-500 transition-all">
        <textarea
          ref={textareaRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSearching || isClarifying}
          placeholder="A bootstrapped SaaS founder who tweets about scaling..."
          className="w-full min-h-[88px] resize-none bg-transparent border-none p-5 text-base placeholder:text-muted-foreground/50 disabled:opacity-50 outline-none focus:ring-0"
          rows={3}
        />

        <div className="flex items-center justify-end gap-4 px-5 pb-4">
          <button
            onClick={onSearch}
            disabled={!query.trim() || isSearching || isClarifying}
            className="flex items-center justify-center bg-indigo-600 hover:bg-indigo-700 text-white w-10 h-10 rounded-full transition-all disabled:opacity-40 disabled:hover:bg-indigo-600 shrink-0"
            aria-label="Search"
          >
            {isSearching ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <ArrowRight size={16} />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
