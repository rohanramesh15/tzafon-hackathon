import { Users } from 'lucide-react';
import { Guest } from '../types';
import { Card, CardContent } from './Card';
import { ProfileAvatar } from './ProfileAvatar';
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
    if (score >= 80) return 'bg-emerald-50 text-emerald-700';
    if (score >= 60) return 'bg-amber-50 text-amber-700';
    return 'bg-zinc-100 text-zinc-700';
  };
  return (
    <Card
      className={`overflow-hidden transition-all cursor-pointer rounded-lg bg-white shadow-sm ${isSelected ? 'border-indigo-500 ring-2 ring-indigo-500/20' : 'border-border hover:border-foreground/30'}`}
      onClick={() => onSelect(guest)}
      role="button"
      aria-label={`View ${guest.name}`}>
      
      <CardContent className="p-4 flex items-center gap-4">
        <ProfileAvatar
          name={guest.name}
          handle={guest.twitter_handle}
          profileImageUrl={guest.profile_image_url} />
        

        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2 truncate">
            <span className="font-semibold text-foreground truncate">
              {guest.name}
            </span>
            <span className="text-muted-foreground text-sm truncate">
              {guest.twitter_handle}
            </span>
          </div>
          <p className="text-sm text-muted-foreground line-clamp-1 mt-0.5">
            {guest.bio}
          </p>
          <div className="flex items-center gap-1.5 mt-1.5 text-xs text-muted-foreground">
            <Users size={12} />
            <span>{formatFollowers(guest.followers)}</span>
          </div>
        </div>

        <div
          className={`shrink-0 px-2 py-0.5 rounded text-xs font-semibold ${getScoreColor(guest.match_score)}`}>
          
          {guest.match_score}%
        </div>
      </CardContent>
    </Card>);

}