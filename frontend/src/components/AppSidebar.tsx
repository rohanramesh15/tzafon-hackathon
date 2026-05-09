import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus,
  Activity,
  CheckCircle2,
  Circle,
  Sparkles,
  TrendingUp,
  Users } from
'lucide-react';
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarSeparator } from
'./Sidebar';
import { Guest } from '../types';
import { ActivityLogItem } from '../types';
export type ScoreFilter = 'all' | 'high' | 'medium';
interface AppSidebarProps {
  onNewSearch: () => void;
  activityLog: ActivityLogItem[];
  leads: Guest[];
  scoreFilter: ScoreFilter;
  setScoreFilter: (f: ScoreFilter) => void;
  isSearching: boolean;
}
const TIPS = [
'Be specific: mention topics, vibe, and audience size you want.',
'Names of communities help: "people in #buildinpublic"',
'Filters in the input nudge the agent toward dimensions to weigh.'];

export function AppSidebar({
  onNewSearch,
  activityLog,
  leads,
  scoreFilter,
  setScoreFilter,
  isSearching
}: AppSidebarProps) {
  const counts = {
    high: leads.filter((g) => g.match_score >= 80).length,
    medium: leads.filter((g) => g.match_score >= 60 && g.match_score < 80).
    length,
    all: leads.length
  };
  const totalReach = leads.reduce((sum, g) => sum + g.followers, 0);
  const avgScore =
  leads.length > 0 ?
  Math.round(
    leads.reduce((sum, g) => sum + g.match_score, 0) / leads.length
  ) :
  0;
  const formatNum = (n: number) => {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return n.toString();
  };
  return (
    <Sidebar collapsible="offcanvas">
      <SidebarHeader className="px-3 pt-3 pb-2">
        <div className="flex items-center gap-2 px-1 mb-3">
          <div className="w-6 h-6 rounded bg-indigo-600 shrink-0" />
          <span className="font-semibold text-base text-foreground tracking-tight">
            PodPipe
          </span>
        </div>
        <button
          onClick={onNewSearch}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-md bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium transition-colors">
          
          <Plus size={15} />
          New search
        </button>
      </SidebarHeader>

      <SidebarContent className="gap-0">
        {/* Session stats — only when there are results */}
        {leads.length > 0 &&
        <>
            <SidebarGroup>
              <SidebarGroupLabel>This search</SidebarGroupLabel>
              <SidebarGroupContent>
                <div className="px-2 grid grid-cols-2 gap-2">
                  <StatCard
                  icon={<TrendingUp size={13} />}
                  label="Avg match"
                  value={`${avgScore}%`} />
                
                  <StatCard
                  icon={<Users size={13} />}
                  label="Reach"
                  value={formatNum(totalReach)} />
                
                </div>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarSeparator />

            {/* Score filters */}
            <SidebarGroup>
              <SidebarGroupLabel>Filter</SidebarGroupLabel>
              <SidebarGroupContent>
                <div className="px-2 space-y-1">
                  <FilterRow
                  label="All guests"
                  count={counts.all}
                  active={scoreFilter === 'all'}
                  onClick={() => setScoreFilter('all')}
                  color="bg-foreground" />
                
                  <FilterRow
                  label="Top match"
                  sublabel="80%+"
                  count={counts.high}
                  active={scoreFilter === 'high'}
                  onClick={() => setScoreFilter('high')}
                  color="bg-emerald-500" />
                
                  <FilterRow
                  label="Good fit"
                  sublabel="60–79%"
                  count={counts.medium}
                  active={scoreFilter === 'medium'}
                  onClick={() => setScoreFilter('medium')}
                  color="bg-amber-500" />
                
                </div>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarSeparator />
          </>
        }

        {/* Activity log */}
        <SidebarGroup>
          <SidebarGroupLabel>
            <Activity size={12} className="mr-1.5" />
            Activity
            {isSearching &&
            <span className="ml-auto h-1.5 w-1.5 rounded-full bg-indigo-500 animate-pulse" />
            }
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <div className="px-3 py-1 max-h-[260px] overflow-y-auto">
              {activityLog.length === 0 ?
              <p className="text-xs text-muted-foreground px-1 py-2">
                  No activity yet. Start a search to see what the agent is
                  doing.
                </p> :

              <ul className="space-y-2">
                  <AnimatePresence initial={false}>
                    {activityLog.map((item) =>
                  <motion.li
                    key={item.id}
                    initial={{
                      opacity: 0,
                      x: -6
                    }}
                    animate={{
                      opacity: 1,
                      x: 0
                    }}
                    transition={{
                      duration: 0.2
                    }}
                    className="flex items-start gap-2 text-xs">
                    
                        {item.kind === 'lead' ?
                    <CheckCircle2
                      size={11}
                      className="text-emerald-600 mt-0.5 shrink-0" /> :

                    item.kind === 'done' ?
                    <CheckCircle2
                      size={11}
                      className="text-indigo-600 mt-0.5 shrink-0" /> :


                    <Circle
                      size={11}
                      className="text-muted-foreground mt-0.5 shrink-0"
                      strokeWidth={2} />

                    }
                        <span
                      className={
                      item.kind === 'lead' ?
                      'text-foreground/90' :
                      'text-muted-foreground'
                      }>
                      
                          {item.message}
                        </span>
                      </motion.li>
                  )}
                  </AnimatePresence>
                </ul>
              }
            </div>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Tips — only when there's no activity */}
        {activityLog.length === 0 &&
        <>
            <SidebarSeparator />
            <SidebarGroup>
              <SidebarGroupLabel>
                <Sparkles size={12} className="mr-1.5" />
                Tips
              </SidebarGroupLabel>
              <SidebarGroupContent>
                <ul className="px-3 py-1 space-y-2">
                  {TIPS.map((tip, i) =>
                <li
                  key={i}
                  className="text-xs text-muted-foreground leading-relaxed">
                  
                      {tip}
                    </li>
                )}
                </ul>
              </SidebarGroupContent>
            </SidebarGroup>
          </>
        }
      </SidebarContent>

      <SidebarFooter className="px-3 py-3 border-t border-border">
        <div className="text-[10px] text-muted-foreground/70 px-1">
          PodPipe · session-only · v0.1
        </div>
      </SidebarFooter>
    </Sidebar>);

}
function StatCard({
  icon,
  label,
  value




}: {icon: React.ReactNode;label: string;value: string;}) {
  return (
    <div className="bg-white border border-border rounded-md px-2.5 py-2">
      <div className="flex items-center gap-1 text-muted-foreground text-[10px] mb-0.5">
        {icon}
        <span className="uppercase tracking-wide">{label}</span>
      </div>
      <div className="text-sm font-semibold text-foreground">{value}</div>
    </div>);

}
function FilterRow({
  label,
  sublabel,
  count,
  active,
  onClick,
  color







}: {label: string;sublabel?: string;count: number;active: boolean;onClick: () => void;color: string;}) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors ${active ? 'bg-secondary text-foreground' : 'text-muted-foreground hover:bg-secondary/60 hover:text-foreground'}`}>
      
      <span className={`h-2 w-2 rounded-full ${color} shrink-0`} />
      <span className="flex-1 text-left flex items-baseline gap-1.5">
        {label}
        {sublabel &&
        <span className="text-[10px] text-muted-foreground/70">
            {sublabel}
          </span>
        }
      </span>
      <span
        className={`text-xs ${active ? 'text-foreground' : 'text-muted-foreground/70'}`}>
        
        {count}
      </span>
    </button>);

}