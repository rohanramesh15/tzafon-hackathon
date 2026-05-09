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
    if (score >= 80) return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    if (score >= 60) return 'bg-amber-50 text-amber-700 border-amber-200';
    return 'bg-zinc-50 text-zinc-700 border-zinc-200';
  };
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-md md:max-w-lg p-0 flex flex-col gap-0 overflow-hidden">
        
        {guest &&
        <>
            {/* Header */}
            <SheetHeader className="p-6 border-b border-border bg-white space-y-4">
              <div className="flex items-start gap-4">
                <img
                src={guest.profile_image_url}
                alt={guest.name}
                className="w-14 h-14 rounded-full object-cover border border-border shrink-0" />
              
                <div className="flex-1 min-w-0">
                  <SheetTitle className="text-lg font-semibold text-foreground truncate">
                    {guest.name}
                  </SheetTitle>
                  <SheetDescription className="text-sm text-muted-foreground truncate">
                    {guest.twitter_handle}
                  </SheetDescription>
                  <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1.5">
                      <Users size={13} />
                      <span>{formatFollowers(guest.followers)} followers</span>
                    </div>
                    <span className="text-border">·</span>
                    <div
                    className={`px-2 py-0.5 rounded text-[11px] font-medium border ${getScoreColor(guest.match_score)}`}>
                    
                      {guest.match_score}% match
                    </div>
                  </div>
                </div>
              </div>
            </SheetHeader>

            {/* Body — scrollable */}
            <div className="flex-1 overflow-y-auto bg-secondary/30">
              <div className="p-6 space-y-6">
                {/* Bio */}
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-foreground uppercase tracking-wide">
                    Bio
                  </h4>
                  <p className="text-sm text-foreground/90 leading-relaxed">
                    {guest.bio}
                  </p>
                </div>

                {/* Why they fit */}
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold text-foreground uppercase tracking-wide">
                    Why they fit
                  </h4>
                  <div className="bg-indigo-50 border border-indigo-100 rounded-md p-3 text-sm text-indigo-900">
                    {guest.match_reason}
                  </div>
                </div>

                {/* Recent Tweets */}
                {guest.recent_tweets && guest.recent_tweets.length > 0 &&
              <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-foreground uppercase tracking-wide">
                      Recent tweets
                    </h4>
                    <div className="grid gap-2">
                      {guest.recent_tweets.map((tweet, i) =>
                  <div
                    key={i}
                    className="bg-white border border-border rounded-md p-3 text-sm text-foreground/90 leading-relaxed">
                    
                          {tweet}
                        </div>
                  )}
                    </div>
                  </div>
              }

                {/* DM */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-semibold text-foreground uppercase tracking-wide">
                      Suggested DM
                    </h4>
                    <button
                    onClick={handleCopy}
                    className="flex items-center gap-1.5 text-xs font-medium text-foreground hover:bg-secondary transition-colors px-2.5 py-1 rounded border border-border bg-white">
                    
                      {copied ? <Check size={13} /> : <Copy size={13} />}
                      {copied ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                  <div className="bg-white border border-border rounded-md p-3.5 text-sm text-foreground/90 whitespace-pre-wrap leading-relaxed">
                    {guest.outreach_dm}
                  </div>
                </div>
              </div>
            </div>

            {/* Footer actions */}
            <div className="border-t border-border bg-white p-4 flex items-center justify-between gap-3">
              <a
              href={guest.twitter_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-sm font-medium text-foreground hover:text-indigo-600 transition-colors px-3 py-2 rounded-md border border-border hover:border-indigo-200">
              
                View on Twitter
                <ExternalLink size={14} />
              </a>
              <button
              onClick={handleCopy}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors">
              
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? 'DM Copied' : 'Copy DM'}
              </button>
            </div>
          </>
        }
      </SheetContent>
    </Sheet>);

}