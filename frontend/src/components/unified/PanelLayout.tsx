import type { ReactNode } from 'react';

interface PanelLayoutProps {
  children: ReactNode;
  className?: string;
}

export default function PanelLayout({ children, className = '' }: PanelLayoutProps) {
  return (
    <div className={`workspace-card ${className}`}>
      {children}
    </div>
  );
}

