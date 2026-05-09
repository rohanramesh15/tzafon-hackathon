import { useState, useCallback, useRef, useEffect } from 'react';
import { Guest, SearchState } from '../types';

const MOCK_STATUSES = [
'Parsing your brief…',
'Searching Twitter for relevant profiles…',
'Analyzing 247 candidate accounts…',
'Scoring topical relevance & engagement…',
'Drafting personalized outreach…'];


const MOCK_GUESTS: Guest[] = [
{
  id: '1',
  name: 'Arvid Kahl',
  twitter_handle: '@arvidkahl',
  twitter_url: 'https://twitter.com/arvidkahl',
  bio: 'Bootstrapped founder. Sold FeedbackPanda. Now I write and podcast about building sustainable, profitable software businesses without VC.',
  followers: 87400,
  profile_image_url: 'https://i.pravatar.cc/150?img=12',
  match_score: 96,
  match_reason:
  'Authoritative voice on bootstrapped SaaS with consistent tactical threads.',
  recent_tweets: [
  "The hardest part of bootstrapping isn't building the product. It's saying no to everything that isn't the product.",
  'Pricing is a feature. Treat changes to it with the same rigor you treat code deploys.',
  'Your first 100 customers will teach you more than any course. Ship, listen, iterate.'],

  outreach_dm:
  'Hey Arvid — long-time reader of The Bootstrapped Founder. I host a podcast for indie operators and would love to dig into your post-FeedbackPanda playbook for sustainable growth. 30 minutes, your schedule. Open to it?'
},
{
  id: '2',
  name: 'Jon Yongfook',
  twitter_handle: '@yongfook',
  twitter_url: 'https://twitter.com/yongfook',
  bio: 'Solo founder of Bannerbear ($45k MRR). I tweet honest numbers and the unglamorous reality of running a one-person SaaS.',
  followers: 42100,
  profile_image_url: 'https://i.pravatar.cc/150?img=33',
  match_score: 92,
  match_reason: 'Transparent revenue updates and concrete scaling tactics.',
  recent_tweets: [
  'Hit $45k MRR this month. Took 4 years. Still a team of one. The compounding is real.',
  'Most "growth hacks" don\'t work for boring B2B SaaS. SEO and patience do.',
  "Outsourcing customer support to AI saved me 12 hours a week. Here's the prompt I use."],

  outreach_dm:
  "Hi Jon — Bannerbear has been a quiet inspiration for how I think about leverage. I'd love to have you on to walk through the unglamorous middle-game: $10k → $45k MRR as a solo founder. Interested?"
},
{
  id: '3',
  name: 'Marie Poulin',
  twitter_handle: '@mariepoulin',
  twitter_url: 'https://twitter.com/mariepoulin',
  bio: 'Building Notion Mastery. Studio of one. I think out loud about systems, productized services, and slow growth.',
  followers: 58200,
  profile_image_url: 'https://i.pravatar.cc/150?img=47',
  match_score: 88,
  match_reason:
  'Systems-thinker with a lived-in perspective on productized businesses.',
  recent_tweets: [
  'A productized service is a SaaS without the engineering burden. Underrated path.',
  'I redesigned my offer three times before it clicked. Stop trying to nail it on the first try.',
  'My calendar is the single most important asset in my business.'],

  outreach_dm:
  'Hi Marie — your Notion Mastery framing of "studio of one" is exactly the conversation my listeners are hungry for. Would love to host you for a 45-minute episode on building deliberately small. Let me know.'
},
{
  id: '4',
  name: 'Pieter Levels',
  twitter_handle: '@levelsio',
  twitter_url: 'https://twitter.com/levelsio',
  bio: 'Solo bootstrapped maker. Nomad List, Remote OK, photoAI. $200k+/mo. I build in public and ship fast.',
  followers: 462000,
  profile_image_url: 'https://i.pravatar.cc/150?img=68',
  match_score: 94,
  match_reason: 'Iconic indie hacker with a reach few peers can match.',
  recent_tweets: [
  'Built a new SaaS in 4 days. Live at $3k MRR week one. Speed is the moat.',
  'Stop reading. Start shipping. Your first version will be embarrassing. Ship it anyway.',
  'I do my own ops, support, marketing, and engineering. AI handles the boring 80%.'],

  outreach_dm:
  "Hey Pieter — your build-in-public approach has set the template for an entire generation of solo founders. I'd be honored to host you on the show. Happy to record on whatever continent you're on this week."
},
{
  id: '5',
  name: 'Tyler Tringas',
  twitter_handle: '@tylertringas',
  twitter_url: 'https://twitter.com/tylertringas',
  bio: 'GP at Calm Company Fund. Previously founded Storemapper. I invest in and write about calm, profitable software businesses.',
  followers: 31700,
  profile_image_url: 'https://i.pravatar.cc/150?img=14',
  match_score: 84,
  match_reason: 'Operator-turned-investor lens on durable SaaS economics.',
  recent_tweets: [
  "Calm companies aren't low ambition. They're high precision about what to ignore.",
  'The best founders I back have a clear answer to: what are you NOT going to build?',
  'Profitability buys you optionality. Optionality buys you sanity.'],

  outreach_dm:
  "Hi Tyler — Calm Company Fund's thesis is one of the most refreshing in the SaaS world. I'd love to have you on to talk about the operator-investor mindset shift and what makes a company genuinely calm. 30 mins?"
},
{
  id: '6',
  name: 'Justin Jackson',
  twitter_handle: '@mijustin',
  twitter_url: 'https://twitter.com/mijustin',
  bio: 'Co-founder of Transistor.fm. Podcaster, writer, slow-build SaaS believer. Sometimes I post charts.',
  followers: 78500,
  profile_image_url: 'https://i.pravatar.cc/150?img=52',
  match_score: 90,
  match_reason:
  'Built Transistor; deeply understands podcasting AND bootstrapping.',
  recent_tweets: [
  'Most SaaS advice is written by people who raised. Different game, different rules.',
  'Your podcast is a relationship engine, not a marketing channel. Treat it accordingly.',
  'We hit $200k MRR by being patient and slightly stubborn.'],

  outreach_dm:
  "Hey Justin — fellow podcaster here. Transistor's slow-and-stubborn growth story is one I'd love to unpack with my audience. Bonus: we can geek out on podcast-as-a-business at the end. Open to a recording?"
},
{
  id: '7',
  name: 'Sahil Lavingia',
  twitter_handle: '@shl',
  twitter_url: 'https://twitter.com/shl',
  bio: 'Founder of Gumroad. Author of The Minimalist Entrepreneur. Building the simplest path from idea to income.',
  followers: 198000,
  profile_image_url: 'https://i.pravatar.cc/150?img=59',
  match_score: 76,
  match_reason: 'Strong founder voice; less tactical, more philosophical.',
  recent_tweets: [
  "Most companies fail because they try to grow before they're needed.",
  'Profitability is the ultimate validation. Everything else is theater.',
  'Building small is not a consolation prize.'],

  outreach_dm:
  'Hi Sahil — your minimalist entrepreneur framing has changed how a lot of my listeners think about building. Would love to have you on for a focused 30-minute conversation on rejecting growth-at-all-costs.'
}];


export function useGuestSearch() {
  const [state, setState] = useState<SearchState>('empty');
  const [query, setQuery] = useState('');
  const [searchId, setSearchId] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [leads, setLeads] = useState<Guest[]>([]);
  const [error, setError] = useState<string | null>(null);

  const timeoutsRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const cleanup = useCallback(() => {
    timeoutsRef.current.forEach((t) => clearTimeout(t));
    timeoutsRef.current = [];
  }, []);

  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  const schedule = (fn: () => void, delay: number) => {
    const id = setTimeout(fn, delay);
    timeoutsRef.current.push(id);
  };

  const startSearch = useCallback(
    (searchQuery: string) => {
      if (!searchQuery.trim()) return;

      cleanup();
      setState('searching');
      setQuery(searchQuery);
      setLeads([]);
      setError(null);
      setStatusMessage(MOCK_STATUSES[0]);
      setSearchId(`mock_${Date.now()}`);

      // Cycle through status messages
      MOCK_STATUSES.forEach((msg, i) => {
        schedule(() => setStatusMessage(msg), i * 750);
      });

      // After statuses complete, stream leads
      const leadsStartDelay = MOCK_STATUSES.length * 750;
      MOCK_GUESTS.forEach((guest, i) => {
        schedule(
          () => setLeads((prev) => [...prev, guest]),
          leadsStartDelay + i * 350
        );
      });

      // Done
      const doneDelay = leadsStartDelay + MOCK_GUESTS.length * 350 + 200;
      schedule(() => {
        setState('done');
        setStatusMessage('Search complete');
      }, doneDelay);
    },
    [cleanup]
  );

  const reset = useCallback(() => {
    cleanup();
    setState('empty');
    setQuery('');
    setSearchId(null);
    setStatusMessage('');
    setLeads([]);
    setError(null);
  }, [cleanup]);

  const exportCsv = useCallback(() => {
    if (leads.length === 0) return;

    const headers = [
    'name',
    'twitter_handle',
    'twitter_url',
    'bio',
    'followers',
    'match_score',
    'match_reason',
    'outreach_dm'];

    const escape = (val: string | number) => {
      const s = String(val).replace(/"/g, '""');
      return `"${s}"`;
    };
    const rows = leads.map((g) =>
    [
    g.name,
    g.twitter_handle,
    g.twitter_url,
    g.bio,
    g.followers,
    g.match_score,
    g.match_reason,
    g.outreach_dm].

    map(escape).
    join(',')
    );
    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `podpipe-guests-${Date.now()}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [leads]);

  return {
    state,
    query,
    setQuery,
    searchId,
    statusMessage,
    leads,
    error,
    startSearch,
    reset,
    exportCsv
  };
}