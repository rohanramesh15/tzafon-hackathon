import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check } from 'lucide-react';
import { SearchState } from '../types';
interface AgentStatusProps {
  state: SearchState;
  message: string;
  totalLeads?: number;
}
export function AgentStatus({
  state,
  message,
  totalLeads = 0
}: AgentStatusProps) {
  if (state === 'empty' || state === 'error') return null;
  const isDone = state === 'done';
  return (
    <div className="w-full flex justify-center mt-6">
      <motion.div
        initial={{
          opacity: 0,
          y: 8
        }}
        animate={{
          opacity: 1,
          y: 0
        }}
        aria-live="polite"
        className="flex items-center gap-3 bg-white border border-border rounded-md px-4 py-2 shadow-sm">
        
        <div className="relative flex h-3 w-3 items-center justify-center">
          {isDone ?
          <div className="h-3.5 w-3.5 rounded-full bg-emerald-600 flex items-center justify-center">
              <Check size={9} className="text-white" strokeWidth={3.5} />
            </div> :

          <>
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-600"></span>
            </>
          }
        </div>

        <div className="relative h-5 overflow-hidden flex items-center min-w-[220px]">
          <AnimatePresence mode="popLayout">
            <motion.span
              key={message}
              initial={{
                opacity: 0,
                y: 14
              }}
              animate={{
                opacity: 1,
                y: 0
              }}
              exit={{
                opacity: 0,
                y: -14
              }}
              transition={{
                duration: 0.3
              }}
              className="text-sm text-foreground absolute whitespace-nowrap">
              
              {isDone ?
              `Search complete · ${totalLeads} guests found` :
              message}
            </motion.span>
          </AnimatePresence>
        </div>
      </motion.div>
    </div>);

}