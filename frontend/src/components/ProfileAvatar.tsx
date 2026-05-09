import { useEffect, useMemo, useState } from 'react';
import { UserRound } from 'lucide-react';

interface ProfileAvatarProps {
  name: string;
  handle?: string;
  profileImageUrl?: string | null;
  className?: string;
  iconClassName?: string;
}

const INVALID_IMAGE_VALUES = new Set(['', 'visible', 'none', 'null', 'undefined', 'n/a']);

function isUsableImageUrl(value?: string | null): value is string {
  if (!value) return false;

  const normalized = value.trim();
  if (INVALID_IMAGE_VALUES.has(normalized.toLowerCase())) return false;

  return /^https?:\/\//i.test(normalized) || /^data:image\//i.test(normalized);
}

function getHandleAvatarUrl(handle?: string): string | null {
  const username = handle?.trim().replace(/^@/, '');
  if (!username) return null;

  return `https://unavatar.io/twitter/${encodeURIComponent(username)}?fallback=false`;
}

export function ProfileAvatar({
  name,
  handle,
  profileImageUrl,
  className = 'w-11 h-11',
  iconClassName = 'w-5 h-5',
}: ProfileAvatarProps) {
  const [imageIndex, setImageIndex] = useState(0);
  const imageUrls = useMemo(() => {
    const urls: string[] = [];
    const providedUrl = isUsableImageUrl(profileImageUrl) ? profileImageUrl.trim() : null;
    const handleUrl = getHandleAvatarUrl(handle);

    if (providedUrl) urls.push(providedUrl);
    if (handleUrl && handleUrl !== providedUrl) urls.push(handleUrl);

    return urls;
  }, [handle, profileImageUrl]);
  const imageUrl = imageUrls[imageIndex];

  useEffect(() => {
    setImageIndex(0);
  }, [imageUrls]);

  if (imageUrl) {
    return (
      <img
        src={imageUrl}
        alt={name}
        className={`${className} rounded-full object-cover shrink-0 bg-secondary`}
        onError={() => setImageIndex((currentIndex) => currentIndex + 1)}
      />
    );
  }

  return (
    <div
      aria-label={name}
      className={`${className} rounded-full shrink-0 bg-secondary text-muted-foreground flex items-center justify-center`}
      role="img">
      <UserRound className={iconClassName} aria-hidden="true" />
    </div>
  );
}
