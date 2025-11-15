import type { ReactNode, MouseEvent } from 'react';

interface BaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  /**
   * Optional max-width preset for the inner card.
   * This is intentionally minimal; we only add options we immediately use.
   */
  size?: 'sm' | 'md' | 'lg';
  /**
   * Additional class names for the card container.
   */
  cardClassName?: string;
  /**
   * Optional z-index override for the overlay.
   */
  zIndexClassName?: string;
  children: ReactNode;
}

/**
 * BaseModal: shared shell for full-screen overlay modals with click-outside-to-close behavior.
 *
 * This keeps visual and interaction behavior consistent across all unified modals.
 */
export default function BaseModal({
  isOpen,
  onClose,
  size = 'md',
  cardClassName = '',
  zIndexClassName = 'z-[80]',
  children,
}: BaseModalProps) {
  if (!isOpen) return null;

  const handleOverlayClick = (event: MouseEvent<HTMLDivElement>) => {
    // Prevent unintended closes if inner content uses stopPropagation.
    if (event.target === event.currentTarget) {
      onClose();
    }
  };

  const sizeClass =
    size === 'sm'
      ? 'max-w-md'
      : size === 'lg'
      ? 'max-w-3xl'
      : 'max-w-xl';

  return (
    <div
      className={`fixed inset-0 ${zIndexClassName} flex items-center justify-center bg-black/60 p-4`}
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
    >
      <div
        className={`workspace-card rounded-2xl w-full ${sizeClass} p-6 shadow-xl space-y-4 ${cardClassName}`}
        onClick={(event) => event.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );
}

