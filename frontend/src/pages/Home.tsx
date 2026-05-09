import React, { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, AlertCircle, RefreshCw, SearchX } from 'lucide-react';
import { useGuestSearch } from '../hooks/useSearch';
import { QueryInput } from '../components/QueryInput';
import { FollowUpQuestions } from '../components/FollowUpQuestions';
import { AgentStatus } from '../components/AgentStatus';
import { GuestCard } from '../components/GuestCard';
import { GuestDetail } from '../components/GuestDetail';
import { AppSidebar, ScoreFilter } from '../components/AppSidebar';
import {
  SidebarProvider,
  SidebarInset,
  SidebarTrigger,
} from '../components/Sidebar';
import { Guest } from '../types';

export function Home() {
  const {
    state,
    query,
    setQuery,
    statusMessage,
    activityLog,
    leads,
    error,
    followUpQuestions,
    startSearch,
    submitClarifications,
    skipClarification,
    reset,
    exportCsv,
  } = useGuestSearch();

  const [selectedGuest, setSelectedGuest] = useState<Guest | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [scoreFilter, setScoreFilter] = useState<ScoreFilter>('all');

  const handleSearch = () => {
    if (!query.trim()) return;
    startSearch(query);
  };

  const handleSelectGuest = (guest: Guest) => {
    setSelectedGuest(guest);
    setDetailOpen(true);
  };

  const handleNewSearch = () => {
    reset();
    setSelectedGuest(null);
    setDetailOpen(false);
    setScoreFilter('all');
  };

  const filteredLeads = useMemo(() => {
    if (scoreFilter === 'high') return leads.filter((g) => g.match_score >= 80);
    if (scoreFilter === 'medium')
      return leads.filter((g) => g.match_score >= 60 && g.match_score < 80);
    return leads;
  }, [leads, scoreFilter]);

  const showResults = leads.length > 0;
  const showEmpty = state === 'empty';
  const isSearching = state === 'searching';
  const isClarifying = state === 'clarifying';

  return (
    <SidebarProvider>
      <AppSidebar
        onNewSearch={handleNewSearch}
        activityLog={activityLog}
        leads={leads}
        scoreFilter={scoreFilter}
        setScoreFilter={setScoreFilter}
        isSearching={isSearching}
      />

      <SidebarInset className="bg-secondary/30">
        {/* Top bar */}
        <header className="h-14 border-b border-border bg-white/60 backdrop-blur-sm flex items-center px-4 gap-3 sticky top-0 z-30">
          <SidebarTrigger className="text-muted-foreground hover:text-foreground" />
          <div className="h-4 w-px bg-border" />
          <div className="text-sm text-muted-foreground">Home</div>
          <div className="ml-auto text-xs text-muted-foreground hidden sm:block">
            ⌘ + Enter to search
          </div>
        </header>

        <main className="flex-1 flex flex-col">
          {/* Empty state - show query input centered */}
          {showEmpty && (
            <div className="flex-1 flex items-center justify-center px-6 py-12">
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="w-full"
              >
                <QueryInput
                  query={query}
                  setQuery={setQuery}
                  onSearch={handleSearch}
                  state={state}
                />
              </motion.div>
            </div>
          )}

          {/* Clarifying state - show follow-up questions */}
          {isClarifying && (
            <div className="flex-1 flex items-center justify-center px-6 py-12">
              <FollowUpQuestions
                questions={followUpQuestions}
                originalQuery={query}
                onSubmit={submitClarifications}
                onSkip={skipClarification}
              />
            </div>
          )}

          {/* Searching/Results state */}
          {!showEmpty && !isClarifying && (
            <div className="px-6 py-8 md:py-12">
              <motion.div
                layout
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
              >
                <QueryInput
                  query={query}
                  setQuery={setQuery}
                  onSearch={handleSearch}
                  state={state}
                />

                <AgentStatus
                  state={state}
                  message={statusMessage}
                  totalLeads={leads.length}
                />
              </motion.div>

              {state === 'error' && (
                <motion.div
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="w-full max-w-[680px] mx-auto mt-10 flex flex-col items-center text-center gap-3 py-10"
                >
                  <AlertCircle
                    size={28}
                    className="text-destructive"
                    strokeWidth={1.5}
                  />
                  <p className="text-foreground">{error}</p>
                  <button
                    onClick={reset}
                    className="flex items-center gap-1.5 text-sm font-medium text-indigo-600 hover:text-indigo-700 transition-colors"
                  >
                    <RefreshCw size={13} />
                    Try again
                  </button>
                </motion.div>
              )}

              {state === 'done' && leads.length === 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="w-full max-w-[680px] mx-auto mt-10 flex flex-col items-center text-center gap-3 py-10"
                >
                  <SearchX
                    size={28}
                    className="text-muted-foreground"
                    strokeWidth={1.5}
                  />
                  <p className="text-foreground">
                    No guests found. Try a different description.
                  </p>
                </motion.div>
              )}

              {showResults && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="w-full max-w-[680px] mx-auto mt-8 flex flex-col gap-4"
                >
                  <div className="flex items-center justify-between">
                    <h2 className="text-sm text-muted-foreground">
                      {filteredLeads.length}{' '}
                      {filteredLeads.length === 1 ? 'guest' : 'guests'}
                      {scoreFilter !== 'all' && (
                        <span className="text-muted-foreground/60">
                          {' '}
                          · filtered
                        </span>
                      )}
                    </h2>

                    <button
                      onClick={exportCsv}
                      disabled={state !== 'done'}
                      className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <Download size={13} />
                      Export CSV
                    </button>
                  </div>

                  <div className="flex flex-col gap-3 pb-20">
                    <AnimatePresence>
                      {filteredLeads.map((guest) => (
                        <motion.div
                          key={guest.id}
                          initial={{ opacity: 0, y: 16 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -8 }}
                          transition={{ duration: 0.3 }}
                        >
                          <GuestCard
                            guest={guest}
                            onSelect={handleSelectGuest}
                            isSelected={
                              detailOpen && selectedGuest?.id === guest.id
                            }
                          />
                        </motion.div>
                      ))}
                    </AnimatePresence>

                    {filteredLeads.length === 0 && (
                      <p className="text-sm text-muted-foreground text-center py-8">
                        No guests in this filter. Try a different one.
                      </p>
                    )}
                  </div>
                </motion.div>
              )}
            </div>
          )}
        </main>

        <GuestDetail
          guest={selectedGuest}
          open={detailOpen}
          onOpenChange={setDetailOpen}
        />
      </SidebarInset>
    </SidebarProvider>
  );
}
