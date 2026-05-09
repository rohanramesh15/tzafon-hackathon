import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  type HTMLAttributes,
  type ReactNode,
} from 'react';

type SheetSide = 'right' | 'left' | 'top' | 'bottom';

type SheetContextValue = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

const SheetContext = createContext<SheetContextValue | null>(null);

export function Sheet({
  open,
  onOpenChange,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: ReactNode;
}) {
  const value = useMemo(() => ({ open, onOpenChange }), [open, onOpenChange]);
  return (
    <SheetContext.Provider value={value}>{children}</SheetContext.Provider>
  );
}

function sidePlacement(side: SheetSide): string {
  switch (side) {
    case 'left':
      return 'inset-y-0 left-0 h-full';
    case 'top':
      return 'top-0 left-0 right-0 max-h-[85vh]';
    case 'bottom':
      return 'bottom-0 left-0 right-0 max-h-[85vh]';
    case 'right':
    default:
      return 'inset-y-0 right-0 h-full';
  }
}

export function SheetContent({
  side = 'right',
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement> & { side?: SheetSide }) {
  const ctx = useContext(SheetContext);

  useEffect(() => {
    if (!ctx?.open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, [ctx?.open]);

  useEffect(() => {
    if (!ctx?.open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') ctx.onOpenChange(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [ctx]);

  if (!ctx?.open) return null;

  return (
    <>
      <button
        type="button"
        aria-label="Close panel"
        className="fixed inset-0 z-40 bg-black/40"
        onClick={() => ctx.onOpenChange(false)}
      />
      <div
        role="dialog"
        aria-modal
        {...props}
        className={`fixed z-50 flex flex-col bg-background shadow-lg ${sidePlacement(side)} ${className ?? ''}`}
      >
        {children}
      </div>
    </>
  );
}

export function SheetHeader({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return <div {...props} className={className} />;
}

export function SheetTitle({
  className,
  ...props
}: HTMLAttributes<HTMLHeadingElement>) {
  return <h2 {...props} className={className} />;
}

export function SheetDescription({
  className,
  ...props
}: HTMLAttributes<HTMLParagraphElement>) {
  return <p {...props} className={className} />;
}
