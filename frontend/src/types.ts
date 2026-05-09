export interface Guest {
  id: string;
  name: string;
  twitter_handle: string;
  twitter_url: string;
  bio: string;
  followers: number;
  profile_image_url?: string | null;
  match_score: number;
  match_reason: string;
  recent_tweets: string[];
  outreach_dm: string;
}

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

export interface ActivityLogItem {
  id: string;
  message: string;
  timestamp: number;
  kind: 'status' | 'lead' | 'done';
}

export interface QuestionOption {
  id: string;
  label: string;
}

export interface FollowUpQuestion {
  id: string;
  question: string;
  type: 'single_choice' | 'text';
  options: QuestionOption[];
}

export interface AnalyzeQueryResponse {
  needs_clarification: boolean;
  questions: FollowUpQuestion[];
}

export type SearchState = 'empty' | 'clarifying' | 'searching' | 'done' | 'error';