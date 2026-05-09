import {
  createContext,
  useContext,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type HTMLAttributes,
  type ReactNode,
} from 'react';
import { createPortal } from 'react-dom';

function cx(...parts: Array<string | undefined>): string {
  return parts.filter(Boolean).join(' ');
}

type SheetContextValue = {
  onOpenChange: (open: boolean) => void;
};

const SheetContext = createContext<SheetContextValue | null>(null);

type SheetProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: ReactNode;
};

export function Sheet({ open, onOpenChange, children }: SheetProps) {
  const [mounted, setMounted] = useState(false);
  const suppressBackdropCloseRef = useRef(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  useLayoutEffect(() => {
    if (!open) return undefined;
    suppressBackdropCloseRef.current = true;
    let raf2 = 0;
    const raf1 = requestAnimationFrame(() => {
      raf2 = requestAnimationFrame(() => {
        suppressBackdropCloseRef.current = false;
      });
    });
    return () => {
      cancelAnimationFrame(raf1);
      cancelAnimationFrame(raf2);
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onOpenChange(false);
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onOpenChange]);

  const closeBackdrop = () => {
    if (suppressBackdropCloseRef.current) return;
    onOpenChange(false);
  };

  if (!open || !mounted) return null;

  return createPortal(
    <SheetContext.Provider value={{ onOpenChange }}>
      <div
        className="fixed inset-0 z-[100]"
        role="dialog"
        aria-modal="true">
        <div
          className="fixed inset-0 z-[100] bg-black/80"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) closeBackdrop();
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget) closeBackdrop();
          }}
          aria-hidden
        />
        {children}
      </div>
    </SheetContext.Provider>,
    document.body
  );
}

type SheetContentProps = HTMLAttributes<HTMLDivElement> & {
  side?: 'top' | 'right' | 'bottom' | 'left';
};

export function SheetContent({
  side = 'right',
  className,
  children,
  onMouseDown,
  onClick,
  ...props
}: SheetContentProps) {
  const ctx = useContext(SheetContext);
  if (!ctx) {
    throw new Error('SheetContent must be used within Sheet');
  }

  const sideClass =
    side === 'right'
      ? 'inset-y-0 right-0 h-full border-l'
      : side === 'left'
        ? 'inset-y-0 left-0 h-full border-r'
        : side === 'top'
          ? 'inset-x-0 top-0 max-h-[90vh] border-b'
          : 'inset-x-0 bottom-0 max-h-[90vh] border-t';

  return (
    <div
      className={cx(
        'fixed z-[110] flex flex-col bg-background shadow-lg outline-none',
        sideClass,
        className
      )}
      onMouseDown={(e) => {
        onMouseDown?.(e);
        e.stopPropagation();
      }}
      onClick={(e) => {
        onClick?.(e);
        e.stopPropagation();
      }}
      {...props}>
      {children}
    </div>
  );
}

export function SheetHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cx('flex flex-col gap-2 text-left', className)}
      {...props}
    />
  );
}

export function SheetTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h2 className={cx('text-lg font-semibold text-foreground', className)} {...props} />
  );
}

export function SheetDescription({
  className,
  ...props
}: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cx('text-sm text-muted-foreground', className)} {...props} />
  );
}
