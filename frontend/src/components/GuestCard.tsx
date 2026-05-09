import React from 'react';
import { Users, ChevronRight } from 'lucide-react';
import { Guest } from '../types';
import { Card, CardContent } from './Card';
interface GuestCardProps {
  guest: Guest;
  onSelect: (guest: Guest) => void;
  isSelected?: boolean;
}
export function GuestCard({ guest, onSelect, isSelected }: GuestCardProps) {
  const formatFollowers = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    if (score >= 60) return 'bg-amber-50 text-amber-700 border-amber-200';
    return 'bg-zinc-50 text-zinc-700 border-zinc-200';
  };
  return (
    <Card
      className={`overflow-hidden transition-all cursor-pointer group rounded-lg bg-white shadow-sm ${isSelected ? 'border-indigo-500 ring-2 ring-indigo-500/20' : 'border-border hover:border-foreground/30'}`}
      onClick={() => onSelect(guest)}
      role="button"
      aria-label={`View details for ${guest.name}`}>
      
      <CardContent className="p-0">
        <div className="p-4 flex items-start gap-4">
          <img
            src={guest.profile_image_url}
            alt={guest.name}
            className="w-11 h-11 rounded-full object-cover border border-border shrink-0" />
          

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-4 mb-1">
              <div className="flex items-baseline gap-2 truncate min-w-0">
                <span className="font-semibold text-foreground truncate">
                  {guest.name}
                </span>
                <span className="text-muted-foreground text-sm truncate">
                  {guest.twitter_handle}
                </span>
              </div>
              <div
                className={`shrink-0 px-2 py-0.5 rounded text-[11px] font-medium border ${getScoreColor(guest.match_score)}`}>
                
                {guest.match_score}% match
              </div>
            </div>

            <p className="text-sm text-foreground/80 line-clamp-2 mb-2.5">
              {guest.bio}
            </p>

            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3 text-xs text-muted-foreground min-w-0">
                <div className="flex items-center gap-1.5 shrink-0">
                  <Users size={13} />
                  <span>{formatFollowers(guest.followers)}</span>
                </div>
                <span className="text-border">·</span>
                <span className="truncate">{guest.match_reason}</span>
              </div>

              <ChevronRight
                size={16}
                className="text-muted-foreground group-hover:text-foreground shrink-0 transition-colors" />
              
            </div>
          </div>
        </div>
      </CardContent>
    </Card>);

}