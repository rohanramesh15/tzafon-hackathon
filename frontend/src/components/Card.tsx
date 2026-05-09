import type { HTMLAttributes } from 'react';

function cx(...parts: Array<string | undefined>): string {
  return parts.filter(Boolean).join(' ');
}

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cx(
        'rounded-lg border border-border bg-card text-card-foreground shadow-sm',
        className
      )}
      {...props}
    />
  );
}

export function CardContent({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return <div className={cx(className)} {...props} />;
}
