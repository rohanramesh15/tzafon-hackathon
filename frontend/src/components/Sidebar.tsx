import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ButtonHTMLAttributes,
  type HTMLAttributes,
  type ReactNode,
} from 'react';
import { PanelLeft } from 'lucide-react';

type SidebarCollapsible = 'offcanvas' | 'none' | 'icon';

type SidebarContextValue = {
  open: boolean;
  setOpen: (open: boolean) => void;
  toggle: () => void;
};

const SidebarContext = createContext<SidebarContextValue | null>(null);

function useSidebar() {
  const ctx = useContext(SidebarContext);
  if (!ctx) {
    throw new Error('Sidebar components must be used within SidebarProvider');
  }
  return ctx;
}

export function SidebarProvider({
  children,
  defaultOpen = true,
}: {
  children: ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const value = useMemo(
    () => ({
      open,
      setOpen,
      toggle: () => setOpen((o) => !o),
    }),
    [open]
  );
  return (
    <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>
  );
}

export function Sidebar({
  collapsible = 'none',
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement> & { collapsible?: SidebarCollapsible }) {
  const { open, setOpen } = useSidebar();
  const offcanvas = collapsible === 'offcanvas';

  return (
    <>
      {offcanvas && open && (
        <button
          type="button"
          aria-label="Close sidebar"
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
          onClick={() => setOpen(false)}
        />
      )}
      <div
        data-sidebar-open={open}
        {...props}
        className={[
          'fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground transition-transform duration-200 ease-out',
          offcanvas && !open && '-translate-x-full',
          className ?? '',
        ]
          .filter(Boolean)
          .join(' ')}
      >
        {children}
      </div>
    </>
  );
}

export function SidebarInset({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  const { open } = useSidebar();
  return (
    <div
      {...props}
      className={[
        'flex min-h-svh flex-1 flex-col',
        open ? 'md:ml-72' : 'md:ml-0',
        'transition-[margin-left] duration-200 ease-out',
        className ?? '',
      ]
        .filter(Boolean)
        .join(' ')}
    />
  );
}

export function SidebarTrigger({
  className,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  const { toggle } = useSidebar();
  return (
    <button
      type="button"
      onClick={toggle}
      {...props}
      className={[
        'inline-flex items-center justify-center rounded-md p-2 outline-none focus-visible:ring-2 focus-visible:ring-ring',
        className ?? '',
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {children ?? <PanelLeft className="h-4 w-4" aria-hidden />}
      <span className="sr-only">Toggle sidebar</span>
    </button>
  );
}

export function SidebarHeader({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      {...props}
      className={['shrink-0 flex flex-col gap-0', className ?? '']
        .filter(Boolean)
        .join(' ')}
    />
  );
}

export function SidebarContent({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      {...props}
      className={['flex flex-1 flex-col gap-2 overflow-y-auto', className ?? '']
        .filter(Boolean)
        .join(' ')}
    />
  );
}

export function SidebarFooter({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      {...props}
      className={['mt-auto shrink-0', className ?? '']
        .filter(Boolean)
        .join(' ')}
    />
  );
}

export function SidebarGroup({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      {...props}
      className={['relative flex flex-col gap-1.5 px-2 py-1', className ?? '']
        .filter(Boolean)
        .join(' ')}
    />
  );
}

export function SidebarGroupLabel({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      {...props}
      className={[
        'flex h-8 items-center gap-1 px-2 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground',
        className ?? '',
      ]
        .filter(Boolean)
        .join(' ')}
    />
  );
}

export function SidebarGroupContent({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return <div {...props} className={className} />;
}

export function SidebarSeparator({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      role="separator"
      {...props}
      className={['mx-2 my-2 h-px bg-sidebar-border', className ?? '']
        .filter(Boolean)
        .join(' ')}
    />
  );
}
