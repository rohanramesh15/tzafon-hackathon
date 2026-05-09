import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, AlertCircle, RefreshCw, SearchX } from 'lucide-react';
import { useGuestSearch } from '../hooks/useGuestSearch';
import { Header } from '../components/Header';
import { QueryInput } from '../components/QueryInput';
import { AgentStatus } from '../components/AgentStatus';
import { GuestCard } from '../components/GuestCard';
import { GuestDetail } from '../components/GuestDetail';
import { Guest } from '../types';
export function Home() {
  const {
    state,
    query,
    setQuery,
    statusMessage,
    leads,
    error,
    startSearch,
    reset,
    exportCsv
  } = useGuestSearch();
  const [selectedGuest, setSelectedGuest] = useState<Guest | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const handleSearch = () => {
    startSearch(query);
  };
  const handleSelectGuest = (guest: Guest) => {
    setSelectedGuest(guest);
    setDetailOpen(true);
  };
  return (
    <div className="min-h-screen bg-secondary/30 flex flex-col font-heading text-foreground">
      <Header />

      <main className="flex-1 w-full max-w-[960px] mx-auto px-6 py-12 md:py-16 flex flex-col">
        <motion.div
          layout
          initial={{
            opacity: 0,
            y: 20
          }}
          animate={{
            opacity: 1,
            y: 0
          }}
          transition={{
            duration: 0.5
          }}
          className={`w-full transition-all duration-500 ${state !== 'empty' ? 'mb-6' : 'my-auto'}`}>
          
          <QueryInput
            query={query}
            setQuery={setQuery}
            onSearch={handleSearch}
            state={state} />
          

          <AgentStatus
            state={state}
            message={statusMessage}
            totalLeads={leads.length} />
          
        </motion.div>

        {/* Error State */}
        {state === 'error' &&
        <motion.div
          initial={{
            opacity: 0,
            scale: 0.97
          }}
          animate={{
            opacity: 1,
            scale: 1
          }}
          className="w-full max-w-[760px] mx-auto mt-6 bg-white border border-border rounded-lg p-6 flex flex-col items-center text-center gap-3">
          
            <div className="w-10 h-10 rounded-full bg-destructive/10 flex items-center justify-center text-destructive">
              <AlertCircle size={20} />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-semibold text-foreground">
                Something went wrong
              </h3>
              <p className="text-muted-foreground text-sm max-w-sm">{error}</p>
            </div>
            <button
            onClick={reset}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors mt-1">
            
              <RefreshCw size={14} />
              Try again
            </button>
          </motion.div>
        }

        {/* No Results State */}
        {state === 'done' && leads.length === 0 &&
        <motion.div
          initial={{
            opacity: 0,
            y: 16
          }}
          animate={{
            opacity: 1,
            y: 0
          }}
          className="w-full max-w-[760px] mx-auto mt-10 flex flex-col items-center text-center gap-3 py-10">
          
            <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center text-muted-foreground">
              <SearchX size={22} />
            </div>
            <div className="space-y-1">
              <h3 className="text-lg font-semibold text-foreground">
                No matching guests found
              </h3>
              <p className="text-muted-foreground max-w-sm mx-auto text-sm">
                Try broadening your criteria or describing the topics you're
                after differently.
              </p>
            </div>
            <button
            onClick={() => {
              const q = query;
              reset();
              setQuery(q);
            }}
            className="text-indigo-600 hover:text-indigo-700 text-sm font-medium mt-1">
            
              Refine search
            </button>
          </motion.div>
        }

        {/* Results */}
        {leads.length > 0 &&
        <motion.div
          initial={{
            opacity: 0
          }}
          animate={{
            opacity: 1
          }}
          className="w-full max-w-[760px] mx-auto mt-8 flex flex-col gap-4">
          
            <div className="flex items-center justify-between">
              <h2 className="text-sm text-muted-foreground">
                <span className="font-semibold text-foreground">
                  {leads.length}
                </span>{' '}
                {state === 'searching' ? 'guests found · streaming' : 'guests'}
              </h2>

              <button
              onClick={exportCsv}
              disabled={state !== 'done'}
              className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-border bg-white hover:bg-secondary text-xs font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
              
                <Download size={14} />
                Export CSV
              </button>
            </div>

            <div className="flex flex-col gap-3 pb-20">
              <AnimatePresence>
                {leads.map((guest) =>
              <motion.div
                key={guest.id}
                initial={{
                  opacity: 0,
                  y: 16
                }}
                animate={{
                  opacity: 1,
                  y: 0
                }}
                transition={{
                  duration: 0.35
                }}>
                
                    <GuestCard
                  guest={guest}
                  onSelect={handleSelectGuest}
                  isSelected={detailOpen && selectedGuest?.id === guest.id} />
                
                  </motion.div>
              )}
              </AnimatePresence>
            </div>
          </motion.div>
        }
      </main>

      <GuestDetail
        guest={selectedGuest}
        open={detailOpen}
        onOpenChange={setDetailOpen} />
      
    </div>);

}