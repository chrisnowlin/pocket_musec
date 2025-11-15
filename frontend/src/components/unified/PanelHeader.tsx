import type { ReactNode } from 'react';

interface PanelHeaderProps {
  title: string;
  subtitle?: string;
  children?: ReactNode;
  className?: string;
}

export default function PanelHeader({
  title,
  subtitle,
  children,
  className = '',
}: PanelHeaderProps) {
  return (
    <div className={className}>
      <h2 className="text-2xl font-bold text-ink-800">{title}</h2>
      {subtitle && <p className="text-ink-600 mt-2">{subtitle}</p>}
      {children}
    </div>
  );
}

