export interface Guest {
  id: string;
  name: string;
  twitter_handle: string;
  twitter_url: string;
  bio: string;
  followers: number;
  profile_image_url: string;
  match_score: number;
  match_reason: string;
  recent_tweets: string[];
  outreach_dm: string;
}

export type SearchState = 'empty' | 'searching' | 'done' | 'error';

export interface SearchEventStatus {
  type: 'status';
  message: string;
}

export interface SearchEventLead {
  type: 'lead';
  data: Guest;
}

export interface SearchEventDone {
  type: 'done';
  total_leads: number;
}

export type SearchEvent = SearchEventStatus | SearchEventLead | SearchEventDone;