import React from 'react';
export function Header() {
  return (
    <header className="w-full border-b border-border bg-white sticky top-0 z-50">
      <div className="max-w-[960px] mx-auto px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-indigo-600" />
          <span className="font-semibold text-base text-foreground tracking-tight">
            PodPipe
          </span>
        </div>
        <span className="text-xs text-muted-foreground hidden sm:inline">
          ⌘ + Enter to search
        </span>
      </div>
    </header>);

}