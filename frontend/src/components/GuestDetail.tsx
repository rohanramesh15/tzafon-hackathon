import React, { useState } from 'react';
import { Users, Copy, ExternalLink, Check } from 'lucide-react';
import { Guest } from '../types';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription } from
'./Sheet';
interface GuestDetailProps {
  guest: Guest | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}
export function GuestDetail({ guest, open, onOpenChange }: GuestDetailProps) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    if (!guest) return;
    navigator.clipboard.writeText(guest.outreach_dm);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  const formatFollowers = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'bg-emerald-50 text-emerald-700';
    if (score >= 60) return 'bg-amber-50 text-amber-700';
    return 'bg-zinc-100 text-zinc-700';
  };
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-md md:max-w-lg p-0 flex flex-col gap-0 overflow-hidden bg-white">
        
        {guest &&
        <>
            <SheetHeader className="p-6 space-y-0">
              <div className="flex items-start gap-4">
                <img
                src={guest.profile_image_url}
                alt={guest.name}
                className="w-14 h-14 rounded-full object-cover shrink-0" />
              
                <div className="flex-1 min-w-0">
                  <SheetTitle className="text-lg font-semibold text-foreground truncate text-left">
                    {guest.name}
                  </SheetTitle>
                  <SheetDescription className="text-sm text-muted-foreground truncate text-left">
                    {guest.twitter_handle}
                  </SheetDescription>
                </div>
                <div
                className={`shrink-0 px-2 py-0.5 rounded text-xs font-semibold ${getScoreColor(guest.match_score)}`}>
                
                  {guest.match_score}%
                </div>
              </div>

              <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-3">
                <Users size={12} />
                <span>{formatFollowers(guest.followers)} followers</span>
              </div>
            </SheetHeader>

            <div className="flex-1 overflow-y-auto px-6 pb-6 space-y-6">
              <p className="text-sm text-foreground/90 leading-relaxed">
                {guest.bio}
              </p>

              <div className="text-sm text-foreground/80 italic border-l-2 border-indigo-200 pl-3">
                {guest.match_reason}
              </div>

              {guest.recent_tweets && guest.recent_tweets.length > 0 &&
            <div className="space-y-2">
                  <div className="text-xs text-muted-foreground">
                    Recent tweets
                  </div>
                  <div className="space-y-2">
                    {guest.recent_tweets.map((tweet, i) =>
                <div
                  key={i}
                  className="border border-border rounded-lg p-3 text-sm text-foreground/90 leading-relaxed">
                  
                        {tweet}
                      </div>
                )}
                  </div>
                </div>
            }

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="text-xs text-muted-foreground">Outreach</div>
                  <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 text-xs font-medium text-foreground hover:bg-secondary transition-colors px-2 py-1 rounded">
                  
                    {copied ? <Check size={12} /> : <Copy size={12} />}
                    {copied ? 'Copied' : 'Copy'}
                  </button>
                </div>
                <div className="bg-secondary/50 rounded-lg p-4 text-sm text-foreground/90 whitespace-pre-wrap leading-relaxed">
                  {guest.outreach_dm}
                </div>
              </div>
            </div>

            <div className="border-t border-border p-4 flex items-center gap-2">
              <button
              onClick={handleCopy}
              className="flex-1 flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors">
              
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? 'Copied' : 'Copy DM'}
              </button>
              <a
              href={guest.twitter_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-sm font-medium text-foreground hover:bg-secondary transition-colors px-3 py-2 rounded-md border border-border">
              
                Twitter
                <ExternalLink size={13} />
              </a>
            </div>
          </>
        }
      </SheetContent>
    </Sheet>);

}